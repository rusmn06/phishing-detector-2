# Struktur Folder Lengkap
Struktur ini mencerminkan keadaan proyek saat ini setelah implementasi **Validasi, Parsing, Analisis SPF/DMARC, Sanitasi HTML, dan Integrasi VirusTotal**.

phising-detector/
│
├── backend/                        # FastAPI Application
│   ├── .venv/                      # Python Virtual Environment (IGNORED in Git)
│   ├── core/                       # Core Business Logic
│   │   ├── __init__.py
│   │   ├── analysis.py             # Logika scoring risiko & agregasi hasil
│   │   ├── dns_resolver.py         # DNS Resolver dengan timeout control
│   │   ├── email_parser.py         # Parsing file .eml (mailparser) + sanitasi awal
│   │   ├── safe_browsing.py        # Adapter Google Safe Browsing (Legacy/Optional)
│   │   ├── virustotal.py           # Adapter VirusTotal API v3
│   │   ├── threat_detector.py      # Factory Pattern untuk switch provider
│   │   └── url_extractor.py        # Ekstraksi URL dari konten email
│   │
│   ├── utils/                      # Utility Functions
│   │   ├── __init__.py
│   │   ├── file_validator.py       # Validasi Magic Bytes & Ukuran File
│   │   └── sanitizer.py            # Sanitasi HTML output (bleach)
│   │
│   ├── tests/                      # Unit & Integration Tests
│   │   ├── __init__.py
│   │   ├── test_file_validator.py
│   │   ├── test_email_parser.py
│   │   └── test_threat_detector.py
│   │
│   ├── config.py                   # Konfigurasi Environment (Pydantic Settings)
│   ├── main.py                     # Entry Point FastAPI & API Routes
│   ├── models.py                   # Pydantic Models untuk Request/Response
│   ├── requirements.txt            # Python Dependencies
│   └── README.md                   # Dokumentasi Khusus Backend (Lihat di bawah)
│
├── frontend/                       # React Application (Vite + Tailwind)
│   ├── node_modules/               # Node Dependencies (IGNORED in Git)
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadArea.jsx
│   │   │   ├── ScanResult.jsx
│   │   │   └── LoadingSpinner.jsx
│   │   ├── services/
│   │   │   └── api.js              # Axios instance
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── infrastructure/                 # Infrastructure-as-Code
│   ├── nginx/
│   │   ├── nginx.conf              # Reverse Proxy & Security Headers
│   │   └── certs/                  # SSL Certificates (IGNORED in Git)
│   ├── logs/                       # Log Files (Auto-generated)
│   ├── docker-compose.yml          # Orkestrasi Services
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
│
├── .env                            # Environment Variables (IGNORED in Git!)
├── .env.example                    # Template Environment Variables
├── .gitignore                      # Git Ignore Rules
└── README.md                       # Project Overview (Root)

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
