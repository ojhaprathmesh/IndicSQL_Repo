-- DDL Specification: ndap_fertilizer_distribution
-- Domain: Agriculture
-- District-level fertilizer allocations, stock availability, and retail point sales.
CREATE TABLE IF NOT EXISTS ndap_fertilizer_distribution (
    state_name VARCHAR,
    district_name VARCHAR,
    financial_year VARCHAR,
    fertilizer_type VARCHAR,
    requirement_tonnes DOUBLE,
    availability_tonnes DOUBLE,
    sales_tonnes DOUBLE,
    PRIMARY KEY (state_name, district_name, financial_year, fertilizer_type)
);