-- DDL Specification: ndap_school_infrastructure
-- Domain: Education
-- School facility compliance including electricity, drinking water, toilets, and digital labs.
CREATE TABLE IF NOT EXISTS ndap_school_infrastructure (
    state_name VARCHAR,
    district_name VARCHAR,
    academic_year VARCHAR,
    total_schools INTEGER,
    schools_with_electricity INTEGER,
    schools_with_drinking_water INTEGER,
    schools_with_girl_toilets INTEGER,
    schools_with_computer_labs INTEGER,
    PRIMARY KEY (state_name, district_name, academic_year)
);