-- Cost with known-bad values removed. See DATA_QUALITY.md for the reasoning.
-- Rerun this file after each load, since the load script rebuilds the tables.
CREATE OR REPLACE VIEW v_permit_cost AS
SELECT
  f.permit_id,
  CASE
    WHEN f.reported_cost IS NULL OR f.reported_cost <= 0 THEN NULL
    WHEN f.reported_cost >= 1000000000 THEN NULL
    WHEN (pt.permit_type LIKE '%EASY%' OR pt.permit_type LIKE '%EXPRESS%')
         AND f.reported_cost > 10000000 THEN NULL
    ELSE f.reported_cost
  END AS clean_cost
FROM fact_permit f
JOIN dim_permit_type pt ON f.permit_type_key = pt.permit_type_key;