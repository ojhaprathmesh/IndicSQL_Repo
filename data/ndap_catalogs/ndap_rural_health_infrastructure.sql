-- DDL Specification: ndap_rural_health_infrastructure
-- Domain: Healthcare
-- Primary healthcare centers (PHC), community health centers (CHC), and specialist doctors.
CREATE TABLE IF NOT EXISTS ndap_rural_health_infrastructure (
    state_name VARCHAR,
    reporting_year INTEGER,
    sub_centres_count INTEGER,
    primary_health_centres_phc INTEGER,
    community_health_centres_chc INTEGER,
    doctors_at_phc INTEGER,
    specialists_at_chc INTEGER,
    PRIMARY KEY (state_name, reporting_year)
);