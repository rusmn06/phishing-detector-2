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

# Buat dan aktifkan virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Buat folder database
mkdir -p data

# Jalankan server
uvicorn main:app --reload --port 8000
```

Backend berjalan di: `http://localhost:8000`
API docs tersedia di: `http://localhost:8000/api/v1/docs`

---

### 3 — Setup Frontend

```bash
# Di terminal baru
cd frontend

npm install
npm run dev
```

Frontend berjalan di: `http://localhost:5173`

---

### Windows Shortcut

Untuk menjalankan keduanya sekaligus di Windows:

```bat
start-dev.bat
```

---

## API Endpoints

### Scanning

| Method | Endpoint | Deskripsi |
|---|---|---|
| `POST` | `/api/v1/scan` | Scan file `.eml` (multipart/form-data) |
| `POST` | `/api/v1/scan-url` | Scan URL langsung |

### History

| Method | Endpoint | Deskripsi |
|---|---|---|
| `GET` | `/api/v1/history` | List history dengan filter & pagination |
| `GET` | `/api/v1/history/{id}` | Detail scan by ID |
| `DELETE` | `/api/v1/history/{id}` | Hapus record scan |
| `POST` | `/api/v1/history/cleanup` | Trigger cleanup record lama |
| `GET` | `/api/v1/history/cleanup/logs` | Log cleanup job |

### Dashboard & Monitoring

| Method | Endpoint | Deskripsi |
|---|---|---|
| `GET` | `/api/v1/dashboard/stats` | Statistik total scan, verdict breakdown |
| `GET` | `/api/v1/quota-status` | Status sisa quota API |
| `GET` | `/api/v1/health` | Health check |

---

## Cara Kerja Scan Email

```
Upload .eml
    │
    ▼
[1] Validasi File
    ├── Magic bytes check (message/rfc822)
    └── Ukuran ≤ 10 MB

    │
    ▼
[2] Parse Email
    ├── Ekstrak header (From, Subject)
    ├── Ekstrak body (text + HTML)
    └── Ekstrak semua URL

    │
    ▼
[3] Analisis Otentikasi (parallel)
    ├── SPF check via checkdmarc
    └── DMARC check via checkdmarc

    │
    ▼
[4] Analisis URL
    └── Google Safe Browsing / VirusTotal / both

    │
    ▼
[5] Hitung Skor Risiko
    ├── DMARC fail  → +40
    ├── SPF fail    → +30
    ├── DKIM tidak dikonfigurasi → +20
    ├── URL berbahaya terdeteksi → +60
    └── Error check URL → +15

    │
    ▼
[6] Verdict
    ├── Score ≥ 70 → PHISHING
    ├── Score ≥ 40 → SUSPICIOUS
    └── Score < 40 → SAFE
```

---

## Konfigurasi Environment Variables

| Variable | Default | Keterangan |
|---|---|---|
| `APP_ENV` | `development` | Mode aplikasi |
| `GOOGLE_SAFE_BROWSING_API_KEY` | — | **Wajib** untuk URL scan |
| `VIRUSTOTAL_API_KEY` | — | **Wajib** untuk URL scan |
| `SECRET_KEY` | — | Random string untuk keamanan internal |
| `URL_THREAT_PROVIDER` | `virustotal` | `google_safe_browsing` / `virustotal` / `both` |
| `RATE_LIMIT` | `5/minute` | Rate limit endpoint |
| `DNS_TIMEOUT` | `5.0` | Timeout DNS query (detik) |
| `DATABASE_URL` | SQLite lokal | Path database SQLite |
| `HISTORY_RETENTION_DAYS` | `30` | Berapa hari history disimpan |
| `CORS_ORIGINS` | localhost | Daftar origin yang diizinkan |
| `ENABLE_DOCS` | `true` | Aktifkan Swagger UI (`false` di production) |

---

## Mengganti Provider URL Scan

Atur variabel `URL_THREAT_PROVIDER` di `.env`:

```env
# Gunakan hanya VirusTotal (default, lebih detail)
URL_THREAT_PROVIDER=virustotal

# Gunakan hanya Google Safe Browsing (lebih cepat)
URL_THREAT_PROVIDER=google_safe_browsing

# Gunakan keduanya (lebih akurat, quota 2x lebih cepat habis)
URL_THREAT_PROVIDER=both
```

Restart backend setelah mengubah nilai ini.

---

## Batasan Quota API

| Provider | Per Menit | Per Hari | Per Bulan |
|---|---|---|---|
| VirusTotal (Free) | 4 req | 500 req | 15.500 req |
| Google Safe Browsing | — | 10.000 req | — |

Aplikasi otomatis mengelola quota dan menghentikan request jika limit tercapai. Pantau quota di endpoint `/api/v1/quota-status`.

---

## Dokumentasi Lanjutan

| Dokumen | Isi |
|---|---|
| [`DEPLOY_AZURE.md`](./DEPLOY_AZURE.md) | Panduan deploy ke Azure Ubuntu 24 LTS (Nginx + Systemd + HTTPS) |
| `http://localhost:8000/api/v1/docs` | Swagger UI interaktif (saat dev) |
| `http://localhost:8000/api/v1/redoc` | ReDoc API reference (saat dev) |

---

## Kontribusi

1. Fork repository ini
2. Buat branch fitur: `git checkout -b feat/nama-fitur`
3. Commit perubahan: `git commit -m "feat: deskripsi singkat"`
4. Push ke branch: `git push origin feat/nama-fitur`
5. Buat Pull Request

---

*Email Phishing Scanner v1.0.0 — Internal Security Tool*