-- DDL Specification: ndap_vocational_skill_training
-- Domain: Education
-- Short-term skilling, ITI certifications, and placement records.
CREATE TABLE IF NOT EXISTS ndap_vocational_skill_training (
    state_name VARCHAR,
    district_name VARCHAR,
    financial_year VARCHAR,
    sector_skill_council VARCHAR,
    enrolled_candidates INTEGER,
    certified_candidates INTEGER,
    placed_candidates INTEGER,
    PRIMARY KEY (state_name, district_name, financial_year, sector_skill_council)
);