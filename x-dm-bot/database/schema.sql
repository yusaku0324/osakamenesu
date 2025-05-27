
-- X DM Bot データベーススキーマ
CREATE TABLE IF NOT EXISTS accounts (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    proxy_url VARCHAR(255),
    settings JSON
);

CREATE TABLE IF NOT EXISTS campaigns (
    id VARCHAR(50) PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    keywords JSON,
    message_templates JSON,
    max_dms_per_hour INT DEFAULT 20,
    check_interval INT DEFAULT 300,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dm_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    campaign_id VARCHAR(50) NOT NULL,
    recipient_username VARCHAR(50) NOT NULL,
    message_sent TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('sent', 'failed', 'pending') DEFAULT 'pending',
    error_message TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    dms_sent INT DEFAULT 0,
    dms_failed INT DEFAULT 0,
    response_rate FLOAT DEFAULT 0,
    engagement_score FLOAT DEFAULT 0,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    UNIQUE KEY unique_account_date (account_id, date)
);

CREATE INDEX idx_dm_history_account ON dm_history(account_id);
CREATE INDEX idx_dm_history_sent_at ON dm_history(sent_at);
CREATE INDEX idx_statistics_date ON statistics(date);
