-- DDL Specification: ndap_midday_meal_scheme
-- Domain: Education
-- Coverage of school meal nutrition, foodgrain quotas, and student beneficiaries.
CREATE TABLE IF NOT EXISTS ndap_midday_meal_scheme (
    state_name VARCHAR,
    district_name VARCHAR,
    financial_year VARCHAR,
    institutions_covered INTEGER,
    primary_students_benefited INTEGER,
    upper_primary_students_benefited INTEGER,
    foodgrains_allocated_mt DOUBLE,
    PRIMARY KEY (state_name, district_name, financial_year)
);