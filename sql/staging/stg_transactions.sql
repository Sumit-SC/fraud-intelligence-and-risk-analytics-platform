-- Stage 3: Staging layer for transactions only
-- Purpose:
--   - Clean and standardize raw transaction data
--   - Preserve raw values alongside cleaned / typed columns
--   - Prepare for downstream analytics, BI, and ML-lite
--
-- Rules:
--   - SQL only, no Python
--   - No joins
--   - No deduplication
--   - No filtering out rows
--   - No indexes
--   - No feature engineering beyond what is listed

USE fraud_db;

-- Recreate the staging table each time this script is run
DROP TABLE IF EXISTS stg_transactions;

CREATE TABLE stg_transactions AS
WITH
-- STEP 1: Basic column cleanup (trim + empty string to NULL)
base AS (
    SELECT
        -- Preserve raw values with *_raw suffix
        txn_id                       AS txn_id_raw,
        txn_ts                       AS txn_ts_raw,
        amount                       AS amount_raw,
        card_id                      AS card_id_raw,
        merchant_id                  AS merchant_id_raw,
        device_id                    AS device_id_raw,
        channel                      AS channel_raw,
        country                      AS country_raw,
        auth_result                  AS auth_result_raw,
        is_fraud                     AS is_fraud_raw,

        -- Cleaned string versions (trimmed, '' → NULL)
        NULLIF(TRIM(txn_id), '')        AS txn_id_clean,
        NULLIF(TRIM(txn_ts), '')        AS txn_ts_clean,
        NULLIF(TRIM(amount), '')        AS amount_clean,
        NULLIF(TRIM(card_id), '')       AS card_id_clean,
        NULLIF(TRIM(merchant_id), '')   AS merchant_id_clean,
        NULLIF(TRIM(device_id), '')     AS device_id_clean,
        NULLIF(TRIM(channel), '')       AS channel_clean,
        NULLIF(TRIM(country), '')       AS country_clean,
        NULLIF(TRIM(auth_result), '')   AS auth_result_clean,
        NULLIF(TRIM(is_fraud), '')      AS is_fraud_clean
    FROM raw_transactions
),

-- STEP 2: Type casting for txn_ts, amount, is_fraud
typed AS (
    SELECT
        b.*,

        -- Safe timestamp cast: invalid formats become NULL
        STR_TO_DATE(b.txn_ts_clean, '%Y-%m-%d %H:%i:%s') AS txn_ts,

        -- Safe numeric cast for amount: non-numeric → NULL
        CASE
            WHEN b.amount_clean REGEXP '^-?[0-9]+(\\.[0-9]+)?$'
                THEN CAST(b.amount_clean AS DECIMAL(12,2))
            ELSE NULL
        END AS amount,

        -- is_fraud as boolean from cleaned string
        CASE
            WHEN LOWER(b.is_fraud_clean) IN ('1', 'true', 'yes', 'y') THEN TRUE
            WHEN LOWER(b.is_fraud_clean) IN ('0', 'false', 'no', 'n') THEN FALSE
            ELSE NULL
        END AS is_fraud
    FROM base b
),

-- STEP 3: Standardize categoricals
standardized AS (
    SELECT
        t.*,

        -- auth_result_std: APPROVED / DECLINED / OTHER
        CASE
            WHEN UPPER(t.auth_result_clean) = 'APPROVED' THEN 'APPROVED'
            WHEN UPPER(t.auth_result_clean) = 'DECLINED' THEN 'DECLINED'
            WHEN t.auth_result_clean IS NULL              THEN NULL
            ELSE 'OTHER'
        END AS auth_result_std,

        -- channel_std: WEB / MOBILE / POS / API / OTHER
        CASE
            WHEN UPPER(t.channel_clean) IN ('WEB', 'ONLINE')          THEN 'WEB'
            WHEN UPPER(t.channel_clean) IN ('MOBILE', 'APP')          THEN 'MOBILE'
            WHEN UPPER(t.channel_clean) IN ('POS', 'POINT_OF_SALE')   THEN 'POS'
            WHEN UPPER(t.channel_clean) = 'API'                       THEN 'API'
            WHEN t.channel_clean IS NULL                              THEN NULL
            ELSE 'OTHER'
        END AS channel_std,

        -- country_std: uppercase 2-letter where possible, else OTHER
        CASE
            WHEN t.country_clean IS NULL THEN NULL
            WHEN LENGTH(TRIM(t.country_clean)) = 2
                THEN UPPER(TRIM(t.country_clean))
            ELSE 'OTHER'
        END AS country_std
    FROM typed t
),

-- STEP 4: Basic derived columns
derived AS (
    SELECT
        s.*,

        -- Date and hour derived from txn_ts
        DATE(s.txn_ts)           AS txn_date,
        HOUR(s.txn_ts)           AS txn_hour,

        -- Simple flags
        CASE
            WHEN s.auth_result_std = 'DECLINED' THEN TRUE
            ELSE FALSE
        END AS is_declined,

        CASE
            WHEN s.amount = 0 THEN TRUE
            ELSE FALSE
        END AS is_zero_amount,

        CASE
            WHEN s.amount < 0 THEN TRUE
            ELSE FALSE
        END AS is_negative_amt,

        CASE
            WHEN s.amount > 10000 THEN TRUE
            ELSE FALSE
        END AS is_high_amount
    FROM standardized s
)

-- Final projection: include raw, cleaned, typed, standardized, and derived
SELECT
    -- Raw identifiers
    txn_id_raw,
    txn_ts_raw,
    amount_raw,
    card_id_raw,
    merchant_id_raw,
    device_id_raw,
    channel_raw,
    country_raw,
    auth_result_raw,
    is_fraud_raw,

    -- Cleaned strings
    txn_id_clean,
    txn_ts_clean,
    amount_clean,
    card_id_clean,
    merchant_id_clean,
    device_id_clean,
    channel_clean,
    country_clean,
    auth_result_clean,

    -- Typed / standardized / derived columns
    txn_ts,
    amount,
    is_fraud,
    auth_result_std,
    channel_std,
    country_std,
    txn_date,
    txn_hour,
    is_declined,
    is_zero_amount,
    is_negative_amt,
    is_high_amount
FROM derived;


