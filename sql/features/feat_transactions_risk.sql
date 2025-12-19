-- Stage 5B: Aggregate risk features for transactions
-- Purpose:
--   - Add card-level and merchant-level historical risk context
--   - Use rolling 30-day aggregates to provide risk signals
--   - Features support analytics, BI, and ML-lite models
--
-- Rules:
--   - SQL only, no Python
--   - Base table: feat_transactions
--   - Preserve one row per transaction (no filtering, no deduplication)
--   - No DISTINCT window functions
--   - Aggregates must be explainable

USE fraud_db;

-- Recreate the risk feature table each time this script is run
DROP TABLE IF EXISTS feat_transactions_risk;

CREATE TABLE feat_transactions_risk AS
WITH
-- Base: all columns from feat_transactions
base AS (
    SELECT *
    FROM feat_transactions
),

-- Card-level daily aggregates (by card_id_clean, date)
card_daily_agg AS (
    SELECT
        b.card_id_clean,
        DATE(b.txn_ts) AS txn_date,
        COUNT(*) AS txn_count,
        AVG(CASE WHEN b.is_fraud = 1 THEN 1.0 ELSE 0.0 END) AS fraud_rate,
        AVG(CASE WHEN b.is_declined = TRUE THEN 1.0 ELSE 0.0 END) AS decline_rate
    FROM base b
    WHERE b.card_id_clean IS NOT NULL
      AND b.txn_ts IS NOT NULL
    GROUP BY b.card_id_clean, DATE(b.txn_ts)
),

-- Card-level 30-day rolling aggregates using window functions
card_30d_agg AS (
    SELECT
        cda.card_id_clean,
        cda.txn_date,
        -- Rolling sum of transaction count over last 30 days
        SUM(cda.txn_count) OVER (
            PARTITION BY cda.card_id_clean
            ORDER BY cda.txn_date
            RANGE BETWEEN INTERVAL 30 DAY PRECEDING AND CURRENT ROW
        ) AS card_txn_count_30d,
        -- Rolling average of fraud rate over last 30 days
        AVG(cda.fraud_rate) OVER (
            PARTITION BY cda.card_id_clean
            ORDER BY cda.txn_date
            RANGE BETWEEN INTERVAL 30 DAY PRECEDING AND CURRENT ROW
        ) AS card_fraud_rate_30d,
        -- Rolling average of decline rate over last 30 days
        AVG(cda.decline_rate) OVER (
            PARTITION BY cda.card_id_clean
            ORDER BY cda.txn_date
            RANGE BETWEEN INTERVAL 30 DAY PRECEDING AND CURRENT ROW
        ) AS card_decline_rate_30d
    FROM card_daily_agg cda
),

-- Merchant-level daily aggregates (by merchant_id_clean, date)
merchant_daily_agg AS (
    SELECT
        b.merchant_id_clean,
        DATE(b.txn_ts) AS txn_date,
        COUNT(*) AS txn_count,
        AVG(CASE WHEN b.is_fraud = 1 THEN 1.0 ELSE 0.0 END) AS fraud_rate,
        AVG(CASE WHEN b.is_declined = TRUE THEN 1.0 ELSE 0.0 END) AS decline_rate
    FROM base b
    WHERE b.merchant_id_clean IS NOT NULL
      AND b.txn_ts IS NOT NULL
    GROUP BY b.merchant_id_clean, DATE(b.txn_ts)
),

-- Merchant-level 30-day rolling aggregates using window functions
merchant_30d_agg AS (
    SELECT
        mda.merchant_id_clean,
        mda.txn_date,
        -- Rolling sum of transaction count over last 30 days
        SUM(mda.txn_count) OVER (
            PARTITION BY mda.merchant_id_clean
            ORDER BY mda.txn_date
            RANGE BETWEEN INTERVAL 30 DAY PRECEDING AND CURRENT ROW
        ) AS merchant_txn_count_30d,
        -- Rolling average of fraud rate over last 30 days
        AVG(mda.fraud_rate) OVER (
            PARTITION BY mda.merchant_id_clean
            ORDER BY mda.txn_date
            RANGE BETWEEN INTERVAL 30 DAY PRECEDING AND CURRENT ROW
        ) AS merchant_fraud_rate_30d,
        -- Rolling average of decline rate over last 30 days
        AVG(mda.decline_rate) OVER (
            PARTITION BY mda.merchant_id_clean
            ORDER BY mda.txn_date
            RANGE BETWEEN INTERVAL 30 DAY PRECEDING AND CURRENT ROW
        ) AS merchant_decline_rate_30d
    FROM merchant_daily_agg mda
),

-- Join card-level aggregates back to base transactions
with_card_risk AS (
    SELECT
        b.*,
        COALESCE(ca.card_txn_count_30d, 0) AS card_txn_count_30d,
        COALESCE(ca.card_fraud_rate_30d, 0) AS card_fraud_rate_30d,
        COALESCE(ca.card_decline_rate_30d, 0) AS card_decline_rate_30d
    FROM base b
    LEFT JOIN card_30d_agg ca
        ON b.card_id_clean = ca.card_id_clean
       AND DATE(b.txn_ts) = ca.txn_date
),

-- Join merchant-level aggregates back to transactions
with_merchant_risk AS (
    SELECT
        wcr.*,
        COALESCE(ma.merchant_txn_count_30d, 0) AS merchant_txn_count_30d,
        COALESCE(ma.merchant_fraud_rate_30d, 0) AS merchant_fraud_rate_30d,
        COALESCE(ma.merchant_decline_rate_30d, 0) AS merchant_decline_rate_30d
    FROM with_card_risk wcr
    LEFT JOIN merchant_30d_agg ma
        ON wcr.merchant_id_clean = ma.merchant_id_clean
       AND DATE(wcr.txn_ts) = ma.txn_date
)

-- Final projection: all columns from feat_transactions + risk features
SELECT *
FROM with_merchant_risk;

