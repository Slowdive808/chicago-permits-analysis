"""Export the summary tables behind the Tableau dashboard to CSV.

Tableau Public can't connect to MySQL, so this script runs the analysis queries
and saves their results to dashboards/data/. Rerun it after reloading the database.
"""
from pathlib import Path

import pandas as pd

from load_permits import ROOT, get_engine

OUT = ROOT / "dashboards/data"

QUERIES = {
    # Median processing days by program and year (from sql/01, query 1b)
    "processing_time_by_year": """
        WITH base AS (
          SELECT
            d.year AS issue_year,
            CASE
              WHEN pt.permit_type LIKE '%%EXPRESS%%' THEN 'Express'
              WHEN pt.permit_type LIKE '%%EASY%%'    THEN 'Easy'
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
            issue_year, program, processing_days,
            ROW_NUMBER() OVER (PARTITION BY issue_year, program ORDER BY processing_days) AS rn,
            COUNT(*)     OVER (PARTITION BY issue_year, program)                          AS n
          FROM base
        )
        SELECT
          issue_year,
          program,
          MAX(n) AS permits,
          AVG(CASE WHEN rn IN (FLOOR((n + 1) / 2), CEIL((n + 1) / 2))
                   THEN processing_days END) AS median_days
        FROM ranked
        GROUP BY issue_year, program
        ORDER BY program, issue_year
    """,
    # Citywide permits per full year (from sql/02, query 2a)
    "citywide_permits_by_year": """
        SELECT d.year, COUNT(*) AS permits
        FROM fact_permit f
        JOIN dim_date d ON f.issue_date_key = d.date_key
        WHERE d.year BETWEEN 2006 AND 2025
        GROUP BY d.year
        ORDER BY d.year
    """,
    # Change in permit activity by community area, for the map (from sql/02, query 2c)
    "community_area_change": """
        WITH yearly AS (
          SELECT f.community_area_key, d.year, COUNT(*) AS permits
          FROM fact_permit f
          JOIN dim_date d ON f.issue_date_key = d.date_key
          WHERE d.year BETWEEN 2015 AND 2025
            AND f.community_area_key IS NOT NULL
          GROUP BY f.community_area_key, d.year
        ),
        periods AS (
          SELECT
            community_area_key,
            AVG(CASE WHEN year BETWEEN 2015 AND 2017 THEN permits END) AS avg_2015_2017,
            AVG(CASE WHEN year BETWEEN 2023 AND 2025 THEN permits END) AS avg_2023_2025
          FROM yearly
          GROUP BY community_area_key
        ),
        city AS (
          SELECT 100 * (SUM(avg_2023_2025) - SUM(avg_2015_2017)) / SUM(avg_2015_2017) AS city_pct
          FROM periods
        )
        SELECT
          ca.community_area_key  AS area_number,
          ca.community_area_name AS area,
          ROUND(p.avg_2015_2017) AS avg_2015_2017,
          ROUND(p.avg_2023_2025) AS avg_2023_2025,
          ROUND(100 * (p.avg_2023_2025 - p.avg_2015_2017) / p.avg_2015_2017, 1) AS pct_change,
          ROUND(100 * (p.avg_2023_2025 - p.avg_2015_2017) / p.avg_2015_2017 - city.city_pct, 1)
            AS vs_city_pts
        FROM periods p
        JOIN dim_community_area ca ON p.community_area_key = ca.community_area_key
        CROSS JOIN city
        ORDER BY pct_change DESC
    """,
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    engine = get_engine()
    for name, sql in QUERIES.items():
        frame = pd.read_sql(sql, engine)
        path = OUT / f"{name}.csv"
        frame.to_csv(path, index=False)
        print(f"  {path.relative_to(ROOT)}: {len(frame):,} rows")


if __name__ == "__main__":
    main()
