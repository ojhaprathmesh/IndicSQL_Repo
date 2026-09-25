-- DDL Specification: ndap_pmay_rural_housing
-- Domain: Rural Development
-- Pucca houses sanctioned, constructed, and subsidy installments credited to homeless beneficiaries.
CREATE TABLE IF NOT EXISTS ndap_pmay_rural_housing (
    state_name VARCHAR,
    district_name VARCHAR,
    financial_year VARCHAR,
    houses_sanctioned INTEGER,
    houses_completed INTEGER,
    funds_transferred_inr DOUBLE,
    PRIMARY KEY (state_name, district_name, financial_year)
);