-- DDL Specification: ndap_education_stats
-- Domain: Education
-- Unified District Information System for Education Plus student and literacy indicators.
CREATE TABLE IF NOT EXISTS ndap_education_stats (
    state_name VARCHAR,
    district_name VARCHAR,
    census_year INTEGER,
    student_count INTEGER,
    female_literacy_rate FLOAT,
    male_literacy_rate FLOAT,
    pupil_teacher_ratio FLOAT,
    PRIMARY KEY (state_name, district_name, census_year)
);