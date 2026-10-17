/* =====================================================================
   03_mysql_setup.sql  --  Road Safety Risk & Operations Analytics
   MySQL 8.0+ (needed later for CTEs and window functions).
   Loads the 3 cleaned CSVs from the Python step.

   BEFORE RUNNING (LOAD DATA LOCAL needs two switches):
   1) Server side (run once, needs admin):   SET GLOBAL local_infile = 1;
   2) Workbench side: Database > Manage Connections > select your
      connection > Advanced tab > "Others" box, add:   OPT_LOCAL_INFILE=1
      then reconnect.
   If you see "Error 3948 / Loading local data is disabled", one of the two
   is missing.
   ===================================================================== */

CREATE DATABASE IF NOT EXISTS road_safety
    CHARACTER SET utf8mb4;
USE road_safety;

SET GLOBAL local_infile = 1;

/* ---------------------------------------------------------------------
   1. Re-runnable: drop children first
   --------------------------------------------------------------------- */
DROP TABLE IF EXISTS casualties;
DROP TABLE IF EXISTS vehicles;
DROP TABLE IF EXISTS collisions;

/* ---------------------------------------------------------------------
   2. Tables. Column ORDER = CSV column order.
      NULL = value was -1 (missing) in the source for the cleaned columns.
      collision_index uses ascii_bin so keys are compared exactly.
   --------------------------------------------------------------------- */
CREATE TABLE collisions (
    collision_index                      VARCHAR(20) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    collision_year                       SMALLINT     NOT NULL,
    `date`                               VARCHAR(10)  NULL,   -- original dd/mm/yyyy
    day_of_week                          TINYINT      NULL,   -- 1=Sunday ... 7=Saturday
    `time`                               VARCHAR(5)   NULL,   -- original HH:MM
    longitude                            DOUBLE       NULL,
    latitude                             DOUBLE       NULL,
    police_force                         SMALLINT     NULL,
    local_authority_ons_district         VARCHAR(12)  NULL,
    road_type                            SMALLINT     NULL,
    speed_limit                          SMALLINT     NULL,
    light_conditions                     SMALLINT     NULL,
    weather_conditions                   SMALLINT     NULL,
    road_surface_conditions              SMALLINT     NULL,
    number_of_vehicles                   SMALLINT     NULL,
    number_of_casualties                 SMALLINT     NULL,
    collision_severity                   SMALLINT     NOT NULL, -- 1 Fatal, 2 Serious, 3 Slight
    enhanced_severity_collision          SMALLINT     NULL,     -- kept raw, -1 NOT converted
    collision_injury_based               SMALLINT     NULL,
    collision_adjusted_severity_serious  DOUBLE       NULL,
    collision_adjusted_severity_slight   DOUBLE       NULL,
    collision_date                       DATE         NULL,     -- derived
    collision_month                      TINYINT      NULL,     -- derived
    collision_hour                       TINYINT      NULL,     -- derived
    weekday_name                         VARCHAR(10)  NULL,     -- derived
    has_coordinates                      TINYINT(1)   NOT NULL  -- derived
) ENGINE = InnoDB;

CREATE TABLE vehicles (
    collision_index     VARCHAR(20) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    collision_year      SMALLINT NOT NULL,
    vehicle_reference   INT      NOT NULL,
    vehicle_type        SMALLINT NULL,
    sex_of_driver       SMALLINT NULL,
    age_band_of_driver  SMALLINT NULL
) ENGINE = InnoDB;

CREATE TABLE casualties (
    collision_index                     VARCHAR(20) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    collision_year                      SMALLINT NOT NULL,
    vehicle_reference                   INT      NULL,
    casualty_reference                  INT      NOT NULL,
    casualty_class                      SMALLINT NULL,
    sex_of_casualty                     SMALLINT NULL,
    age_band_of_casualty                SMALLINT NULL,
    casualty_type                       SMALLINT NULL,
    casualty_severity                   SMALLINT NOT NULL,
    enhanced_casualty_severity          SMALLINT NULL,          -- kept raw
    casualty_injury_based               SMALLINT NULL,
    casualty_adjusted_severity_serious  DOUBLE   NULL,
    casualty_adjusted_severity_slight   DOUBLE   NULL
) ENGINE = InnoDB;

/* ---------------------------------------------------------------------
   3. Load. In LOAD DATA an empty field becomes 0 for numbers, NOT NULL,
      so nullable columns go through @variables + NULLIF(@v, '').
      Paths use forward slashes. Edit them if your folder is different.
      If the load reports 0 rows or one giant row, change '\r\n' to '\n'.
   --------------------------------------------------------------------- */
LOAD DATA LOCAL INFILE 'F:/Project/Road Safety Risk & Operations Analytics/clean/collisions_clean.csv'
INTO TABLE collisions
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(collision_index, collision_year, @date, @day_of_week, @time, @longitude, @latitude,
 @police_force, @la_ons, @road_type, @speed_limit, @light, @weather, @surface,
 @n_veh, @n_cas, collision_severity, @enh_sev, @inj_based, @adj_serious, @adj_slight,
 @c_date, @c_month, @c_hour, @weekday_name, has_coordinates)
SET `date`                               = NULLIF(@date, ''),
    day_of_week                          = NULLIF(@day_of_week, ''),
    `time`                               = NULLIF(@time, ''),
    longitude                            = NULLIF(@longitude, ''),
    latitude                             = NULLIF(@latitude, ''),
    police_force                         = NULLIF(@police_force, ''),
    local_authority_ons_district         = NULLIF(@la_ons, ''),
    road_type                            = NULLIF(@road_type, ''),
    speed_limit                          = NULLIF(@speed_limit, ''),
    light_conditions                     = NULLIF(@light, ''),
    weather_conditions                   = NULLIF(@weather, ''),
    road_surface_conditions              = NULLIF(@surface, ''),
    number_of_vehicles                   = NULLIF(@n_veh, ''),
    number_of_casualties                 = NULLIF(@n_cas, ''),
    enhanced_severity_collision          = NULLIF(@enh_sev, ''),
    collision_injury_based               = NULLIF(@inj_based, ''),
    collision_adjusted_severity_serious  = NULLIF(@adj_serious, ''),
    collision_adjusted_severity_slight   = NULLIF(@adj_slight, ''),
    collision_date                       = NULLIF(@c_date, ''),
    collision_month                      = NULLIF(@c_month, ''),
    collision_hour                       = NULLIF(@c_hour, ''),
    weekday_name                         = NULLIF(@weekday_name, '');
SHOW WARNINGS LIMIT 5;

LOAD DATA LOCAL INFILE 'F:/Project/Road Safety Risk & Operations Analytics/clean/vehicles_clean.csv'
INTO TABLE vehicles
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(collision_index, collision_year, vehicle_reference, @vehicle_type, @sex, @age_band)
SET vehicle_type       = NULLIF(@vehicle_type, ''),
    sex_of_driver      = NULLIF(@sex, ''),
    age_band_of_driver = NULLIF(@age_band, '');
SHOW WARNINGS LIMIT 5;

LOAD DATA LOCAL INFILE 'F:/Project/Road Safety Risk & Operations Analytics/clean/casualties_clean.csv'
INTO TABLE casualties
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(collision_index, collision_year, @veh_ref, casualty_reference, @class, @sex, @age_band,
 @type, casualty_severity, @enh_sev, @inj_based, @adj_serious, @adj_slight)
SET vehicle_reference                   = NULLIF(@veh_ref, ''),
    casualty_class                      = NULLIF(@class, ''),
    sex_of_casualty                     = NULLIF(@sex, ''),
    age_band_of_casualty                = NULLIF(@age_band, ''),
    casualty_type                       = NULLIF(@type, ''),
    enhanced_casualty_severity          = NULLIF(@enh_sev, ''),
    casualty_injury_based               = NULLIF(@inj_based, ''),
    casualty_adjusted_severity_serious  = NULLIF(@adj_serious, ''),
    casualty_adjusted_severity_slight   = NULLIF(@adj_slight, '');
SHOW WARNINGS LIMIT 5;

/* ---------------------------------------------------------------------
   4. Row counts must match the Python quality report
   --------------------------------------------------------------------- */
SELECT 'collisions' AS tbl, COUNT(*) AS n, 513801 AS expected FROM collisions
UNION ALL SELECT 'vehicles',   COUNT(*), 937265 FROM vehicles
UNION ALL SELECT 'casualties', COUNT(*), 652821 FROM casualties;

/* ---------------------------------------------------------------------
   5. Keys and indexes (added after the load: faster, and a violation
      shows up as a clear error)
   --------------------------------------------------------------------- */
ALTER TABLE collisions ADD PRIMARY KEY (collision_index);
ALTER TABLE vehicles   ADD PRIMARY KEY (collision_index, vehicle_reference);
ALTER TABLE casualties ADD PRIMARY KEY (collision_index, casualty_reference);

ALTER TABLE vehicles
    ADD CONSTRAINT fk_vehicles_collisions
    FOREIGN KEY (collision_index) REFERENCES collisions (collision_index);
ALTER TABLE casualties
    ADD CONSTRAINT fk_casualties_collisions
    FOREIGN KEY (collision_index) REFERENCES collisions (collision_index);

-- indexes for the analysis questions (where / when / conditions / who)
CREATE INDEX ix_collisions_year_sev  ON collisions (collision_year, collision_severity);
CREATE INDEX ix_collisions_area      ON collisions (local_authority_ons_district, collision_severity);
CREATE INDEX ix_collisions_hour_dow  ON collisions (collision_hour, day_of_week);
CREATE INDEX ix_casualties_class_type ON casualties (casualty_class, casualty_type, casualty_severity);
CREATE INDEX ix_vehicles_type        ON vehicles (vehicle_type);

/* ---------------------------------------------------------------------
   6. Sanity checks
   --------------------------------------------------------------------- */
SELECT COUNT(*) AS collisions_without_vehicles
FROM collisions c WHERE NOT EXISTS (SELECT 1 FROM vehicles v WHERE v.collision_index = c.collision_index);

SELECT COUNT(*) AS collisions_without_casualties
FROM collisions c WHERE NOT EXISTS (SELECT 1 FROM casualties k WHERE k.collision_index = c.collision_index);

SELECT COUNT(*) AS date_year_mismatch
FROM collisions WHERE YEAR(collision_date) <> collision_year;

SELECT COUNT(*) AS rows_without_coordinates_expected_53
FROM collisions WHERE has_coordinates = 0;

-- Severity by year: compare with section 6 of quality_report.txt
SELECT collision_year, collision_severity, COUNT(*) AS n
FROM collisions
GROUP BY collision_year, collision_severity
ORDER BY collision_year, collision_severity;
