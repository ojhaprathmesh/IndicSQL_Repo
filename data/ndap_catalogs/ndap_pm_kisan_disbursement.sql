-- DDL Specification: ndap_pm_kisan_disbursement
-- Domain: Agriculture
-- Pradhan Mantri Kisan Samman Nidhi state and district level fund disbursements.
CREATE TABLE IF NOT EXISTS ndap_pm_kisan_disbursement (
    state_name VARCHAR,
    district_name VARCHAR,
    financial_year VARCHAR,
    farmer_beneficiaries BIGINT,
    amount_inr DOUBLE,
    PRIMARY KEY (state_name, district_name, financial_year)
);