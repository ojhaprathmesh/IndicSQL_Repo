-- DDL Specification: ndap_jal_jeevan_tap_water
-- Domain: Rural Development
-- Rural household tap water connections (FHTC) and water quality surveillance.
CREATE TABLE IF NOT EXISTS ndap_jal_jeevan_tap_water (
    state_name VARCHAR,
    district_name VARCHAR,
    total_rural_households INTEGER,
    households_with_tap_connection INTEGER,
    tap_connection_coverage_pct FLOAT,
    villages_certified_har_ghar_jal INTEGER,
    PRIMARY KEY (state_name, district_name)
);