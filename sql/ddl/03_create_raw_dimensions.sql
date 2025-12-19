USE fraud_db;

-- Raw merchants table (as-ingested, no constraints)
CREATE TABLE IF NOT EXISTS raw_merchants (
    merchant_id     VARCHAR(64),
    merchant_name   VARCHAR(255),
    mcc             VARCHAR(16),
    country         VARCHAR(16),
    risk_tier       VARCHAR(16)
);

-- Raw devices table (as-ingested, no constraints)
CREATE TABLE IF NOT EXISTS raw_devices (
    device_id   VARCHAR(64),
    os          VARCHAR(64),
    browser     VARCHAR(64),
    is_emulator VARCHAR(8)
);

-- Raw cards table (as-ingested, no constraints)
CREATE TABLE IF NOT EXISTS raw_cards (
    card_id   VARCHAR(64),
    bin       VARCHAR(16),
    issuer    VARCHAR(64),
    card_type VARCHAR(16)
);

-- Raw rule hits table (as-ingested, no constraints)
CREATE TABLE IF NOT EXISTS raw_rule_hits (
    txn_id     VARCHAR(64),
    rule_name  VARCHAR(64),
    rule_score VARCHAR(16)
);

-- Raw investigator notes table (as-ingested, no constraints)
CREATE TABLE IF NOT EXISTS raw_investigator_notes (
    txn_id     VARCHAR(64),
    note_text  VARCHAR(1024),
    created_at VARCHAR(64)
);


