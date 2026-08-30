CREATE TABLE IF NOT EXISTS `${catalog}`.`retail_pos`.dim_store (
  store_id STRING COMMENT 'Stable unique identifier for a retail store.',
  store_name STRING COMMENT 'Business name of the retail store.',
  region STRING COMMENT 'Sales operating region used for regional rollups.',
  store_format STRING COMMENT 'Retail format such as Flagship, Mall, or Outlet.',
  opened_date DATE COMMENT 'Date on which the store began trading.'
) COMMENT 'Retail POS store dimension. One row per physical store.';
-- STATEMENT
INSERT OVERWRITE `${catalog}`.`retail_pos`.dim_store
SELECT * FROM VALUES
  ('S001', 'Seattle Flagship', 'West', 'Flagship', DATE'2019-03-01'),
  ('S002', 'Austin Domain', 'South', 'Mall', DATE'2021-06-15'),
  ('S003', 'Boston Harbor', 'East', 'Outlet', DATE'2020-09-10')
AS dim_store(store_id, store_name, region, store_format, opened_date);
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`retail_pos`.dim_product (
  product_id STRING COMMENT 'Stable unique identifier for a sellable product.',
  product_name STRING COMMENT 'Product display name.',
  category STRING COMMENT 'Merchandise category used for product mix analysis.',
  unit_cost DECIMAL(10,2) COMMENT 'Standard unit cost in USD for gross-margin calculations.',
  list_price DECIMAL(10,2) COMMENT 'Standard list price in USD before promotion.'
) COMMENT 'Retail POS product dimension. One row per sellable product.';
-- STATEMENT
INSERT OVERWRITE `${catalog}`.`retail_pos`.dim_product
SELECT * FROM VALUES
  ('P100', 'Trail Jacket', 'Outerwear', 62.00, 129.00),
  ('P200', 'Everyday Runner', 'Footwear', 48.00, 110.00),
  ('P300', 'Canvas Tote', 'Accessories', 9.00, 28.00)
AS dim_product(product_id, product_name, category, unit_cost, list_price);
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`retail_pos`.dim_customer_segment (
  customer_segment_id STRING COMMENT 'Non-identifying customer segment identifier.',
  segment_name STRING COMMENT 'Marketing segment label.',
  loyalty_tier STRING COMMENT 'Loyalty level used for aggregate behavior analysis.',
  customer_count INT COMMENT 'Estimated active customers in this segment.'
) COMMENT 'Non-PII retail customer segmentation dimension. No direct customer identifiers.';
-- STATEMENT
INSERT OVERWRITE `${catalog}`.`retail_pos`.dim_customer_segment
SELECT * FROM VALUES
  ('C001', 'Urban Explorer', 'Gold', 12400),
  ('C002', 'Family Value', 'Silver', 18300),
  ('C003', 'Weekend Athlete', 'Bronze', 9600)
AS dim_customer_segment(customer_segment_id, segment_name, loyalty_tier, customer_count);
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`retail_pos`.fact_pos_sale (
  transaction_id STRING COMMENT 'Unique point-of-sale transaction identifier.',
  transaction_timestamp TIMESTAMP COMMENT 'Timestamp at which the sale completed.',
  store_id STRING COMMENT 'Foreign key to dim_store.store_id.',
  product_id STRING COMMENT 'Foreign key to dim_product.product_id.',
  customer_segment_id STRING COMMENT 'Non-identifying foreign key to dim_customer_segment.',
  quantity INT COMMENT 'Number of units sold in the transaction line.',
  net_sales_usd DECIMAL(10,2) COMMENT 'Net recognized sales amount in USD after discounts.',
  discount_usd DECIMAL(10,2) COMMENT 'Promotion discount amount in USD.',
  channel STRING COMMENT 'Sales channel: STORE or PICKUP.'
) COMMENT 'Retail point-of-sale transaction facts. One row per transaction product line; contains no direct customer PII.';
-- STATEMENT
INSERT OVERWRITE `${catalog}`.`retail_pos`.fact_pos_sale
SELECT * FROM VALUES
  ('T001', TIMESTAMP'2026-08-28 09:15:00', 'S001', 'P100', 'C001', 1, 119.00, 10.00, 'STORE'),
  ('T002', TIMESTAMP'2026-08-28 11:10:00', 'S002', 'P200', 'C002', 2, 200.00, 20.00, 'STORE'),
  ('T003', TIMESTAMP'2026-08-29 14:05:00', 'S001', 'P300', 'C003', 3, 72.00, 12.00, 'PICKUP'),
  ('T004', TIMESTAMP'2026-08-29 16:20:00', 'S003', 'P100', 'C001', 1, 129.00, 0.00, 'STORE')
AS fact_pos_sale(transaction_id, transaction_timestamp, store_id, product_id, customer_segment_id, quantity, net_sales_usd, discount_usd, channel);
-- STATEMENT
CREATE OR REPLACE VIEW `${catalog}`.`retail_pos`.v_daily_store_sales
COMMENT 'Certified daily retail sales metric view at store, region, and sales-date grain.'
AS SELECT date(sale.transaction_timestamp) AS sales_date, store.store_id, store.store_name, store.region,
          sum(sale.net_sales_usd) AS net_sales_usd, sum(sale.quantity) AS units_sold,
          sum(sale.net_sales_usd - product.unit_cost * sale.quantity) AS gross_profit_usd
FROM `${catalog}`.`retail_pos`.fact_pos_sale sale
JOIN `${catalog}`.`retail_pos`.dim_store store ON sale.store_id = store.store_id
JOIN `${catalog}`.`retail_pos`.dim_product product ON sale.product_id = product.product_id
GROUP BY date(sale.transaction_timestamp), store.store_id, store.store_name, store.region;
-- STATEMENT
CREATE OR REPLACE VIEW `${catalog}`.`retail_pos`.v_category_sales
COMMENT 'Certified retail sales metric view at sales-date, region, category, and channel grain.'
AS SELECT date(sale.transaction_timestamp) AS sales_date, store.region, product.category, sale.channel,
          sum(sale.net_sales_usd) AS net_sales_usd, sum(sale.quantity) AS units_sold,
          sum(sale.discount_usd) AS discount_usd
FROM `${catalog}`.`retail_pos`.fact_pos_sale sale
JOIN `${catalog}`.`retail_pos`.dim_store store ON sale.store_id = store.store_id
JOIN `${catalog}`.`retail_pos`.dim_product product ON sale.product_id = product.product_id
GROUP BY date(sale.transaction_timestamp), store.region, product.category, sale.channel;