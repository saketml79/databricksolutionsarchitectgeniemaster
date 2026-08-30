CREATE OR REPLACE VIEW `${catalog}`.`${schema}`.v_architecture_knowledge_current AS
SELECT item.feature_name, item.capability_claim, item.limitation_claim, item.release_state,
       item.cloud_scope, item.region_scope, source.canonical_url, source.published_at, item.reviewed_at
FROM `${catalog}`.`${schema}`.architecture_knowledge_item item
JOIN `${catalog}`.`${schema}`.architecture_knowledge_source source ON item.source_id = source.source_id
WHERE item.review_status = 'REVIEWED' AND item.supersedes_knowledge_id IS NULL;
-- STATEMENT
CREATE OR REPLACE VIEW `${catalog}`.`${schema}`.v_architecture_kpis AS
SELECT 'failed_run_rate' AS metric, owner AS dimension, avg(failed_run_rate) AS metric_value
FROM `${catalog}`.`${schema}`.workload_summary GROUP BY owner
UNION ALL
SELECT 'monthly_cost_usd', owner, sum(monthly_cost_usd)
FROM `${catalog}`.`${schema}`.cost_summary GROUP BY owner;
-- STATEMENT
CREATE OR REPLACE FUNCTION `${catalog}`.`${schema}`.find_reusable_assets(search_term STRING)
RETURNS TABLE(asset_id STRING, asset_type STRING, full_name STRING, owner STRING, classification STRING)
RETURN SELECT asset_id, asset_type, full_name, owner, classification
FROM `${catalog}`.`${schema}`.platform_asset
WHERE lifecycle_state = 'ACTIVE' AND lower(concat_ws(' ', asset_type, full_name, domain)) LIKE concat('%', lower(search_term), '%');
-- STATEMENT
CREATE OR REPLACE FUNCTION `${catalog}`.`${schema}`.downstream_impact(source_asset_id STRING)
RETURNS TABLE(relationship_type STRING, downstream_asset STRING, downstream_owner STRING, source_ref STRING)
RETURN SELECT relationship_type, target.full_name, target.owner, relationship.source_ref
FROM `${catalog}`.`${schema}`.platform_relationship relationship
JOIN `${catalog}`.`${schema}`.platform_asset target ON relationship.to_asset_id = target.asset_id
WHERE relationship.from_asset_id = source_asset_id;
-- STATEMENT
CREATE OR REPLACE FUNCTION `${catalog}`.`${schema}`.summarize_cost_drivers(domain_name STRING)
RETURNS TABLE(compute_name STRING, monthly_cost_usd DECIMAL(12,2), utilization_pct DOUBLE, recommendation STRING)
RETURN SELECT cost.compute_name, cost.monthly_cost_usd, cost.utilization_pct, cost.recommendation
FROM `${catalog}`.`${schema}`.cost_summary cost
JOIN `${catalog}`.`${schema}`.platform_asset asset ON asset.owner = cost.owner
WHERE asset.domain = domain_name;