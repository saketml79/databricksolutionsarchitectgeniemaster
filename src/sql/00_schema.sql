CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.platform_asset (
  asset_id STRING, asset_type STRING, full_name STRING, owner STRING, domain STRING,
  classification STRING, lifecycle_state STRING, observed_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.platform_relationship (
  relationship_id STRING, from_asset_id STRING, relationship_type STRING, to_asset_id STRING,
  source_ref STRING, observed_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.architecture_requirement (
  requirement_id STRING, requirement_text STRING, priority STRING, constraint_type STRING,
  source_ref STRING
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.platform_policy (
  policy_id STRING, policy_name STRING, requirement_text STRING, applies_to_domain STRING,
  enforcement_boundary STRING, owner STRING, status STRING, observed_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.workload_summary (
  workload_id STRING, workload_name STRING, workload_type STRING, owner STRING, schedule STRING,
  freshness_sla_minutes INT, failed_run_rate DOUBLE, status STRING, observed_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.cost_summary (
  cost_record_id STRING, compute_name STRING, compute_type STRING, owner STRING,
  monthly_cost_usd DECIMAL(12,2), utilization_pct DOUBLE, recommendation STRING, observed_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.architecture_proposal (
  proposal_id STRING, requirement_id STRING, title STRING, recommendation STRING, status STRING,
  evidence_json STRING, migration_plan_json STRING, draft_iac_json STRING, created_at TIMESTAMP,
  created_by STRING, reviewed_at TIMESTAMP, reviewed_by STRING
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.architecture_knowledge_source (
  source_id STRING, canonical_url STRING, source_type STRING, publisher STRING, published_at TIMESTAMP,
  retrieved_at TIMESTAMP, content_hash STRING, raw_content_uri STRING, ingestion_status STRING
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.architecture_knowledge_item (
  knowledge_id STRING, source_id STRING, feature_name STRING, capability_claim STRING,
  limitation_claim STRING, release_state STRING, cloud_scope STRING, region_scope STRING,
  review_status STRING, valid_from TIMESTAMP, supersedes_knowledge_id STRING,
  extracted_at TIMESTAMP, reviewed_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.platform_observation (
  observation_id STRING, source_name STRING, source_scope STRING, observation_type STRING,
  subject_ref STRING, status STRING, detail_json STRING, observed_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.workspace_artifact (
  artifact_id STRING, artifact_type STRING, artifact_path STRING, content_hash STRING,
  lifecycle_state STRING, source_ref STRING, observed_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.diagram_artifact (
  artifact_id STRING, proposal_id STRING, artifact_type STRING, volume_path STRING,
  content_hash STRING, status STRING, created_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.semantic_data_product (
  product_id STRING, object_name STRING, object_type STRING, domain STRING, owner STRING,
  classification STRING, description STRING, lifecycle_state STRING, publication_status STRING,
  genie_eligible BOOLEAN, last_validated_at TIMESTAMP, observed_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.semantic_column_contract (
  object_name STRING, column_name STRING, data_type STRING, business_description STRING,
  semantic_role STRING, sensitivity STRING, is_join_key BOOLEAN, is_metric_input BOOLEAN,
  example_value STRING, contract_status STRING, observed_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.semantic_join_contract (
  join_id STRING, left_object STRING, left_column STRING, right_object STRING, right_column STRING,
  cardinality STRING, join_type STRING, description STRING, contract_status STRING, observed_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.semantic_metric_contract (
  metric_id STRING, metric_name STRING, object_name STRING, expression_sql STRING, grain_description STRING,
  business_description STRING, owner STRING, certification_status STRING, observed_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.pipeline_contract (
  pipeline_id STRING, pipeline_name STRING, pipeline_type STRING, source_object STRING, target_object STRING,
  schedule STRING, freshness_sla_minutes INT, owner STRING, lifecycle_state STRING, observed_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.genie_sync_audit (
  sync_id STRING, space_id STRING, object_count INT, publication_status STRING, detail_json STRING, synced_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.architecture_knowledge_chunk (
  chunk_id STRING, knowledge_id STRING, source_id STRING, canonical_url STRING, publisher STRING,
  feature_name STRING, content STRING, content_hash STRING, chunk_ordinal INT, review_status STRING,
  cloud_scope STRING, region_scope STRING, published_at TIMESTAMP, retrieved_at TIMESTAMP, reviewed_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.architecture_request (
  request_id STRING, request_fingerprint STRING, request_text STRING, request_title STRING, requester STRING,
  status STRING, submitted_at TIMESTAMP, updated_at TIMESTAMP, active_proposal_id STRING, error_message STRING
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.architecture_conversation (
  conversation_id STRING, request_id STRING, turn_number INT, actor_type STRING, content STRING,
  content_type STRING, created_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.architecture_evidence (
  evidence_id STRING, request_id STRING, proposal_id STRING, evidence_type STRING, evidence_ref STRING,
  evidence_status STRING, summary STRING, observed_at TIMESTAMP, used_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.knowledge_source_allowlist (
  source_pattern STRING, publisher STRING, source_type STRING, active BOOLEAN, review_owner STRING,
  allowed_purpose STRING, added_at TIMESTAMP, updated_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.architecture_approval (
  approval_id STRING, proposal_id STRING, decision STRING, decision_reason STRING, decided_by STRING,
  decided_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.architecture_option_decision (
  proposal_id STRING, option_id STRING, option_title STRING, status STRING, decision_reason STRING,
  decided_by STRING, decided_at TIMESTAMP
) USING DELTA;
-- STATEMENT
CREATE TABLE IF NOT EXISTS `${catalog}`.`${schema}`.architecture_review_package (
  package_id STRING, request_id STRING, proposal_id STRING, package_status STRING, svg_path STRING,
  png_path STRING, pdf_path STRING, evidence_manifest_path STRING, created_at TIMESTAMP, created_by STRING
) USING DELTA;