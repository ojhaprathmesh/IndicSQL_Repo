-- DDL Specification: ndap_soil_health_records
-- Domain: Agriculture
-- Micro and macro nutrient soil test profiles and Soil Health Cards issued.
CREATE TABLE IF NOT EXISTS ndap_soil_health_records (
    state_name VARCHAR,
    district_name VARCHAR,
    cycle_year INTEGER,
    samples_tested INTEGER,
    cards_issued INTEGER,
    nitrogen_status VARCHAR,
    phosphorus_status VARCHAR,
    organic_carbon_pct FLOAT,
    PRIMARY KEY (state_name, district_name, cycle_year)
);