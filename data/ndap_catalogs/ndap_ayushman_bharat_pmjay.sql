-- DDL Specification: ndap_ayushman_bharat_pmjay
-- Domain: Healthcare
-- Golden card issuances, hospital empanelment, and secondary/tertiary claim settlements.
CREATE TABLE IF NOT EXISTS ndap_ayushman_bharat_pmjay (
    state_name VARCHAR,
    district_name VARCHAR,
    financial_year VARCHAR,
    cards_issued BIGINT,
    empanelled_hospitals INTEGER,
    authorized_admissions INTEGER,
    claim_amount_settled_inr DOUBLE,
    PRIMARY KEY (state_name, district_name, financial_year)
);