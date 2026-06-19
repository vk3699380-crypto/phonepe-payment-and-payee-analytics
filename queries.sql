-- ====================================================================
-- PhonePe Payment Insights - SQL Queries (SQLite Compatible)
-- ====================================================================

-- --------------------------------------------------------------------
-- INTERMEDIATE LEVEL QUESTIONS
-- --------------------------------------------------------------------

-- 1. How do you find the top 5 states by total transaction amount?
-- Analysis: Aggregate transaction amount by state and sort in descending order.
-- Displays the states that contribute the most to digital payments.
SELECT 
    state,
    SUM(transaction_count) AS total_transactions,
    ROUND(SUM(transaction_amount), 2) AS total_amount
FROM 
    agg_trans
GROUP BY 
    state
ORDER BY 
    total_amount DESC
LIMIT 5;


-- 2. How to calculate growth in SQL (Quarter-over-Quarter / Year-over-Year)?
-- Analysis: Since our PhonePe data is stored quarterly, we calculate 
-- Quarter-over-Quarter (QoQ) growth using the LAG() window function.
WITH quarterly_totals AS (
    SELECT 
        year,
        quarter,
        SUM(transaction_amount) AS total_amount
    FROM 
        agg_trans
    GROUP BY 
        year, 
        quarter
),
growth_calc AS (
    SELECT 
        year,
        quarter,
        total_amount,
        LAG(total_amount, 1) OVER (ORDER BY year, quarter) AS prev_quarter_amount
    FROM 
        quarterly_totals
)
SELECT 
    year,
    quarter,
    ROUND(total_amount, 2) AS current_amount,
    ROUND(prev_quarter_amount, 2) AS previous_amount,
    CASE 
        WHEN prev_quarter_amount IS NULL THEN 'N/A'
        ELSE ROUND(((total_amount - prev_quarter_amount) / prev_quarter_amount) * 100, 2) || '%'
    END AS qoq_growth_rate
FROM 
    growth_calc;


-- 3. What is a subquery? Give an example.
-- Example: Identify states whose average transaction amount per quarter 
-- is higher than the overall national average transaction amount per quarter.
SELECT 
    state, 
    ROUND(AVG(transaction_amount), 2) AS state_quarterly_avg
FROM 
    agg_trans
GROUP BY 
    state
HAVING 
    AVG(transaction_amount) > (
        SELECT AVG(transaction_amount) 
        FROM agg_trans
    )
ORDER BY 
    state_quarterly_avg DESC;


-- --------------------------------------------------------------------
-- ADVANCED LEVEL QUESTIONS
-- --------------------------------------------------------------------

-- 1. Explain Window Functions: ROW_NUMBER(), RANK(), and DENSE_RANK()
-- Example: Rank states by total transaction amount within each year and quarter 
-- to show how rankings shift over time, comparing the three ranking methods.
WITH state_rankings AS (
    SELECT 
        year,
        quarter,
        state,
        SUM(transaction_amount) AS total_amount
    FROM 
        agg_trans
    GROUP BY 
        year, 
        quarter, 
        state
)
SELECT 
    year,
    quarter,
    state,
    ROUND(total_amount, 2) AS total_amount,
    ROW_NUMBER() OVER (
        PARTITION BY year, quarter 
        ORDER BY total_amount DESC
    ) AS row_num,
    RANK() OVER (
        PARTITION BY year, quarter 
        ORDER BY total_amount DESC
    ) AS rnk,
    DENSE_RANK() OVER (
        PARTITION BY year, quarter 
        ORDER BY total_amount DESC
    ) AS dense_rnk
FROM 
    state_rankings
WHERE 
    year = 2023 AND quarter = 4
LIMIT 10;


-- 2. Write a query to find duplicate transactions
-- In this dataset, a duplicate can be defined as multiple records sharing 
-- the exact same state, year, quarter, transaction_type, count, and amount.
SELECT 
    state, 
    year, 
    quarter, 
    transaction_type, 
    transaction_count, 
    transaction_amount, 
    COUNT(*) AS occurrence_count
FROM 
    agg_trans
GROUP BY 
    state, 
    year, 
    quarter, 
    transaction_type, 
    transaction_count, 
    transaction_amount
HAVING 
    COUNT(*) > 1;


-- 3. Handling NULL values in SQL
-- Example: Show how to safely calculate total app opens and handle missing device counts.
-- COALESCE() or IFNULL() replaces NULL with 0 to prevent issues in downstream models.
SELECT 
    state,
    year,
    quarter,
    COALESCE(brand, 'Unknown Brand') AS device_brand,
    SUM(COALESCE(user_count, 0)) AS total_device_users,
    ROUND(SUM(COALESCE(percentage, 0.0)) * 100, 2) || '%' AS brand_percentage
FROM 
    agg_user
GROUP BY 
    state, 
    year, 
    quarter, 
    brand
ORDER BY 
    state, year, quarter, total_device_users DESC
LIMIT 10;
