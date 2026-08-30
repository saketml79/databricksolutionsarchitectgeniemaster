INSERT OVERWRITE `${catalog}`.`${schema}`.platform_asset VALUES
  ('asset_customer_gold','TABLE','main.customer.gold_customer_360','customer-data@contoso.com','customer','PII','ACTIVE',current_timestamp()),
  ('asset_customer_silver','TABLE','main.customer.silver_customer','customer-data@contoso.com','customer','PII','ACTIVE',current_timestamp()),
  ('asset_acquisition_landing','VOLUME','main.acquisition.landing','acquisition@contoso.com','acquisition','CONFIDENTIAL','PLANNED',current_timestamp()),
  ('asset_customer_dashboard','DASHBOARD','Customer 360 Executive Dashboard','bi@contoso.com','customer','INTERNAL','ACTIVE',current_timestamp()),
  ('asset_customer_api','SERVING_ENDPOINT','customer-profile-api','customer-platform@contoso.com','customer','PII','ACTIVE',current_timestamp()),
  ('asset_vector_capability','CAPABILITY','Vector Search','ml-platform@contoso.com','shared','INTERNAL','AVAILABLE',current_timestamp());
-- STATEMENT
INSERT OVERWRITE `${catalog}`.`${schema}`.platform_relationship VALUES
  ('rel_001','asset_customer_silver','FEEDS','asset_customer_gold','UC lineage snapshot; coverage is point-in-time',current_timestamp()),
  ('rel_002','asset_customer_gold','FEEDS','asset_customer_dashboard','UC lineage snapshot; dashboard dependency',current_timestamp()),
  ('rel_003','asset_customer_gold','SERVES','asset_customer_api','UC lineage snapshot; API dependency',current_timestamp());
-- STATEMENT
INSERT OVERWRITE `${catalog}`.`${schema}`.platform_policy VALUES
  ('policy_pii','PII isolation','Customer PII must remain in the customer Unity Catalog boundary.','customer','Unity Catalog catalog/schema','data-governance@contoso.com','ACTIVE',current_timestamp()),
  ('policy_retention','Regional retention','Acquired customer data must remain in its approved region.','acquisition','Storage location and catalog policy','data-governance@contoso.com','ACTIVE',current_timestamp());
-- STATEMENT
INSERT OVERWRITE `${catalog}`.`${schema}`.workload_summary VALUES
  ('workload_customer_refresh','customer-360-refresh','Lakeflow pipeline','customer-data@contoso.com','*/15 * * * *',30,0.02,'HEALTHY',current_timestamp()),
  ('workload_dashboard','customer-360-dashboard-refresh','Job','bi@contoso.com','0 * * * *',60,0.01,'HEALTHY',current_timestamp());
-- STATEMENT
INSERT OVERWRITE `${catalog}`.`${schema}`.cost_summary VALUES
  ('cost_warehouse','customer-bi-warehouse','SQL warehouse','bi@contoso.com',4820.00,22.00,'Resize or enable auto-stop after dashboard review.',current_timestamp()),
  ('cost_idle_cluster','legacy-enrichment-cluster','All-purpose cluster','customer-data@contoso.com',1930.00,4.00,'Retire after validating the replacement pipeline.',current_timestamp());
-- STATEMENT
INSERT OVERWRITE `${catalog}`.`${schema}`.architecture_knowledge_source VALUES
  ('source_vector_search','https://docs.databricks.com/aws/en/generative-ai/vector-search','DOCUMENTATION','Databricks',timestamp('2026-01-01'),current_timestamp(),'demo-vector-search-v1','review-workspace://sources/vector-search','REVIEWED');
-- STATEMENT
INSERT OVERWRITE `${catalog}`.`${schema}`.architecture_knowledge_item VALUES
  ('knowledge_vector_search','source_vector_search','Vector Search','Vector Search can support semantic retrieval over approved indexed content.','Availability and configuration vary by cloud and region; validate workspace entitlement before implementation.','GA','AWS/Azure/GCP','workspace-specific','REVIEWED',timestamp('2026-01-01'),NULL,current_timestamp(),current_timestamp());
-- STATEMENT
INSERT OVERWRITE `${catalog}`.`${schema}`.knowledge_source_allowlist VALUES
  ('https://docs.databricks.com/%','Databricks','DOCUMENTATION',true,'data-governance@contoso.com','Architecture capability and best-practice research',current_timestamp(),current_timestamp()),
  ('https://docs.databricks.com/aws/en/release-notes/','Databricks','RELEASE_NOTES',true,'data-governance@contoso.com','Architecture capability and best-practice research',current_timestamp(),current_timestamp()),
  ('https://docs.databricks.com/%/release-notes/%','Databricks','RELEASE_NOTES',true,'data-governance@contoso.com','Architecture capability and best-practice research',current_timestamp(),current_timestamp());