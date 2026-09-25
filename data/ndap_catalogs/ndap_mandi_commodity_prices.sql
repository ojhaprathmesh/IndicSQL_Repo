-- DDL Specification: ndap_mandi_commodity_prices
-- Domain: Agriculture
-- Daily and monthly wholesale agricultural commodity prices across regulated mandis.
CREATE TABLE IF NOT EXISTS ndap_mandi_commodity_prices (
    state_name VARCHAR,
    district_name VARCHAR,
    market_name VARCHAR,
    commodity VARCHAR,
    arrival_date VARCHAR,
    arrival_quantity_tonnes DOUBLE,
    min_price_inr DOUBLE,
    max_price_inr DOUBLE,
    modal_price_inr DOUBLE,
    PRIMARY KEY (state_name, district_name, market_name, commodity, arrival_date)
);