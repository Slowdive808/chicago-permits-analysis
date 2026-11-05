DROP TABLE IF EXISTS bridge_permit_contact, fact_permit, dim_contact,
  dim_community_area, dim_status, dim_permit_type, dim_date;

CREATE TABLE dim_date (
  date_key     INT PRIMARY KEY,              -- YYYYMMDD, e.g. 20140121
  full_date    DATE NOT NULL UNIQUE,
  year         SMALLINT NOT NULL,
  quarter      TINYINT NOT NULL,
  month        TINYINT NOT NULL,
  month_name   VARCHAR(9) NOT NULL,
  day_of_week  TINYINT NOT NULL,             -- 1 = Monday
  day_name     VARCHAR(9) NOT NULL,
  is_weekend   BOOLEAN NOT NULL
);

CREATE TABLE dim_permit_type (
  permit_type_key  INT AUTO_INCREMENT PRIMARY KEY,
  permit_type      VARCHAR(100) NOT NULL,
  review_type      VARCHAR(100) NOT NULL,
  work_type        VARCHAR(100) NOT NULL DEFAULT 'UNKNOWN',
  UNIQUE KEY uq_permit_type (permit_type, review_type, work_type)
) COLLATE utf8mb4_bin;

CREATE TABLE dim_status (
  status_key        INT AUTO_INCREMENT PRIMARY KEY,
  permit_status     VARCHAR(50)  NOT NULL DEFAULT 'UNKNOWN',
  permit_milestone  VARCHAR(200) NOT NULL DEFAULT 'UNKNOWN',
  UNIQUE KEY uq_status (permit_status, permit_milestone)
) COLLATE utf8mb4_bin;

CREATE TABLE dim_community_area (
  community_area_key   SMALLINT UNSIGNED PRIMARY KEY,   -- city's 1-77 numbering
  community_area_name  VARCHAR(50) NULL
);

CREATE TABLE dim_contact (
  contact_key   INT AUTO_INCREMENT PRIMARY KEY,
  contact_name  VARCHAR(255) NOT NULL,
  city          VARCHAR(100) NOT NULL DEFAULT '',
  state         CHAR(2)      NOT NULL DEFAULT '',
  zip5          CHAR(5)      NOT NULL DEFAULT '',
  UNIQUE KEY uq_contact (contact_name, city, state, zip5)
) COLLATE utf8mb4_bin;

CREATE TABLE fact_permit (
  permit_id                VARCHAR(20) PRIMARY KEY,   -- source ID column
  permit_number            VARCHAR(20) NOT NULL,
  permit_type_key          INT NOT NULL,
  status_key               INT NOT NULL,
  community_area_key       SMALLINT UNSIGNED NULL,
  application_date_key     INT NULL,
  issue_date_key           INT NOT NULL,
  processing_days          INT NULL,
  reported_cost            DECIMAL(14,2) NULL,
  building_fee_paid        DECIMAL(12,2) NOT NULL DEFAULT 0,
  zoning_fee_paid          DECIMAL(12,2) NOT NULL DEFAULT 0,
  other_fee_paid           DECIMAL(12,2) NOT NULL DEFAULT 0,
  total_fee_unpaid         DECIMAL(12,2) NOT NULL DEFAULT 0,
  total_fee_waived         DECIMAL(12,2) NOT NULL DEFAULT 0,
  total_fee                DECIMAL(12,2) NOT NULL DEFAULT 0,
  residential_unit_change  INT NULL,
  ward                     TINYINT UNSIGNED NULL,
  census_tract             INT UNSIGNED NULL,
  street_number            INT UNSIGNED NULL,
  street_direction         VARCHAR(2) NULL,
  street_name              VARCHAR(100) NULL,
  latitude                 DECIMAL(9,6) NULL,
  longitude                DECIMAL(9,6) NULL,
  work_description         TEXT NULL,
  permit_condition         TEXT NULL,
  FOREIGN KEY (permit_type_key)      REFERENCES dim_permit_type (permit_type_key),
  FOREIGN KEY (status_key)           REFERENCES dim_status (status_key),
  FOREIGN KEY (community_area_key)   REFERENCES dim_community_area (community_area_key),
  FOREIGN KEY (application_date_key) REFERENCES dim_date (date_key),
  FOREIGN KEY (issue_date_key)       REFERENCES dim_date (date_key)
);

CREATE TABLE bridge_permit_contact (
  permit_id     VARCHAR(20)  NOT NULL,
  contact_key   INT          NOT NULL,
  contact_type  VARCHAR(100) NOT NULL,
  PRIMARY KEY (permit_id, contact_key, contact_type),
  FOREIGN KEY (permit_id)   REFERENCES fact_permit (permit_id),
  FOREIGN KEY (contact_key) REFERENCES dim_contact (contact_key)
);