-- ============================================================
--  CyberRakshak AI — Seed Demo Data (Bengaluru Synthetic Scenario)
--  CLEARLY LABELLED SYNTHETIC DATA — NOT REAL INCIDENTS
-- ============================================================

USE cyberrakshak_db;

INSERT IGNORE INTO incidents
    (incident_id, incident_category, description, incident_date, incident_time, platform, financial_loss, ongoing_status)
VALUES
    ('INC-DEMO-001',
     'UPI Fraud / Fake KYC',
     '[SYNTHETIC DEMO] Received SMS claiming SBI account will be blocked. Clicked link, filled form. Later noticed ₹5,000 deducted via UPI.',
     '2024-07-15', '14:30:00', 'UPI / Mobile Banking', 5000.00, 0);

INSERT IGNORE INTO scam_analysis
    (incident_id, potential_category, risk_level, indicators, explanation, recommendations)
VALUES
    ('INC-DEMO-001',
     'Phishing + UPI Fraud',
     'Critical',
     'Urgency tactic; fake KYC claim; suspicious link; unauthorized UPI transaction',
     'Classic smishing attack. Fraudster impersonated bank, used urgency to trick victim into entering credentials on phishing site.',
     'Call 1930 immediately; block UPI on banking app; report at cybercrime.gov.in');

INSERT IGNORE INTO incident_timeline
    (incident_id, event_description, event_timestamp, source_type)
VALUES
    ('INC-DEMO-001', 'SMS received claiming KYC update required', '2024-07-15 14:25:00', 'user_reported'),
    ('INC-DEMO-001', 'User clicked link in SMS', '2024-07-15 14:28:00', 'user_reported'),
    ('INC-DEMO-001', 'Credentials entered on suspicious website', '2024-07-15 14:30:00', 'user_reported'),
    ('INC-DEMO-001', 'Unauthorized UPI transaction of ₹5,000 detected', '2024-07-15 14:35:00', 'user_reported'),
    ('INC-DEMO-001', 'Incident reported to CyberRakshak AI', '2024-07-15 15:00:00', 'system');
