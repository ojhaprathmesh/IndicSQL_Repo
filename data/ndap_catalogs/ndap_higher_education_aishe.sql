-- DDL Specification: ndap_higher_education_aishe
-- Domain: Education
-- Colleges, universities, faculty census, and Gross Enrollment Ratios (GER).
CREATE TABLE IF NOT EXISTS ndap_higher_education_aishe (
    state_name VARCHAR,
    survey_year VARCHAR,
    university_count INTEGER,
    college_count INTEGER,
    gross_enrollment_ratio_male FLOAT,
    gross_enrollment_ratio_female FLOAT,
    total_faculty_count INTEGER,
    PRIMARY KEY (state_name, survey_year)
);