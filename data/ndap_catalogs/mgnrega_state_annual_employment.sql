-- DDL Specification: mgnrega_state_annual_employment
-- Domain: Rural Development
-- Mahatma Gandhi NREGA person-days generated, households engaged, and wage expenditures.
CREATE TABLE IF NOT EXISTS mgnrega_state_annual_employment (
    state_name VARCHAR,
    financial_year VARCHAR,
    households_worked BIGINT,
    total_mandays_generated BIGINT,
    women_mandays_pct FLOAT,
    total_wage_expenditure_inr DOUBLE,
    PRIMARY KEY (state_name, financial_year)
);