-- Queries to Answer Questions

-- 1. How much on-chain bridging activity did Grail appear to generate?
SELECT SUM(amount_usd) AS total_bridging_activity_usd
FROM NEAR.DEFI.EZ_BRIDGE_ACTIVITY
WHERE block_timestamp BETWEEN '2024-06-24' AND '2024-07-14';

-- 2. How did the volume of bridging activity change over time?
SELECT block_timestamp::DATE AS date, SUM(amount_usd) AS daily_bridging_activity_usd
FROM NEAR.DEFI.EZ_BRIDGE_ACTIVITY
WHERE block_timestamp BETWEEN '2024-06-24' AND '2024-07-14'
GROUP BY block_timestamp::DATE
ORDER BY date;

-- 3. What chains and tokens were the biggest source of bridged capital?
SELECT source_chain, symbol, SUM(amount_usd) AS total_bridged_usd
FROM NEAR.DEFI.EZ_BRIDGE_ACTIVITY
WHERE block_timestamp BETWEEN '2024-06-24' AND '2024-07-14'
GROUP BY source_chain, symbol
ORDER BY total_bridged_usd DESC;

-- 4. How long did users keep their capital bridged over to NEAR?
SELECT source_address, MIN(block_timestamp) AS first_bridge_in, MAX(block_timestamp) AS last_bridge_out,
DATEDIFF('second', MIN(block_timestamp), MAX(block_timestamp)) AS duration_seconds
FROM NEAR.DEFI.EZ_BRIDGE_ACTIVITY
WHERE direction = 'inbound'
AND block_timestamp BETWEEN '2024-06-24' AND '2024-07-14'
GROUP BY source_address;

-- 5. Once the program was over, did they keep their capital in NEAR, or remove it?
SELECT direction, SUM(amount_usd) AS total_amount_usd
FROM NEAR.DEFI.EZ_BRIDGE_ACTIVITY
WHERE block_timestamp BETWEEN '2024-07-14' AND '2024-07-20' -- assuming one week post-program analysis
GROUP BY direction;

-- 6. How much capital flowed into vs. out of NEAR via bridging during the program?
SELECT direction, SUM(amount_usd) AS total_amount_usd
FROM NEAR.DEFI.EZ_BRIDGE_ACTIVITY
WHERE block_timestamp BETWEEN '2024-06-24' AND '2024-07-14'
GROUP BY direction;

-- 7. What % of bridge activity qualified for Grail during the program period?
SELECT
SUM(CASE WHEN direction = 'inbound' THEN amount_usd ELSE 0 END) / SUM(amount_usd) * 100 AS grail_qualified_percentage
FROM NEAR.DEFI.EZ_BRIDGE_ACTIVITY
WHERE block_timestamp BETWEEN '2024-06-24' AND '2024-07-14';

-- 8. How did bridging activity change during the program, compared with the periods before and after it?
WITH periods AS (
    SELECT
        'before' AS period,
        block_timestamp,
        amount_usd
    FROM NEAR.DEFI.EZ_BRIDGE_ACTIVITY
    WHERE block_timestamp < '2024-06-24'
    UNION ALL
    SELECT
        'during' AS period,
        block_timestamp,
        amount_usd
    FROM NEAR.DEFI.EZ_BRIDGE_ACTIVITY
    WHERE block_timestamp BETWEEN '2024-06-24' AND '2024-07-14'
    UNION ALL
    SELECT
        'after' AS period,
        block_timestamp,
        amount_usd
    FROM NEAR.DEFI.EZ_BRIDGE_ACTIVITY
    WHERE block_timestamp > '2024-07-14'
)
SELECT period, SUM(amount_usd) AS total_amount_usd
FROM periods
GROUP BY period;
