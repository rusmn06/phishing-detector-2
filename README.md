# Struktur Folder Lengkap
Struktur ini mencerminkan keadaan proyek saat ini setelah implementasi **Validasi, Parsing, Analisis SPF/DMARC, Sanitasi HTML, dan Integrasi VirusTotal**.

# Email Phishing Scanner - Backend Documentation

Backend aplikasi ini dibangun menggunakan **FastAPI** (Python) dengan arsitektur modular yang mengutamakan keamanan, skalabilitas, dan kemudahan maintenance.

---

## Daftar Isi

1. [Prasyarat](#prasyarat)
2. [Setup Lingkungan Pengembangan](#setup-lingkungan-pengembangan)
3. [Struktur Modul](#struktur-modul)
4. [Konfigurasi Environment Variables](#konfigurasi-environment-variables)
5. [Panduan Mengganti Provider Deteksi URL](#panduan-mengganti-provider-deteksi-url)
6. [Menjalankan Server](#menjalankan-server)
7. [Testing API](#testing-api)
8. [Troubleshooting](#troubleshooting)

---

## Prasyarat

- Python 3.12 atau lebih baru
- pip (Python Package Manager)
- Virtual Environment (venv)

---

## Setup Lingkungan Pengembangan

### 1. Buat Virtual Environment
```bash
cd backend
python -m venv .venv
```

### 2. Aktifkan Virtual Environment
```bash
.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Setup Environment Variables
Salin file **.env.example** dari root proyek menjadi **.env**:
```bash
cp ../.env.example ../.env
```

## Struktur Modul
|Modul |Fungsi Utama|
|:----|:----------|
|main.py|Entry point, definisi endpoint API, middleware CORS.|
|config.py|Manajemen konfigurasi menggunakan Pydantic Settings (membaca .env).|
|models.py|Schema validasi request/response menggunakan Pydantic.|
|core/analysis.py|Logika scoring risiko berdasarkan SPF, DMARC, dan ancaman URL.|
|core/dns_resolver.py|DNS resolver dengan timeout ketat untuk mencegah hanging.|
|core/email_parser.py|Parsing file .eml menggunakan mailparser.|
|core/threat_detector.py|Factory Pattern: Memilih adapter provider (Google/VirusTotal).|
|core/virustotal.py|Adapter spesifik untuk VirusTotal API v3.|
|core/safe_browsing.py|Adapter spesifik untuk Google Safe Browsing API.|
|utils/file_validator.py|Validasi file upload: Magic Bytes (message/rfc822) + Max 10MB.|
|utils/sanitizer.py|Sanitasi HTML output menggunakan bleach untuk mencegah XSS.|

## Konfigurasi Environment Variables
```bash
# --- Application Settings ---
APP_ENV=development
API_V1_STR=/api/v1

# API untuk detect email dns dan phisng URL.
# Dapatkan di: console.cloud.google.com/apis/credentials
GOOGLE_SAFE_BROWSING_API_KEY=your_google_api_key_here

# API untuk detect phishing URL.
# Dapatkan di: https://www.virustotal.com/gui/my-apikey
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here

# --- URL Threat Detection Provider ---
# PILIHAN: "google_safe_browsing", "virustotal", "both"
# Default: virustotal
URL_THREAT_PROVIDER=virustotal

# --- Rate Limiting ---
RATE_LIMIT=5/minute

# --- DNS Settings ---
DNS_TIMEOUT=5.0
```
