-- DDL Specification: ndap_national_tuberculosis_portal
-- Domain: Healthcare
-- Tuberculosis notifications, treatment completion outcomes, and nutritional support (Nikshay Poshan).
CREATE TABLE IF NOT EXISTS ndap_national_tuberculosis_portal (
    state_name VARCHAR,
    district_name VARCHAR,
    reporting_year INTEGER,
    total_notified_patients INTEGER,
    treatment_success_rate_pct FLOAT,
    hiv_screened_pct FLOAT,
    dbt_nutritional_amount_inr DOUBLE,
    PRIMARY KEY (state_name, district_name, reporting_year)
);