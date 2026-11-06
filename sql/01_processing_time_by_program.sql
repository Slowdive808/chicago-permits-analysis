-- Question 1: How much faster are the Express and Easy permit programs
-- than standard permits, and has that changed over time?
-- Uses the median instead of the average, because a few permits that took
-- years would pull the average far above what's typical.

-- 1a. Overall comparison
WITH base AS (
  SELECT
    CASE
      WHEN pt.permit_type LIKE '%EXPRESS%' THEN 'Express'
      WHEN pt.permit_type LIKE '%EASY%'    THEN 'Easy'
      ELSE 'Standard'
    END AS program,
    f.processing_days
  FROM fact_permit f
  JOIN dim_permit_type pt ON f.permit_type_key = pt.permit_type_key
  WHERE f.processing_days IS NOT NULL
),
ranked AS (
  SELECT
    program,
    processing_days,
    ROW_NUMBER() OVER (PARTITION BY program ORDER BY processing_days) AS rn,
    COUNT(*)     OVER (PARTITION BY program)                          AS n
  FROM base
)
SELECT
  program,
  MAX(n) AS permits,
  ROUND(AVG(CASE WHEN rn IN (FLOOR((n + 1) / 2), CEIL((n + 1) / 2))
                 THEN processing_days END), 1) AS median_days,
  ROUND(AVG(processing_days), 1)              AS avg_days
FROM ranked
GROUP BY program
ORDER BY median_days;

-- 1b. Median processing days by year, with the change from the prior year
WITH base AS (
  SELECT
    d.year AS issue_year,
    CASE
      WHEN pt.permit_type LIKE '%EXPRESS%' THEN 'Express'
      WHEN pt.permit_type LIKE '%EASY%'    THEN 'Easy'
      ELSE 'Standard'
    END AS program,
    f.processing_days
  FROM fact_permit f
  JOIN dim_permit_type pt ON f.permit_type_key = pt.permit_type_key
  JOIN dim_date d         ON f.issue_date_key  = d.date_key
  WHERE f.processing_days IS NOT NULL
),
ranked AS (
  SELECT
    issue_year,
    program,
    processing_days,
    ROW_NUMBER() OVER (PARTITION BY issue_year, program ORDER BY processing_days) AS rn,
    COUNT(*)     OVER (PARTITION BY issue_year, program)                          AS n
  FROM base
),
yearly AS (
  SELECT
    issue_year,
    program,
    MAX(n) AS permits,
    AVG(CASE WHEN rn IN (FLOOR((n + 1) / 2), CEIL((n + 1) / 2))
             THEN processing_days END) AS median_days
  FROM ranked
  GROUP BY issue_year, program
)
SELECT
  issue_year,
  program,
  permits,
  ROUND(median_days, 1) AS median_days,
  ROUND(median_days - LAG(median_days) OVER (PARTITION BY program ORDER BY issue_year), 1)
    AS change_vs_prior_year
FROM yearly
ORDER BY program, issue_year;

-- 1c. How common are same-day permits, and how slow is the slowest 10%?
WITH base AS (
  SELECT
    CASE
      WHEN pt.permit_type LIKE '%EXPRESS%' THEN 'Express'
      WHEN pt.permit_type LIKE '%EASY%'    THEN 'Easy'
      ELSE 'Standard'
    END AS program,
    f.processing_days
  FROM fact_permit f
  JOIN dim_permit_type pt ON f.permit_type_key = pt.permit_type_key
  WHERE f.processing_days IS NOT NULL
),
ranked AS (
  SELECT
    program,
    processing_days,
    ROW_NUMBER() OVER (PARTITION BY program ORDER BY processing_days) AS rn,
    COUNT(*)     OVER (PARTITION BY program)                          AS n
  FROM base
)
SELECT
  program,
  ROUND(100 * AVG(processing_days = 0), 1)                         AS pct_same_day,
  ROUND(100 * AVG(processing_days <= 7), 1)                        AS pct_within_week,
  MAX(CASE WHEN rn = CEIL(0.90 * n) THEN processing_days END)      AS p90_days
FROM ranked
GROUP BY program
ORDER BY p90_days;


-- 1d. Did standard permits slow down, or did the mix change?
-- Median days by permit type for standard permits, before and after the late-2023 system change.
WITH base AS (
  SELECT
    pt.permit_type,
    CASE WHEN d.year <= 2023 THEN '2021-2023' ELSE '2024-2026' END AS period,
    f.processing_days
  FROM fact_permit f
  JOIN dim_permit_type pt ON f.permit_type_key = pt.permit_type_key
  JOIN dim_date d         ON f.issue_date_key  = d.date_key
  WHERE f.processing_days IS NOT NULL
    AND d.year >= 2021
    AND pt.permit_type NOT LIKE '%EXPRESS%'
    AND pt.permit_type NOT LIKE '%EASY%'
),
ranked AS (
  SELECT
    permit_type,
    period,
    processing_days,
    ROW_NUMBER() OVER (PARTITION BY permit_type, period ORDER BY processing_days) AS rn,
    COUNT(*)     OVER (PARTITION BY permit_type, period)                          AS n
  FROM base
)
SELECT
  permit_type,
  period,
  MAX(n) AS permits,
  AVG(CASE WHEN rn IN (FLOOR((n + 1) / 2), CEIL((n + 1) / 2))
           THEN processing_days END) AS median_days
FROM ranked
GROUP BY permit_type, period
ORDER BY permit_type, period;

