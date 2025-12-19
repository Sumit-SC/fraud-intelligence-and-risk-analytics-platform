-- Stage 4: Enriched staging layer for transactions
-- Purpose:
--   - Add business context to transactions via LEFT JOINs with dimension tables
--   - Preserve all transaction rows (no filtering, no deduplication)
--   - Prepare enriched data for analytics and BI
--
-- Rules:
--   - SQL only, no Python
--   - LEFT JOINs only (preserves row count)
--   - No window functions
--   - No aggregations
--   - No ML features
--   - No indexes
--   - Readable CTE-based SQL

USE fraud_db;

-- Recreate the enriched staging table each time this script is run
DROP TABLE IF EXISTS stg_transactions_enriched;

CREATE TABLE stg_transactions_enriched AS
WITH
-- Base: all columns from stg_transactions
base AS (
    SELECT *
    FROM stg_transactions
),

-- Join with merchants dimension
with_merchants AS (
    SELECT
        b.*,
        -- Merchant fields (cleaned/standardized from raw)
        NULLIF(TRIM(m.mcc), '')           AS merchant_category,
        NULLIF(TRIM(m.country), '')       AS merchant_country,
        NULLIF(TRIM(m.risk_tier), '')     AS merchant_risk_tier
    FROM base b
    LEFT JOIN raw_merchants m
        ON b.merchant_id_clean = m.merchant_id
),

-- Join with devices dimension
with_devices AS (
    SELECT
        wm.*,
        -- Device fields (cleaned/standardized from raw)
        NULLIF(TRIM(d.os), '')            AS device_type,
        NULLIF(TRIM(d.os), '')            AS os,
        CASE
            WHEN NULLIF(TRIM(d.is_emulator), '') IN ('1', 'true', 'TRUE', 'True', 'yes', 'YES', 'Yes')
                THEN 1
            WHEN NULLIF(TRIM(d.is_emulator), '') IN ('0', 'false', 'FALSE', 'False', 'no', 'NO', 'No')
                THEN 0
            ELSE NULL
        END                               AS is_emulator
    FROM with_merchants wm
    LEFT JOIN raw_devices d
        ON wm.device_id_clean = d.device_id
),

-- Join with cards dimension
with_cards AS (
    SELECT
        wd.*,
        -- Card fields (cleaned/standardized from raw)
        NULLIF(TRIM(c.issuer), '')        AS card_network,
        NULLIF(TRIM(c.card_type), '')    AS card_type,
        -- Note: issuing_country not available in raw_cards, using NULL
        NULL                               AS issuing_country
    FROM with_devices wd
    LEFT JOIN raw_cards c
        ON wd.card_id_clean = c.card_id
),

-- Add simple derived flags
with_flags AS (
    SELECT
        wc.*,
        -- is_high_risk_merchant: merchant_risk_tier = 'HIGH'
        CASE
            WHEN UPPER(wc.merchant_risk_tier) = 'HIGH' THEN TRUE
            ELSE FALSE
        END                               AS is_high_risk_merchant,
        
        -- is_foreign_transaction: transaction country differs from issuing country
        -- Note: Since issuing_country is NULL, this will be FALSE for now
        -- This flag will be meaningful once issuing_country is populated
        CASE
            WHEN wc.country_std IS NOT NULL 
                 AND wc.issuing_country IS NOT NULL
                 AND wc.country_std <> wc.issuing_country
                THEN TRUE
            ELSE FALSE
        END                               AS is_foreign_transaction,
        
        -- is_emulator_device: is_emulator = 1
        CASE
            WHEN wc.is_emulator = 1 THEN TRUE
            ELSE FALSE
        END                               AS is_emulator_device
    FROM with_cards wc
)

-- Final projection: all columns from stg_transactions + dimension fields + flags
SELECT *
FROM with_flags;

