"""
02_clean_stats19.py  --  Road Safety Risk & Operations Analytics

Principles (see cleaning_decisions.md):
  1. Don't lose valid rows because some fields are missing.
  2. Don't change the meaning of the data: original columns are kept,
     derived columns are ADDED next to them.
  3. Every decision is logged (cleaning_log.csv) and documented.

Inputs : the 3 raw STATS19 CSVs (collisions, vehicles, casualties)
Outputs: clean/collisions_clean.csv, vehicles_clean.csv, casualties_clean.csv
         clean/cleaning_log.csv   (what was changed and how many values)
"""
from pathlib import Path
import sys
import pandas as pd

# ----------------------------------------------------------------------
# 0. Paths
# ----------------------------------------------------------------------
DATA_DIR = Path(r"F:\Project\Road Safety Risk & Operations Analytics\data")
OUT_DIR = DATA_DIR.parent / "clean"
OUT_DIR.mkdir(exist_ok=True)

# NB: the casualty file name also contains "casualty-statistics-collision"
# style prefixes, so match on the part AFTER "statistics-".
PATTERNS = {
    "collisions": "*statistics-collision-*.csv",
    "vehicles": "*statistics-vehicle-*.csv",
    "casualties": "*statistics-casualty-*.csv",
}

# ----------------------------------------------------------------------
# 1. Columns to keep (only those needed for the analysis questions).
#    OPTIONAL columns are kept only if they exist in the file.
# ----------------------------------------------------------------------
KEEP = {
    "collisions": [
        "collision_index", "collision_year", "date", "day_of_week", "time",
        "longitude", "latitude", "police_force", "local_authority_ons_district",
        "road_type", "speed_limit", "light_conditions", "weather_conditions",
        "road_surface_conditions", "number_of_vehicles", "number_of_casualties",
        # severity: original + adjusted/injury-based (final choice pending the data guide)
        "collision_severity", "enhanced_severity_collision", "collision_injury_based",
        "collision_adjusted_severity_serious", "collision_adjusted_severity_slight",
    ],
    "vehicles": [
        "collision_index", "collision_year", "vehicle_reference", "vehicle_type",
        "sex_of_driver", "age_band_of_driver",
    ],
    "casualties": [
        "collision_index", "collision_year", "vehicle_reference", "casualty_reference",
        "casualty_class", "sex_of_casualty", "age_band_of_casualty", "casualty_type",
        "casualty_severity", "enhanced_casualty_severity", "casualty_injury_based",
        "casualty_adjusted_severity_serious", "casualty_adjusted_severity_slight",
    ],
}
REQUIRED_KEYS = {
    "collisions": ["collision_index"],
    "vehicles": ["collision_index", "vehicle_reference"],
    "casualties": ["collision_index", "casualty_reference"],
}

# ----------------------------------------------------------------------
# 2. Columns where -1 means "data missing / out of range" -> NULL.
#    (Verify each one against the STATS19 data guide before trusting it.)
#    Code 9 / 99 ("unknown" categories that are real codes in the guide)
#    are NOT touched here; map them to an "Unknown" label in the SQL
#    lookup tables instead.
#    Severity columns are deliberately NOT in this list.
# ----------------------------------------------------------------------
MINUS1_TO_NULL = {
    "collisions": ["speed_limit", "light_conditions", "weather_conditions",
                   "road_surface_conditions", "road_type"],
    "vehicles": ["vehicle_type", "sex_of_driver", "age_band_of_driver"],
    "casualties": ["casualty_class", "sex_of_casualty", "age_band_of_casualty",
                   "casualty_type"],
}

WEEKDAY = {1: "Sunday", 2: "Monday", 3: "Tuesday", 4: "Wednesday",
           5: "Thursday", 6: "Friday", 7: "Saturday"}

log_rows = []


def log(table, column, action, n):
    log_rows.append({"table": table, "column": column, "action": action, "count": int(n)})


def find_file(table):
    hits = sorted(DATA_DIR.glob(PATTERNS[table]))
    if len(hits) != 1:
        sys.exit(f"[{table}] expected exactly 1 file matching {PATTERNS[table]} "
                 f"in {DATA_DIR}, found {len(hits)}: {[h.name for h in hits]}")
    return hits[0]


def load(table):
    path = find_file(table)
    df = pd.read_csv(path, low_memory=False)
    log(table, "*", "rows_read", len(df))
    cols = [c for c in KEEP[table] if c in df.columns]
    missing = [c for c in KEEP[table] if c not in df.columns]
    if missing:
        print(f"[{table}] columns not found (skipped): {missing}")
        log(table, ",".join(missing), "columns_not_found_skipped", len(missing))
    dropped = len(df.columns) - len(cols)
    log(table, "*", "columns_dropped_not_needed", dropped)
    return df[cols].copy()


def minus1_to_null(df, table):
    for col in MINUS1_TO_NULL[table]:
        if col in df.columns:
            n = (df[col] == -1).sum()
            # nullable Int64 keeps codes as 30, not 30.0 (clean import into SQL Server)
            df[col] = df[col].where(df[col] != -1).astype("Int64")
            log(table, col, "minus1_to_null", n)
    return df


# ----------------------------------------------------------------------
# 3. Collisions
# ----------------------------------------------------------------------
def clean_collisions(df):
    df = minus1_to_null(df, "collisions")

    # dates: STATS19 uses dd/mm/yyyy. Keep the original `date` and `time`.
    d = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
    if d.isna().any():
        d = d.fillna(pd.to_datetime(df["date"], dayfirst=True, errors="coerce"))
    log("collisions", "date", "unparseable_dates", d.isna().sum())
    df["collision_date"] = d.dt.strftime("%Y-%m-%d")
    df["collision_month"] = d.dt.month
    year_mismatch = (d.dt.year != df["collision_year"]).sum()
    log("collisions", "date", "year_differs_from_collision_year", year_mismatch)

    t = pd.to_datetime(df["time"], format="%H:%M", errors="coerce")
    log("collisions", "time", "unparseable_times", t.isna().sum())
    df["collision_hour"] = t.dt.hour

    # weekday: derived from the date; compare with the original day_of_week.
    # STATS19: 1 = Sunday ... 7 = Saturday.
    wd = ((d.dt.dayofweek + 1) % 7) + 1
    log("collisions", "day_of_week", "differs_from_date_derived_weekday",
        (wd != df["day_of_week"]).sum())
    df["weekday_name"] = df["day_of_week"].map(WEEKDAY)

    # keep crashes without coordinates; flag them (exclude from the map only)
    has_xy = df["longitude"].notna() & df["latitude"].notna()
    df["has_coordinates"] = has_xy.astype(int)
    log("collisions", "longitude/latitude", "rows_without_coordinates_kept", (~has_xy).sum())
    return df


# ----------------------------------------------------------------------
# 4. Checks + export
# ----------------------------------------------------------------------
def check_keys(df, table):
    keys = REQUIRED_KEYS[table]
    assert df[keys].notna().all().all(), f"[{table}] null in key {keys}"
    dups = df.duplicated(keys).sum()
    assert dups == 0, f"[{table}] {dups} duplicate keys {keys}"


def export(df, table):
    path = OUT_DIR / f"{table}_clean.csv"
    # empty string = NULL (use KEEPNULLS in BULK INSERT / the import wizard)
    df.to_csv(path, index=False, encoding="utf-8", na_rep="")
    log(table, "*", "rows_written", len(df))
    print(f"[{table}] {len(df):,} rows x {df.shape[1]} cols -> {path}")


def main():
    col = clean_collisions(load("collisions"))
    veh = minus1_to_null(load("vehicles"), "vehicles")
    cas = minus1_to_null(load("casualties"), "casualties")

    for df, name in ((col, "collisions"), (veh, "vehicles"), (cas, "casualties")):
        check_keys(df, name)

    # referential integrity must survive the cleaning
    assert veh["collision_index"].isin(col["collision_index"]).all(), "orphan vehicles"
    assert cas["collision_index"].isin(col["collision_index"]).all(), "orphan casualties"

    export(col, "collisions")
    export(veh, "vehicles")
    export(cas, "casualties")

    pd.DataFrame(log_rows).to_csv(OUT_DIR / "cleaning_log.csv", index=False)
    print(f"log -> {OUT_DIR / 'cleaning_log.csv'}")


if __name__ == "__main__":
    main()