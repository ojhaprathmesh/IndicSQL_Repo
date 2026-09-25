-- DDL Specification: ndap_crop_production_census
-- Domain: Agriculture
-- District-wise crop acreage, production yield, and seasonal harvest volumes.
CREATE TABLE IF NOT EXISTS ndap_crop_production_census (
    state_name VARCHAR,
    district_name VARCHAR,
    crop_year INTEGER,
    crop_name VARCHAR,
    season VARCHAR,
    area_hectares DOUBLE,
    production_tonnes DOUBLE,
    yield_kg_per_hectare DOUBLE,
    PRIMARY KEY (state_name, district_name, crop_year, crop_name, season)
);