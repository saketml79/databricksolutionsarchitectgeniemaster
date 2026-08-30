INSERT OVERWRITE `${catalog}`.`${schema}`.semantic_data_product VALUES
  ('retail_store','${catalog}.retail_pos.dim_store','TABLE','retail','retail-analytics@contoso.com','INTERNAL','Store master data for retail sales analysis.','ACTIVE','APPROVED',true,current_timestamp(),current_timestamp()),
  ('retail_product','${catalog}.retail_pos.dim_product','TABLE','retail','retail-analytics@contoso.com','INTERNAL','Product master data for margin and category analysis.','ACTIVE','APPROVED',true,current_timestamp(),current_timestamp()),
  ('retail_segment','${catalog}.retail_pos.dim_customer_segment','TABLE','retail','retail-analytics@contoso.com','INTERNAL','Non-identifying customer segments for aggregate analysis.','ACTIVE','APPROVED',true,current_timestamp(),current_timestamp()),
  ('retail_sales','${catalog}.retail_pos.fact_pos_sale','TABLE','retail','retail-analytics@contoso.com','CONFIDENTIAL','POS transaction lines without direct customer PII.','ACTIVE','APPROVED',true,current_timestamp(),current_timestamp()),
  ('retail_daily_sales','${catalog}.retail_pos.v_daily_store_sales','VIEW','retail','retail-analytics@contoso.com','INTERNAL','Certified daily store sales, units, and gross profit.','ACTIVE','APPROVED',true,current_timestamp(),current_timestamp()),
  ('retail_category_sales','${catalog}.retail_pos.v_category_sales','VIEW','retail','retail-analytics@contoso.com','INTERNAL','Certified category and channel sales metrics.','ACTIVE','APPROVED',true,current_timestamp(),current_timestamp());
-- STATEMENT
INSERT OVERWRITE `${catalog}`.`${schema}`.semantic_column_contract VALUES
  ('${catalog}.retail_pos.dim_store','store_id','STRING','Stable store key.','PRIMARY_KEY','INTERNAL',true,false,'S001','APPROVED',current_timestamp()),
  ('${catalog}.retail_pos.dim_store','region','STRING','Sales region rollup.','DIMENSION','INTERNAL',false,false,'West','APPROVED',current_timestamp()),
  ('${catalog}.retail_pos.dim_product','product_id','STRING','Stable product key.','PRIMARY_KEY','INTERNAL',true,false,'P100','APPROVED',current_timestamp()),
  ('${catalog}.retail_pos.dim_product','category','STRING','Merchandise category.','DIMENSION','INTERNAL',false,false,'Outerwear','APPROVED',current_timestamp()),
  ('${catalog}.retail_pos.dim_customer_segment','customer_segment_id','STRING','Non-identifying segment key.','PRIMARY_KEY','INTERNAL',true,false,'C001','APPROVED',current_timestamp()),
  ('${catalog}.retail_pos.fact_pos_sale','transaction_id','STRING','POS transaction line key.','PRIMARY_KEY','CONFIDENTIAL',false,false,'T001','APPROVED',current_timestamp()),
  ('${catalog}.retail_pos.fact_pos_sale','store_id','STRING','Store join key.','FOREIGN_KEY','INTERNAL',true,false,'S001','APPROVED',current_timestamp()),
  ('${catalog}.retail_pos.fact_pos_sale','product_id','STRING','Product join key.','FOREIGN_KEY','INTERNAL',true,false,'P100','APPROVED',current_timestamp()),
  ('${catalog}.retail_pos.fact_pos_sale','net_sales_usd','DECIMAL(10,2)','Net sales in USD after discounts.','MEASURE','CONFIDENTIAL',false,true,'119.00','APPROVED',current_timestamp()),
  ('${catalog}.retail_pos.fact_pos_sale','quantity','INT','Units sold.','MEASURE','CONFIDENTIAL',false,true,'1','APPROVED',current_timestamp()),
  ('${catalog}.retail_pos.v_daily_store_sales','gross_profit_usd','DECIMAL(38,2)','Net sales less standard product cost.','CERTIFIED_METRIC','INTERNAL',false,true,'57.00','APPROVED',current_timestamp());
-- STATEMENT
INSERT OVERWRITE `${catalog}`.`${schema}`.semantic_join_contract VALUES
  ('join_sale_store','${catalog}.retail_pos.fact_pos_sale','store_id','${catalog}.retail_pos.dim_store','store_id','MANY_TO_ONE','INNER','Each POS sale belongs to one store.','APPROVED',current_timestamp()),
  ('join_sale_product','${catalog}.retail_pos.fact_pos_sale','product_id','${catalog}.retail_pos.dim_product','product_id','MANY_TO_ONE','INNER','Each POS sale references one product.','APPROVED',current_timestamp()),
  ('join_sale_segment','${catalog}.retail_pos.fact_pos_sale','customer_segment_id','${catalog}.retail_pos.dim_customer_segment','customer_segment_id','MANY_TO_ONE','LEFT','Each sale can be grouped by a non-identifying customer segment.','APPROVED',current_timestamp());
-- STATEMENT
INSERT OVERWRITE `${catalog}`.`${schema}`.semantic_metric_contract VALUES
  ('metric_net_sales','Net Sales','${catalog}.retail_pos.v_daily_store_sales','sum(net_sales_usd)','sales_date, store_id','Recognized POS net sales in USD.','retail-analytics@contoso.com','CERTIFIED',current_timestamp()),
  ('metric_units','Units Sold','${catalog}.retail_pos.v_daily_store_sales','sum(units_sold)','sales_date, store_id','Total retail units sold.','retail-analytics@contoso.com','CERTIFIED',current_timestamp()),
  ('metric_gross_profit','Gross Profit','${catalog}.retail_pos.v_daily_store_sales','sum(gross_profit_usd)','sales_date, store_id','Net sales less standard product cost.','retail-analytics@contoso.com','CERTIFIED',current_timestamp());
-- STATEMENT
INSERT OVERWRITE `${catalog}`.`${schema}`.pipeline_contract VALUES
  ('pipeline_pos_ingest','retail-pos-ingestion','Lakeflow','retail source POS feed','${catalog}.retail_pos.fact_pos_sale','*/15 * * * *',30,'retail-analytics@contoso.com','ACTIVE',current_timestamp()),
  ('pipeline_pos_metrics','retail-sales-metrics','SQL materialization','${catalog}.retail_pos.fact_pos_sale','${catalog}.retail_pos.v_daily_store_sales','0 * * * *',60,'retail-analytics@contoso.com','ACTIVE',current_timestamp());