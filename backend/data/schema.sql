-- Tabel untuk menyimpan history scan
CREATE TABLE IF NOT EXISTS scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(255) NOT NULL,
    verdict VARCHAR(20) NOT NULL,  -- 'safe', 'suspicious', 'phishing'
    risk_score INTEGER NOT NULL,
    from_domain VARCHAR(255),
    from_email VARCHAR(255),
    subject VARCHAR(500),
    url_count INTEGER DEFAULT 0,
    threatening_url_count INTEGER DEFAULT 0,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),  -- Untuk audit
    result_data JSON  -- Full response stored untuk detail view
);

-- Index untuk performa search & filter
CREATE INDEX IF NOT EXISTS idx_scanned_at ON scan_history(scanned_at);
CREATE INDEX IF NOT EXISTS idx_verdict ON scan_history(verdict);
CREATE INDEX IF NOT EXISTS idx_filename ON scan_history(filename);

-- Tabel untuk cleanup job tracking
CREATE TABLE IF NOT EXISTS cleanup_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    records_deleted INTEGER,
    status VARCHAR(20)  -- 'success', 'failed'
);