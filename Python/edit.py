"""
Road Safety Risk & Operations Analytics
Step 1: Data quality check for STATS19 (Collisions / Vehicles / Casualties), 2021-2025

How to use:
  1. Put all CSV files (per-year or combined) inside the DATA_DIR folder (sub-folders are fine).
  2. Run:  python 01_data_quality_check.py
  3. Read the console output or quality_report/quality_report.txt
     and quality_report/missing_values.csv

Requires: pandas  (pip install pandas)
"""

from pathlib import Path
import pandas as pd

# ----------------------------- Settings -----------------------------
BASE_DIR = Path(__file__).resolve().parent
# CSVs are searched in the script's own folder and all sub-folders.
# If your CSVs are elsewhere, replace with e.g. Path(r"F:\Project\...\data")
DATA_DIR = BASE_DIR
OUT_DIR = BASE_DIR / "quality_report"   # report output folder
YEARS = list(range(2021, 2026))    # 2021 to 2025

# file-name keyword -> table name (order matters: the collision file name
# also contains the word "casualty", so casualties are checked last)
KEYWORDS = [("collision", "collisions"), ("vehicle", "vehicles"), ("casualty", "casualties")]

UK_LAT = (49.5, 61.0)
UK_LON = (-8.7, 2.0)

# ----------------------------- Helpers -----------------------------
OUT_DIR.mkdir(exist_ok=True)
_lines = []


def log(text=""):
    print(text)
    _lines.append(str(text))


def title(text):
    log("\n" + "=" * 70)
    log(text)
    log("=" * 70)


def classify(path):
    name = path.name.lower()
    for kw, table in KEYWORDS:
        if kw in name:
            return table
    return None


def load_tables():
    files = {"collisions": [], "vehicles": [], "casualties": []}
    log(f"    searching in: {DATA_DIR}")
    all_csv = [p for p in sorted(DATA_DIR.rglob("*.csv")) if OUT_DIR not in p.parents]
    log(f"    CSV files found: {len(all_csv)}")
    for p in all_csv:
        table = classify(p)
        if table:
            files[table].append(p)
        else:
            log(f"[!] Ignored (name has no collision/vehicle/casualty): {p.name}")

    tables = {}
    for table, paths in files.items():
        if not paths:
            log(f"[!] No CSV files found for: {table}")
            continue
        parts = []
        for p in paths:
            log(f"    reading {table}: {p.name}")
            df = pd.read_csv(
                p,
                low_memory=False,
                dtype={"collision_index": str, "collision_ref_no": str},
            )
            df["source_file"] = p.name
            parts.append(df)
        df = pd.concat(parts, ignore_index=True)
        if "collision_year" in df.columns:
            df["collision_year"] = pd.to_numeric(df["collision_year"], errors="coerce")
            df = df[df["collision_year"].isin(YEARS)].copy()
        tables[table] = df
    return tables


# ----------------------------- Checks -----------------------------
def check_overview(tables):
    title("1. OVERVIEW: rows, columns, rows per year")
    for name, df in tables.items():
        log(f"\n{name}: {len(df):,} rows x {df.shape[1]} columns")
        if "collision_year" in df.columns:
            log(df["collision_year"].value_counts().sort_index().to_string())
        files = df["source_file"].nunique()
        if files > 1:
            log(f"(combined from {files} files: check there is no overlap between files)")


def check_keys(tables):
    title("2. KEY UNIQUENESS (duplicates)")
    keys = {
        "collisions": ["collision_index"],
        "vehicles": ["collision_index", "vehicle_reference"],
        "casualties": ["collision_index", "casualty_reference"],
    }
    for name, key in keys.items():
        if name not in tables:
            continue
        df = tables[name]
        dups = df.duplicated(subset=key, keep=False).sum()
        log(f"{name:11s} key={key} -> duplicate rows: {dups:,}")


def check_orphans(tables):
    title("3. ORPHANS and COUNT CONSISTENCY")
    if not {"collisions", "vehicles", "casualties"} <= tables.keys():
        log("Skipped: one of the three tables is missing.")
        return
    c, v, k = tables["collisions"], tables["vehicles"], tables["casualties"]
    ids = set(c["collision_index"])

    log(f"Vehicles without a matching collision:   {(~v['collision_index'].isin(ids)).sum():,}")
    log(f"Casualties without a matching collision: {(~k['collision_index'].isin(ids)).sum():,}")
    log(f"Collisions with no vehicle rows:         {(~c['collision_index'].isin(set(v['collision_index']))).sum():,}")
    log(f"Collisions with no casualty rows:        {(~c['collision_index'].isin(set(k['collision_index']))).sum():,}")

    vkeys = set(zip(v["collision_index"], v["vehicle_reference"]))
    kkeys = list(zip(k["collision_index"], k["vehicle_reference"]))
    miss = sum(1 for x in kkeys if x not in vkeys)
    log(f"Casualties whose (collision, vehicle_reference) is not in Vehicles: {miss:,}")
    log("   (note: some mismatch can be legitimate, e.g. pedestrians; review a sample)")

    vc = v.groupby("collision_index").size().rename("veh_count")
    kc = k.groupby("collision_index").size().rename("cas_count")
    m = c[["collision_index", "number_of_vehicles", "number_of_casualties"]].merge(
        vc, on="collision_index", how="left").merge(kc, on="collision_index", how="left")
    m[["veh_count", "cas_count"]] = m[["veh_count", "cas_count"]].fillna(0)
    log(f"number_of_vehicles != rows in Vehicles:    {(m['number_of_vehicles'] != m['veh_count']).sum():,}")
    log(f"number_of_casualties != rows in Casualties: {(m['number_of_casualties'] != m['cas_count']).sum():,}")
    log("   (note: differences are NOT automatically errors; review samples, recording rules,")
    log("    join keys and possible overlap between files before judging)")


def check_missing(tables):
    title("4. MISSING VALUES: NULL and -1 (unknown) per column")
    rows = []
    for name, df in tables.items():
        n = len(df)
        for col in df.columns:
            if col == "source_file":
                continue
            s = df[col]
            nulls = int(s.isna().sum())
            minus1 = int((pd.to_numeric(s, errors="coerce") == -1).sum())
            rows.append((name, col, nulls, round(nulls / n * 100, 2), minus1, round(minus1 / n * 100, 2)))
    rep = pd.DataFrame(rows, columns=["table", "column", "null_count", "null_pct", "minus1_count", "minus1_pct"])
    rep.to_csv(OUT_DIR / "missing_values.csv", index=False)
    bad = rep[(rep.null_pct > 0) | (rep.minus1_pct > 0)].copy()
    bad["worst_pct"] = bad[["null_pct", "minus1_pct"]].max(axis=1)
    log("Note: -1 is only COUNTED here. Its meaning differs per column, so check the")
    log("STATS19 data guide before deciding how to treat it.")
    log("Top 25 columns by missing/unknown share (full list in missing_values.csv):")
    log(bad.sort_values("worst_pct", ascending=False).head(25).drop(columns="worst_pct").to_string(index=False))

    log("\nColumns planned for the analysis:")
    focus = ["latitude", "longitude", "date", "time", "collision_severity", "light_conditions",
             "weather_conditions", "road_surface_conditions", "road_type", "speed_limit",
             "police_force", "local_authority_ons_district", "vehicle_type", "casualty_type",
             "casualty_severity", "casualty_class", "age_band_of_casualty"]
    log(rep[rep.column.isin(focus)].to_string(index=False))


def check_location_and_time(tables):
    title("5. LOCATION and DATE/TIME VALIDITY (Collisions)")
    if "collisions" not in tables:
        return
    c = tables["collisions"]

    lat = pd.to_numeric(c["latitude"], errors="coerce")
    lon = pd.to_numeric(c["longitude"], errors="coerce")
    outside = ~lat.between(*UK_LAT) | ~lon.between(*UK_LON)
    log(f"Missing coordinates:         {(lat.isna() | lon.isna()).sum():,}")
    log(f"Outside UK bounding box:     {(outside & lat.notna() & lon.notna()).sum():,}")

    date = pd.to_datetime(c["date"], format="%d/%m/%Y", errors="coerce")
    if date.isna().mean() > 0.5:
        date = pd.to_datetime(c["date"], dayfirst=True, errors="coerce")
    log(f"Unparseable dates:           {date.isna().sum():,}")
    year_mismatch = (
        date.notna()
        & c["collision_year"].notna()
        & date.dt.year.ne(c["collision_year"])
    )
    log(f"date year != collision_year: {year_mismatch.sum():,}")

    hour = pd.to_datetime(c["time"], format="%H:%M", errors="coerce").dt.hour
    log(f"Unparseable times:           {hour.isna().sum():,}")
    if hour.notna().any():
        log("\nCollisions per hour (sanity check, expect rush-hour peaks):")
        log(hour.value_counts().sort_index().to_string())

    dow = pd.to_numeric(c["day_of_week"], errors="coerce")
    log(f"\nday_of_week values: {sorted(dow.dropna().unique().tolist())}  (1=Sunday ... 7=Saturday)")


def check_severity(tables):
    title("6. SEVERITY DISTRIBUTION BY YEAR (1=Fatal, 2=Serious, 3=Slight)")
    if "collisions" in tables:
        c = tables["collisions"]
        log("\ncollision_severity:")
        log(pd.crosstab(c["collision_year"], c["collision_severity"]).to_string())
        adj = [x for x in c.columns if "adjusted" in x or x in ("enhanced_severity_collision", "collision_injury_based")]
        log(f"\nAdjusted / injury-based severity columns found: {adj}")
        for col in adj:
            log(f"\n{col} (by year):")
            log(pd.crosstab(c["collision_year"], c[col]).to_string())
        log("\n=> Before comparing years, read the data guide to decide which severity column to use.")
    if "casualties" in tables:
        k = tables["casualties"]
        log("\ncasualty_severity:")
        log(pd.crosstab(k["collision_year"], k["casualty_severity"]).to_string())


# ----------------------------- Main -----------------------------
if __name__ == "__main__":
    title("LOADING FILES")
    tables = load_tables()
    if not tables:
        raise SystemExit(f"No CSV files found in '{DATA_DIR}'. Check DATA_DIR.")

    check_overview(tables)
    check_keys(tables)
    check_orphans(tables)
    check_missing(tables)
    check_location_and_time(tables)
    check_severity(tables)

    (OUT_DIR / "quality_report.txt").write_text("\n".join(_lines), encoding="utf-8")
    log(f"\nDone. Report saved to: {OUT_DIR / 'quality_report.txt'}")