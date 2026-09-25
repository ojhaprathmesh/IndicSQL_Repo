-- DDL Specification: ndap_pmgsy_rural_roads
-- Domain: Rural Development
-- All-weather road connectivity to eligible unconnected rural habitations.
CREATE TABLE IF NOT EXISTS ndap_pmgsy_rural_roads (
    state_name VARCHAR,
    district_name VARCHAR,
    financial_year VARCHAR,
    sanctioned_road_length_km DOUBLE,
    completed_road_length_km DOUBLE,
    habitations_connected INTEGER,
    total_expenditure_inr DOUBLE,
    PRIMARY KEY (state_name, district_name, financial_year)
);