-- ============================================================
--  CyberRakshak AI — MySQL Schema
--  Run: mysql -u root -p < database/schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS cyberrakshak_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE cyberrakshak_db;

-- -------------------------------------------------------
-- incidents
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS incidents (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    incident_id      VARCHAR(20)  NOT NULL UNIQUE,
    incident_category VARCHAR(100) NOT NULL,
    description      TEXT         NOT NULL,
    incident_date    DATE,
    incident_time    TIME,
    platform         VARCHAR(100),
    financial_loss   DECIMAL(12,2) DEFAULT 0.00,
    ongoing_status   TINYINT(1)   DEFAULT 0,
    created_at       DATETIME     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (incident_category),
    INDEX idx_created  (created_at)
) ENGINE=InnoDB;

-- -------------------------------------------------------
-- evidence
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS evidence (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    incident_id        VARCHAR(20)  NOT NULL,
    file_name          VARCHAR(255) NOT NULL,
    file_type          VARCHAR(50),
    storage_reference  VARCHAR(500),
    extracted_text     TEXT,
    upload_timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id) ON DELETE CASCADE,
    INDEX idx_ev_incident (incident_id)
) ENGINE=InnoDB;

-- -------------------------------------------------------
-- incident_timeline
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS incident_timeline (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    incident_id       VARCHAR(20)  NOT NULL,
    event_description TEXT         NOT NULL,
    event_timestamp   DATETIME,
    source_type       VARCHAR(50)  DEFAULT 'system',
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id) ON DELETE CASCADE,
    INDEX idx_tl_incident (incident_id)
) ENGINE=InnoDB;

-- -------------------------------------------------------
-- scam_analysis
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS scam_analysis (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    incident_id      VARCHAR(20)  NOT NULL UNIQUE,
    potential_category VARCHAR(100),
    risk_level       VARCHAR(30),
    indicators       TEXT,
    explanation      TEXT,
    recommendations  TEXT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- -------------------------------------------------------
-- workflow_logs
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS workflow_logs (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    workflow_id      VARCHAR(20)  NOT NULL,
    agent_name       VARCHAR(100) NOT NULL,
    execution_status VARCHAR(30)  NOT NULL,
    message          TEXT,
    timestamp        DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_wf_workflow (workflow_id)
) ENGINE=InnoDB;
