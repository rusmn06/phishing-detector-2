from pydantic_settings import BaseSettings
from pathlib import Path

# Tentukan path ke file .env (di root proyek, satu level di atas backend/)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    """
    Kelas untuk mengelola konfigurasi aplikasi.
    Menggunakan Pydantic Settings untuk validasi otomatis.
    Sesuai blueprint 'Email Phishing Scanner'
    """
    
    # ===========================================
    # Application Settings (Dari Blueprint)
    # ===========================================
    APP_ENV: str = "development"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "phising-detector-2"
    
    # ===========================================
    # Security & External APIs
    # ===========================================
    # Google Safe Browsing API Key (untuk deteksi email)
    GOOGLE_SAFE_BROWSING_API_KEY: str = ""
    
    # VirusTotal API Key (untuk deteksi URL phishing)
    VIRUSTOTAL_API_KEY: str = ""
    
    # Secret key untuk internal use (JWT, session, dll)
    SECRET_KEY: str = "change-this-to-random-string-in-production"
    
    # ===========================================
    # URL Threat Detection Provider
    # ===========================================
    # Pilihan: "google_safe_browsing", "virustotal", "both"
    URL_THREAT_PROVIDER: str = "virustotal"
    
    # ===========================================
    # Rate Limiting (Dari Blueprint)
    # ===========================================
    RATE_LIMIT: str = "5/minute"
    
    # ===========================================
    # DNS Settings (Dari Blueprint)
    # ===========================================
    DNS_TIMEOUT: float = 5.0
    DNS_NAMESERVERS: str = "8.8.8.8,8.8.4.4"
    
    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Abaikan variabel .env yang tidak didefinisikan

# Inisialisasi instance settings global
settings = Settings()