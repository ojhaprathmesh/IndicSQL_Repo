-- DDL Specification: ndap_gram_panchayat_finance
-- Domain: Rural Development
-- Fifteenth Finance Commission basic and tied grants allocated to Gram Panchayats.
CREATE TABLE IF NOT EXISTS ndap_gram_panchayat_finance (
    state_name VARCHAR,
    district_name VARCHAR,
    financial_year VARCHAR,
    gram_panchayat_count INTEGER,
    grant_allocated_inr DOUBLE,
    grant_utilized_inr DOUBLE,
    sanitation_drinking_water_expenditure_inr DOUBLE,
    PRIMARY KEY (state_name, district_name, financial_year)
);