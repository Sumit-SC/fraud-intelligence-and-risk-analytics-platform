-- Stage 5A: Feature layer for transactions
-- Purpose:
--   - Add interpretable, transaction-level features using window functions
--   - Features support analytics, BI, and ML-lite models
--   - All features are explainable in plain English
--
-- Rules:
--   - SQL only, no Python
--   - Use stg_transactions_enriched as base
--   - Preserve one row per transaction (no filtering, no deduplication)
--   - No joins to new tables
--   - Window functions allowed
--   - Features must be explainable

USE fraud_db;

-- Recreate the feature table each time this script is run
DROP TABLE IF EXISTS feat_transactions;

CREATE TABLE feat_transactions AS
WITH
-- Base: all columns from stg_transactions_enriched
base AS (
    SELECT *
    FROM stg_transactions_enriched
),

-- Add velocity features (by card_id_clean, time-based windows)
velocity_features AS (
    SELECT
        b.*,
        
        -- txns_last_1h: count of transactions by same card in last 1 hour
        -- NULL if txn_ts is NULL (can't compute time-based window)
        CASE
            WHEN b.txn_ts IS NULL THEN NULL
            ELSE COUNT(*) OVER (
                PARTITION BY b.card_id_clean
                ORDER BY b.txn_ts
                RANGE BETWEEN INTERVAL 1 HOUR PRECEDING AND CURRENT ROW
            )
        END AS txns_last_1h,
        
        -- txns_last_24h: count of transactions by same card in last 24 hours
        -- NULL if txn_ts is NULL
        CASE
            WHEN b.txn_ts IS NULL THEN NULL
            ELSE COUNT(*) OVER (
                PARTITION BY b.card_id_clean
                ORDER BY b.txn_ts
                RANGE BETWEEN INTERVAL 24 HOUR PRECEDING AND CURRENT ROW
            )
        END AS txns_last_24h,
        
        -- amt_last_24h: sum of transaction amounts by same card in last 24 hours
        -- NULL if txn_ts is NULL, 0 if no transactions in window
        CASE
            WHEN b.txn_ts IS NULL THEN NULL
            ELSE COALESCE(
                SUM(b.amount) OVER (
                    PARTITION BY b.card_id_clean
                    ORDER BY b.txn_ts
                    RANGE BETWEEN INTERVAL 24 HOUR PRECEDING AND CURRENT ROW
                ),
                0
            )
        END AS amt_last_24h
        
    FROM base b
),

-- Add decline history features (by card_id_clean)
decline_features AS (
    SELECT
        vf.*,
        
        -- declined_txns_last_24h: count of declined transactions by same card in last 24 hours
        -- NULL if txn_ts is NULL
        CASE
            WHEN vf.txn_ts IS NULL THEN NULL
            ELSE COUNT(CASE WHEN vf.is_declined = TRUE THEN 1 END) OVER (
                PARTITION BY vf.card_id_clean
                ORDER BY vf.txn_ts
                RANGE BETWEEN INTERVAL 24 HOUR PRECEDING AND CURRENT ROW
            )
        END AS declined_txns_last_24h
        
    FROM velocity_features vf
),

-- Add behavioral deviation features
behavioral_features AS (
    SELECT
        df.*,
        
        -- amount_vs_card_avg: ratio of current amount to card's average amount
        -- NULL if card average is 0 or NULL
        CASE
            WHEN df.amount IS NULL THEN NULL
            WHEN AVG(df.amount) OVER (PARTITION BY df.card_id_clean) = 0 THEN NULL
            WHEN AVG(df.amount) OVER (PARTITION BY df.card_id_clean) IS NULL THEN NULL
            ELSE df.amount / NULLIF(AVG(df.amount) OVER (PARTITION BY df.card_id_clean), 0)
        END AS amount_vs_card_avg
        
    FROM decline_features df
),

-- Deduplicate merchants per card: one row per (card_id_clean, merchant_id_clean)
-- Use MIN(txn_ts) as the first occurrence timestamp for each merchant
distinct_merchant_first_seen AS (
    SELECT
        bf.card_id_clean,
        bf.merchant_id_clean,
        MIN(bf.txn_ts) AS first_seen_ts
    FROM behavioral_features bf
    WHERE bf.card_id_clean IS NOT NULL
      AND bf.merchant_id_clean IS NOT NULL
      AND bf.txn_ts IS NOT NULL
    GROUP BY bf.card_id_clean, bf.merchant_id_clean
),

-- Count distinct merchants in 24h window using window function on deduplicated set
-- COUNT(*) counts distinct merchants (one row per merchant) in the 24h window
merchant_counts AS (
    SELECT
        dmfs.card_id_clean,
        dmfs.first_seen_ts AS txn_ts,
        COUNT(*) OVER (
            PARTITION BY dmfs.card_id_clean
            ORDER BY dmfs.first_seen_ts
            RANGE BETWEEN INTERVAL 24 HOUR PRECEDING AND CURRENT ROW
        ) AS distinct_merchants_last_24h
    FROM distinct_merchant_first_seen dmfs
),

-- For each transaction, get the distinct merchant count at that timestamp
-- Use the count from the most recent merchant_counts row <= transaction timestamp
transaction_merchant_counts AS (
    SELECT
        bf.card_id_clean,
        bf.txn_ts,
        COALESCE(MAX(mc.distinct_merchants_last_24h), 0) AS distinct_merchants_last_24h
    FROM behavioral_features bf
    LEFT JOIN merchant_counts mc
        ON mc.card_id_clean = bf.card_id_clean
       AND mc.txn_ts <= bf.txn_ts
    WHERE bf.txn_ts IS NOT NULL
    GROUP BY bf.card_id_clean, bf.txn_ts
),

-- Add merchant exposure features
-- Join back to get distinct merchant count for each transaction
merchant_features AS (
    SELECT
        bf.*,
        
        -- distinct_merchants_last_24h: count of distinct merchants by same card in last 24 hours
        -- NULL if txn_ts is NULL, otherwise get count from transaction_merchant_counts
        CASE
            WHEN bf.txn_ts IS NULL THEN NULL
            ELSE tmc.distinct_merchants_last_24h
        END AS distinct_merchants_last_24h
        
    FROM behavioral_features bf
    LEFT JOIN transaction_merchant_counts tmc
        ON bf.card_id_clean = tmc.card_id_clean
       AND bf.txn_ts = tmc.txn_ts
)

-- Final projection: all columns from stg_transactions_enriched + features
SELECT *
FROM merchant_features;

