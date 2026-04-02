from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any

class AuthenticationResult(BaseModel):
    """Struktur hasil analisis otentikasi domain."""
    spf: Dict[str, Any]
    dkim: Dict[str, Any]
    dmarc: Dict[str, Any]

class URLAnalysisResult(BaseModel):
    """Struktur hasil analisis URL."""
    total_urls: int
    threatening_urls: int
    threats: List[Dict[str, Any]]
    status: str

class ScanResult(BaseModel):
    """Struktur respons utama untuk endpoint /scan."""
    verdict: str  # "safe", "suspicious", "phishing"
    risk_score: int  # 0-100
    risk_factors: List[str]
    details: Dict[str, Any]
    
    # Field khusus untuk konten aman
    sanitized_body_preview: Optional[str] = None
    email_subject: Optional[str] = None
    from_domain: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "verdict": "safe",
                "risk_score": 15,
                "risk_factors": ["DKIM not configured"],
                "details": {
                    "authentication": {"spf": {"status": "pass"}},
                    "url_analysis": {"total_urls": 2, "threatening_urls": 0}
                },
                "sanitized_body_preview": "<p>Email content here...</p>",
                "email_subject": "Test Email",
                "from_domain": "example.com"
            }
        }

class URLScanRequest(BaseModel):
    """Request model untuk scan URL langsung."""
    url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://suspicious-site.com/login"
            }
        }

class URLScanResult(BaseModel):
    """Result model untuk scan URL."""
    url: str
    verdict: str  # "safe", "suspicious", "malicious"
    risk_score: int  # 0-100
    provider: str
    details: Dict[str, Any]

class AuthenticationResult(BaseModel):
    """Struktur hasil analisis otentikasi domain."""
    spf: Dict[str, Any]
    dkim: Dict[str, Any]
    dmarc: Dict[str, Any]

class ScanResult(BaseModel):
    """Struktur respons utama untuk endpoint /scan."""
    verdict: str
    risk_score: int
    risk_factors: List[str]
    details: Dict[str, Any]
    sanitized_body_preview: Optional[str] = None
    email_subject: Optional[str] = None
    from_domain: Optional[str] = None