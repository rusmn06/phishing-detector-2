"""
Main entry point untuk FastAPI application.
Menginisialisasi semua routes, middleware, dan database.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, Optional
from datetime import datetime
import logging

# Import configuration
from config import settings

# Import utilities
from utils.file_validator import validate_email_file
from utils.sanitizer import sanitize_html

# Import core logic
from core.email_parser import parse_eml_file
from core.analysis import analyze_authenticity
from core.rate_limiter import quota_manager
from core.safe_browsing import check_urls_safe_browsing
from core.virustotal import virustotal_adapter

# Import models
from models import URLScanRequest, URLScanResult

# Import database
from database import init_db, get_db, ScanHistory, cleanup_old_records
from sqlalchemy.orm import Session

# Import routes
from routes.history import router as history_router

# ===========================================
# Logging Configuration
# ===========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===========================================
# FastAPI Application Initialization
# ===========================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Aplikasi Internal Deteksi Phishing Email - Berbasis Arsitektur Hybrid",
    version="1.0.0",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# ===========================================
# Middleware Configuration
# ===========================================

# CORS Middleware - Allow frontend to access API
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative dev port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================================
# Startup Event - Initialize Database
# ===========================================
@app.on_event("startup")
async def startup_event():
    """
    Initialize database tables on application startup.
    Also trigger initial cleanup if needed.
    """
    logger.info("Starting application initialization...")
    init_db()
    logger.info("Database initialized successfully")
    
    # Optional: Run initial cleanup on startup
    # db = next(get_db())
    # cleanup_old_records(db, retention_days=30)

# ===========================================
# Health Check Endpoint
# ===========================================
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancer.
    Returns application status and environment.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

# ===========================================
# Quota Status Endpoint
# ===========================================
@app.get(f"{settings.API_V1_STR}/quota-status", tags=["Monitoring"])
async def get_quota_status():
    """
    Get API quota status for monitoring.
    Useful to check remaining quota before making requests.
    """
    vt_status = await quota_manager.check_rate_limit("virustotal")
    gs_status = await quota_manager.check_rate_limit("google_safe_browsing")
    
    return {
        "virustotal": {
            "remaining": vt_status["remaining"],
            "warnings": vt_status["warnings"],
            "allowed": vt_status["allowed"]
        },
        "google_safe_browsing": {
            "remaining": gs_status["remaining"],
            "warnings": gs_status["warnings"],
            "allowed": gs_status["allowed"]
        }
    }

# ===========================================
# POST /scan-url - Scan URL Langsung
# ===========================================
@app.post(f"{settings.API_V1_STR}/scan-url", response_model=URLScanResult, tags=["Scanning"])
async def scan_url(request: URLScanRequest):
    """
    Scan URL langsung untuk deteksi phishing/malware.
    Menggunakan VirusTotal API untuk analisis URL.
    
    **Use Case:**
    - Cek link sebelum diklik
    - Verifikasi URL dari SMS/WhatsApp
    - Analisis URL tanpa perlu file email
    """
    
    # Validasi URL sederhana
    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL harus dimulai dengan http:// atau https://"
        )
    
    # Cek URL menggunakan threat detector (VirusTotal)
    url_threat_results = await virustotal_adapter.check_urls([request.url])
    
    # Hitung skor risiko berdasarkan hasil
    risk_score = 0
    threatening_urls = url_threat_results.get("threatening_urls", 0)
    
    if threatening_urls > 0:
        # Ada URL berbahaya terdeteksi
        risk_score = 100
        verdict = "malicious"
    elif url_threat_results.get("status") == "unknown":
        # URL belum pernah dianalisis
        risk_score = 50
        verdict = "suspicious"
    else:
        # Tidak ada ancaman terdeteksi
        risk_score = 0
        verdict = "safe"
    
    return URLScanResult(
        url=request.url,
        verdict=verdict,
        risk_score=risk_score,
        provider=url_threat_results.get("provider", settings.URL_THREAT_PROVIDER),
        details=url_threat_results
    )

# ===========================================
# POST /scan - Scan Email (.eml file)
# ===========================================
@app.post(f"{settings.API_V1_STR}/scan", tags=["Scanning"])
async def scan_email(
    file: Annotated[UploadFile, File(description="File email .eml untuk dianalisis")],
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint utama untuk scan email phishing.
    
    **Flow:**
    1. Validasi file (ukuran + magic bytes)
    2. Parse email (ekstrak header, body, URL)
    3. Analisis otentikasi (SPF/DKIM/DMARC)
    4. Analisis URL (Google Safe Browsing / VirusTotal)
    5. Hitung skor risiko dan verdict
    6. Simpan ke database untuk history
    
    **File Requirements:**
    - Format: .eml (RFC822)
    - Max Size: 10MB
    - Magic Bytes: message/rfc822
    """
    
    logger.info(f"Starting scan for file: {file.filename}")
    
    # --- Step 1: Validasi File ---
    try:
        validated_content = await validate_email_file(file)
    except HTTPException as e:
        logger.warning(f"File validation failed: {e.detail}")
        raise e
    
    # --- Step 2: Parse Email ---
    parsed_email = parse_eml_file(validated_content)
    
    # Handle jika domain pengirim tidak teridentifikasi
    if not parsed_email.get("from_domain"):
        # Save to database even if failed
        scan_record = ScanHistory(
            filename=file.filename,
            verdict="suspicious",
            risk_score=50,
            from_domain="",
            from_email=parsed_email.get("from", ""),
            subject=parsed_email.get("subject", ""),
            url_count=0,
            threatening_url_count=0,
            ip_address=request.client.host if request.client else "unknown",
            result_data={
                "error": "Tidak dapat mengidentifikasi domain pengirim",
                "parsed_email": parsed_email
            }
        )
        db.add(scan_record)
        db.commit()
        db.refresh(scan_record)
        
        return {
            "verdict": "suspicious",
            "risk_score": 50,
            "scan_id": scan_record.id,
            "scanned_at": scan_record.scanned_at.isoformat(),
            "risk_factors": ["Tidak dapat mengidentifikasi domain pengirim"],
            "details": parsed_email,
            "sanitized_body_preview": parsed_email.get("sanitized_html", "")[:500],
            "email_subject": parsed_email.get("subject", ""),
            "from_domain": "",
        }
    
    # --- Step 3: Analisis Otentikasi (SPF/DMARC) ---
    logger.info(f"Analyzing authenticity for domain: {parsed_email['from_domain']}")
    auth_results = await analyze_authenticity(parsed_email["from_domain"])
    
    # --- Step 4: Ekstrak & Analisis URL ---
    urls = parsed_email.get("urls", [])
    logger.info(f"Found {len(urls)} URLs in email")
    url_threat_results = await check_urls_safe_browsing(urls)
    
    # --- Step 5: Hitung Skor Risiko ---
    risk_score = 0
    risk_factors = []
    
    def get_status(auth_dict: dict, key: str) -> str:
        """Safely get status from auth_results with fallback."""
        try:
            return auth_dict.get(key, {}).get("status", "unknown")
        except (AttributeError, TypeError):
            return "unknown"
    
    def is_timeout(auth_dict: dict, key: str) -> bool:
        """Check if auth check timed out."""
        try:
            return auth_dict.get(key, {}).get("is_timeout", False)
        except (AttributeError, TypeError):
            return False
    
    # --- DMARC Scoring ---
    dmarc_status = get_status(auth_results, "dmarc")
    
    if dmarc_status == "fail":
        risk_score += 40
        risk_factors.append("DMARC verification failed")
    elif dmarc_status == "error" or is_timeout(auth_results, "dmarc"):
        # Timeout/error - jangan tambah poin, hanya info
        risk_factors.append("⚠️ DMARC check timeout - tidak dapat diverifikasi")
    
    # --- SPF Scoring ---
    spf_status = get_status(auth_results, "spf")
    
    if spf_status == "fail":
        risk_score += 30
        risk_factors.append("SPF verification failed")
    elif spf_status == "error" or is_timeout(auth_results, "spf"):
        # Timeout/error - jangan tambah poin
        risk_factors.append("⚠️ SPF check timeout - tidak dapat diverifikasi")
    
    # --- DKIM Scoring ---
    dkim_status = get_status(auth_results, "dkim")
    
    if dkim_status == "not_configured":
        risk_score += 20
        risk_factors.append("DKIM not configured for domain")
    
    # --- Error saat check otentikasi ---
    if "error" in auth_results:
        risk_score += 25
        risk_factors.append(f"Authentication check error: {auth_results['error']}")
    
    # --- URL BERBAHAYA TERDETEKSI = +60 poin ---
    if url_threat_results.get("threatening_urls", 0) > 0:
        risk_score += 60
        threat_count = url_threat_results["threatening_urls"]
        provider_name = url_threat_results.get("provider", "URL Threat Detector")
        risk_factors.append(f"{threat_count} URL berbahaya terdeteksi oleh {provider_name}")
    
    # --- Error saat check URL ---
    if url_threat_results.get("status") in ["error", "timeout"]:
        risk_score += 15
        risk_factors.append(f"URL check error: {url_threat_results.get('error', 'Unknown')}")
    
    # Tentukan verdict berdasarkan skor
    if risk_score >= 70:
        verdict = "phishing"
    elif risk_score >= 40:
        verdict = "suspicious"
    else:
        verdict = "safe"
    
    logger.info(f"Scan completed - Verdict: {verdict}, Score: {risk_score}")
    
    # --- Step 6: Save to Database ---
    scan_record = ScanHistory(
        filename=file.filename,
        verdict=verdict,
        risk_score=min(risk_score, 100),
        from_domain=parsed_email.get("from_domain", ""),
        from_email=parsed_email.get("from", ""),
        subject=parsed_email.get("subject", ""),
        url_count=len(urls),
        threatening_url_count=url_threat_results.get("threatening_urls", 0),
        ip_address=request.client.host if request.client else "unknown",
        result_data={
            "authentication": auth_results,
            "url_analysis": url_threat_results,
            "risk_factors": risk_factors,
        }
    )
    
    db.add(scan_record)
    db.commit()
    db.refresh(scan_record)
    
    # --- Return Hasil ---
    return {
        "verdict": verdict,
        "risk_score": min(risk_score, 100),
        "scan_id": scan_record.id,
        "scanned_at": scan_record.scanned_at.isoformat(),
        "risk_factors": risk_factors,
        "details": {
            "from_domain": parsed_email["from_domain"],
            "subject": parsed_email["subject"],
            "authentication": auth_results,
            "url_analysis": url_threat_results,
            "urls_found": len(urls),
        },
        "sanitized_body_preview": sanitize_html(parsed_email.get("html", ""))[:1000] if parsed_email.get("html") else None,
        "email_subject": parsed_email.get("subject", ""),
        "from_domain": parsed_email.get("from_domain", ""),
    }

# ===========================================
# Include Routers
# ===========================================
app.include_router(history_router, prefix=f"{settings.API_V1_STR}", tags=["History"])

# ===========================================
# Main Entry Point
# ===========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )