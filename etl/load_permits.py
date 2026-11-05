"""Load the Chicago building permits CSV into the MySQL star schema."""
from pathlib import Path

import pandas as pd
from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data/raw/building_permits.csv"
AREAS_CSV = ROOT / "data/raw/community_areas.csv"
SCHEMA = ROOT / "db/schema.sql"
CHUNK = 10_000


def get_engine():
    env = dotenv_values(ROOT / ".env")
    url = URL.create(
        "mysql+pymysql",
        username="root",
        password=env["MYSQL_ROOT_PASSWORD"],
        host="127.0.0.1",
        port=3306,
        database=env["MYSQL_DATABASE"],
    )
    return create_engine(url)


def rebuild_schema(engine):
    with engine.begin() as conn:
        for stmt in SCHEMA.read_text().split(";"):
            if stmt.strip():
                conn.exec_driver_sql(stmt)


def load(frame, table, engine):
    frame.to_sql(table, engine, if_exists="append", index=False,
                 chunksize=CHUNK, method="multi")
    print(f"  {table}: {len(frame):,} rows")


def load_dim(source, cols, table, key, engine):
    """Insert the distinct values, then return each source row's new key."""
    renamed = source[list(cols)].rename(columns=cols)
    load(renamed.drop_duplicates(), table, engine)
    keys = pd.read_sql(f"SELECT * FROM {table}", engine)
    return renamed.merge(keys, on=list(cols.values()), how="left")[key].to_numpy()


def money(s):
    return pd.to_numeric(s.str.replace(r"[$,]", "", regex=True), errors="coerce")


def whole_number(s):
    return pd.to_numeric(s, errors="coerce").round().astype("Int64")


def date_key(d):
    return (d.dt.year * 10000 + d.dt.month * 100 + d.dt.day).astype("Int64")


def clean_text(s):
    return s.str.strip().str.upper().str.replace(r"\s+", " ", regex=True)


def main():
    engine = get_engine()
    issues = {}

    print("Reading CSV...")
    df = pd.read_csv(CSV, dtype=str, low_memory=False)

    print("Rebuilding schema...")
    rebuild_schema(engine)
    print("Loading tables...")

    # dim_date: every day from the earliest to the latest date in the data
    app = pd.to_datetime(df["APPLICATION_START_DATE"], format="%m/%d/%Y", errors="coerce")
    iss = pd.to_datetime(df["ISSUE_DATE"], format="%m/%d/%Y", errors="coerce")
    issues["missing application date"] = int(app.isna().sum())
    days = pd.Series(pd.date_range(min(app.min(), iss.min()),
                                   max(app.max(), iss.max()), freq="D"))
    load(pd.DataFrame({
        "date_key": date_key(days),
        "full_date": days.dt.date,
        "year": days.dt.year,
        "quarter": days.dt.quarter,
        "month": days.dt.month,
        "month_name": days.dt.month_name(),
        "day_of_week": days.dt.day_of_week + 1,
        "day_name": days.dt.day_name(),
        "is_weekend": days.dt.day_of_week >= 5,
    }), "dim_date", engine)

    # dim_permit_type and dim_status
    for col in ["PERMIT_TYPE", "REVIEW_TYPE", "WORK_TYPE",
                "PERMIT_STATUS", "PERMIT_MILESTONE"]:
        df[col] = clean_text(df[col]).fillna("UNKNOWN")
    permit_type_key = load_dim(
        df, {"PERMIT_TYPE": "permit_type", "REVIEW_TYPE": "review_type",
             "WORK_TYPE": "work_type"},
        "dim_permit_type", "permit_type_key", engine)
    status_key = load_dim(
        df, {"PERMIT_STATUS": "permit_status", "PERMIT_MILESTONE": "permit_milestone"},
        "dim_status", "status_key", engine)

    # dim_community_area: numbers and names from the city's boundaries file
    community_area = whole_number(df["COMMUNITY_AREA"])
    valid_area = community_area.between(1, 77).fillna(False)
    issues["community area outside 1-77 (set to NULL)"] = int(
        (community_area.notna() & ~valid_area).sum())
    community_area = community_area.where(valid_area)
    areas = pd.read_csv(AREAS_CSV, usecols=["AREA_NUMBE", "COMMUNITY"])
    load(pd.DataFrame({
        "community_area_key": areas["AREA_NUMBE"].astype(int),
        "community_area_name": areas["COMMUNITY"].str.strip(),
    }).sort_values("community_area_key"), "dim_community_area", engine)

    # fact_permit
    processing = whole_number(df["PROCESSING_TIME"].str.replace(",", ""))
    negative = (processing < 0).fillna(False)
    issues["negative processing time (set to NULL)"] = int(negative.sum())
    processing = processing.mask(negative)

    paid_parts = (money(df["BUILDING_FEE_PAID"]) + money(df["ZONING_FEE_PAID"])
                  + money(df["OTHER_FEE_PAID"]))
    issues["paid fees that don't add up to SUBTOTAL_PAID"] = int(
        ((paid_parts - money(df["SUBTOTAL_PAID"])).abs() > 0.01).sum())

    cost = money(df["REPORTED_COST"])
    issues["reported cost missing"] = int(cost.isna().sum())
    issues["reported cost $0"] = int((cost == 0).sum())
    issues["reported cost negative"] = int((cost < 0).sum())
    issues["reported cost over $1B"] = int((cost > 1e9).sum())

    load(pd.DataFrame({
        "permit_id": df["ID"],
        "permit_number": df["PERMIT#"],
        "permit_type_key": permit_type_key,
        "status_key": status_key,
        "community_area_key": community_area,
        "application_date_key": date_key(app),
        "issue_date_key": date_key(iss),
        "processing_days": processing,
        "reported_cost": cost,
        "building_fee_paid": money(df["BUILDING_FEE_PAID"]).fillna(0),
        "zoning_fee_paid": money(df["ZONING_FEE_PAID"]).fillna(0),
        "other_fee_paid": money(df["OTHER_FEE_PAID"]).fillna(0),
        "total_fee_unpaid": money(df["SUBTOTAL_UNPAID"]).fillna(0),
        "total_fee_waived": money(df["SUBTOTAL_WAIVED"]).fillna(0),
        "total_fee": money(df["TOTAL_FEE"]).fillna(0),
        "residential_unit_change": whole_number(df["RESIDENTIAL_UNIT_CHANGE"]),
        "ward": whole_number(df["WARD"]),
        "census_tract": whole_number(df["CENSUS_TRACT"]),
        "street_number": whole_number(df["STREET_NUMBER"]),
        "street_direction": df["STREET_DIRECTION"].str.strip(),
        "street_name": clean_text(df["STREET_NAME"]),
        "latitude": pd.to_numeric(df["LATITUDE"], errors="coerce"),
        "longitude": pd.to_numeric(df["LONGITUDE"], errors="coerce"),
        "work_description": df["WORK_DESCRIPTION"],
        "permit_condition": df["PERMIT_CONDITION"],
    }), "fact_permit", engine)

    # Contacts: unpivot the 15 slots into one long table
    names = ["permit_id", "contact_type", "contact_name", "city", "state", "zip"]
    frames = []
    for i in range(1, 16):
        part = df[["ID", f"CONTACT_{i}_TYPE", f"CONTACT_{i}_NAME", f"CONTACT_{i}_CITY",
                   f"CONTACT_{i}_STATE", f"CONTACT_{i}_ZIPCODE"]].set_axis(names, axis=1)
        frames.append(part.dropna(subset=["contact_name"]))
    contacts = pd.concat(frames, ignore_index=True)

    contacts["contact_type"] = clean_text(contacts["contact_type"]).fillna("UNKNOWN")
    is_owner = contacts["contact_type"].str.contains("OWNER")
    issues["owner contacts skipped (privacy)"] = int(is_owner.sum())
    contacts = contacts[~is_owner].copy()

    name = clean_text(contacts["contact_name"])
    license_prefix = r"^[A-Z]{1,3}\d{6,}-"
    issues["license numbers stripped from names"] = int(
        name.str.contains(license_prefix, na=False).sum())
    contacts["contact_name"] = name.str.replace(license_prefix, "", regex=True)

    contacts["city"] = clean_text(contacts["city"]).fillna("")
    state = clean_text(contacts["state"]).replace({"ILL": "IL"})
    contacts["state"] = state.where(state.str.fullmatch(r"[A-Z]{2}", na=False), "")
    contacts["zip5"] = contacts["zip"].str.extract(r"^(\d{5})", expand=False).fillna("")
    contacts = contacts[contacts["contact_name"].str.len() > 0]

    contacts["contact_key"] = load_dim(
        contacts, {"contact_name": "contact_name", "city": "city",
                   "state": "state", "zip5": "zip5"},
        "dim_contact", "contact_key", engine)

    bridge = contacts[["permit_id", "contact_key", "contact_type"]].drop_duplicates()
    issues["duplicate contact entries removed"] = len(contacts) - len(bridge)
    load(bridge, "bridge_permit_contact", engine)

    print("\nData quality summary:")
    for label, count in issues.items():
        print(f"  {label}: {count:,}")


if __name__ == "__main__":
    main()