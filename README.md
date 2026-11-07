# Chicago Building Permits Analysis

An end-to-end analysis of every building permit issued by the City of Chicago since 2006:
852,143 permits loaded from a messy public CSV into a MySQL star schema, cleaned and
documented, and analyzed with SQL window functions.

The project covers the full path from raw data to findings: database design, an ETL
pipeline, data quality checks, and analysis. Every cleaning decision is logged in
[`DATA_QUALITY.md`](DATA_QUALITY.md), and the full write-up of results is in
[`FINDINGS.md`](FINDINGS.md).

## Key findings

**Chicago's fast-track permit programs work, but the system changed in late 2023.**
From 2006 to 2023, 87% of Easy permits and 55% of Express permits were issued the same day,
compared with 35% of standard permits. In late 2023 the city ended the Easy Permit program
and moved that work into Express. After the change, median processing times for standard
permits rose sharply within the same permit types (new construction from 3 to 52 days).
A 3-day median for new construction before 2024 is implausibly fast, which suggests part of
the increase may come from a change in how the application start date is recorded rather
than slower reviews.

**Permit activity fell 28% citywide, and the busiest neighborhoods fell hardest.**
Comparing 2015-2017 with 2023-2025, most South and Southwest Side areas held up better
than the city, and Ashburn (+34%) grew outright. Logan Square (-43%), West Town (-39%),
and the Loop (-37%) fell faster than the city overall.

**A handful of typos can reshape a ranking.** Rooftop solar permits listed at up to
$872 million pushed several neighborhoods into the top 10 by project value. Removing 91
implausible costs out of more than 530,000 fast-track permits removed six areas from the
top 20.

## Data model

The source CSV has 117 columns, including 15 repeated slots for contacts. It is loaded into
a star schema:

```
                 dim_date (application and issue dates)
                        |
dim_permit_type -- fact_permit -- dim_status
                        |
              dim_community_area
                        |
             bridge_permit_contact -- dim_contact
```

| Table | Rows | Contents |
|---|---|---|
| `fact_permit` | 852,143 | One row per permit: dates, processing time, cost, fees, location |
| `dim_date` | 9,525 | Calendar attributes for every date in the data |
| `dim_permit_type` | 40 | Permit type, review type, and work type |
| `dim_status` | 43 | Permit status and milestone |
| `dim_community_area` | 77 | Chicago's community areas, joined from a second city dataset |
| `dim_contact` | 60,441 | Deduplicated contractors, architects, and other professionals |
| `bridge_permit_contact` | 2,361,540 | Links permits to contacts with each contact's role |

A view, `v_permit_cost`, applies the cost cleaning rules in one place so every analysis
uses the same definition of a valid cost.

## Data quality highlights

The full log is in [`DATA_QUALITY.md`](DATA_QUALITY.md). Some examples:

- 81 permits were issued before their application date. Their processing times are set to NULL.
- Contacts were stored in 15 wide column slots. They were unpivoted into a bridge table,
  license numbers were stripped from 8,679 contractor names, and inconsistent states and zip
  codes were standardized.
- Fee components were checked against their stated subtotals (0 mismatches) before the
  redundant subtotal columns were dropped.
- 134 permits used community area `0` as a placeholder. These are stored as NULL.
- **Privacy:** 589,154 owner contacts were excluded, since many are private individuals.
  Only contractors, architects, and other professionals are stored.

## Repository layout

```
├── docker-compose.yml        MySQL 8.4 container
├── db/
│   ├── schema.sql            Star schema
│   └── views.sql             Cleaned cost view
├── etl/
│   └── load_permits.py       Reads the CSVs, cleans them, and loads every table
├── sql/
│   ├── 00_sanity_checks.sql  Checks run after loading
│   ├── 01_processing_time_by_program.sql
│   └── 02_community_area_trends.sql
├── notebooks/
│   └── analysis.ipynb        Exploration in pandas
├── DATA_QUALITY.md
└── FINDINGS.md
```

## Tools

MySQL 8.4 in Docker, Python (pandas, SQLAlchemy), SQL window functions (`ROW_NUMBER`,
`LAG`, `RANK`), DBeaver, and JupyterLab.

## Running it yourself

You need Docker Desktop and Python 3.12.

1. Clone the repo and set up the environment:
   ```bash
   git clone https://github.com/Slowdive808/chicago-permits-analysis.git
   cd chicago-permits-analysis
   cp .env.example .env          # then set your own password in .env
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start MySQL:
   ```bash
   docker compose up -d
   ```
3. Download the two source files as CSV from the Chicago Data Portal and save them in
   `data/raw/`:
   - [Building Permits](https://data.cityofchicago.org/d/ydr8-5enu) as `building_permits.csv`
   - [Boundaries - Community Areas](https://data.cityofchicago.org/d/igwz-8jzy) as `community_areas.csv`
4. Load the data (about 10 to 15 minutes), then create the view:
   ```bash
   python etl/load_permits.py
   docker exec -i permits-mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" permits' < db/views.sql
   ```
5. Run any file in `sql/` against the `permits` database.

The raw data is not included in this repo. Results reflect the data as downloaded on
November 4, 2026.

## Next steps

- Contractor analysis: the busiest contractors and how their share has changed
- Project cost by permit type, using the cleaned cost view
- A regression on what drives processing time
- Database administration: a read-only analyst user, tested backup and restore, and
  index tuning documented with before and after `EXPLAIN` output
- An interactive dashboard in Tableau Public

## Data source

City of Chicago Data Portal, [Building Permits](https://data.cityofchicago.org/d/ydr8-5enu)
and [Boundaries - Community Areas](https://data.cityofchicago.org/d/igwz-8jzy).
