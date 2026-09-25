-- DDL Specification: ndap_nfhs5_health_indicators
-- Domain: Healthcare
-- District maternal health, child nutrition, immunization, and lifestyle indicators.
CREATE TABLE IF NOT EXISTS ndap_nfhs5_health_indicators (
    state_name VARCHAR,
    district_name VARCHAR,
    institutional_births_pct FLOAT,
    fully_vaccinated_children_pct FLOAT,
    stunted_children_pct FLOAT,
    anaemic_women_pct FLOAT,
    households_improved_sanitation_pct FLOAT,
    PRIMARY KEY (state_name, district_name)
);