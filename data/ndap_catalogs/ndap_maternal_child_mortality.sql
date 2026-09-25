-- DDL Specification: ndap_maternal_child_mortality
-- Domain: Healthcare
-- Maternal Mortality Ratio (MMR), Infant Mortality Rate (IMR), and Under-5 Mortality.
CREATE TABLE IF NOT EXISTS ndap_maternal_child_mortality (
    state_name VARCHAR,
    survey_year VARCHAR,
    maternal_mortality_ratio_mmr INTEGER,
    infant_mortality_rate_imr INTEGER,
    under_five_mortality_rate_u5mr INTEGER,
    birth_rate FLOAT,
    PRIMARY KEY (state_name, survey_year)
);