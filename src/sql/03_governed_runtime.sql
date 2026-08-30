CREATE VOLUME IF NOT EXISTS `${catalog}`.`${schema}`.architecture_artifacts
COMMENT 'Review-only Mermaid, SVG, PNG, and draft IaC artifacts created by the Enterprise Architect workflow.';
-- STATEMENT
CREATE OR REPLACE VIEW `${catalog}`.`${schema}`.v_platform_refresh_status AS
SELECT source_name, source_scope, status, max(observed_at) AS last_observed_at
FROM `${catalog}`.`${schema}`.platform_observation
GROUP BY source_name, source_scope, status;
-- STATEMENT
CREATE OR REPLACE VIEW `${catalog}`.`${schema}`.v_pending_architecture_proposals AS
SELECT proposal_id, requirement_id, title, recommendation, status, created_at, created_by
FROM `${catalog}`.`${schema}`.architecture_proposal
WHERE status = 'PENDING_APPROVAL';
-- STATEMENT
ALTER TABLE `${catalog}`.`${schema}`.architecture_knowledge_chunk
SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
-- STATEMENT
CREATE OR REPLACE VIEW `${catalog}`.`${schema}`.v_genie_semantic_context AS
SELECT product.object_name AS governed_object, product.object_type, product.domain, product.owner,
	   product.classification, product.description, product.publication_status,
	   concat('APPROVED is the published and Genie-eligible state for this governed data product.') AS publication_guidance
FROM `${catalog}`.`${schema}`.semantic_data_product product
WHERE product.publication_status = 'APPROVED' AND product.genie_eligible = true
UNION ALL
SELECT metric.object_name, 'CERTIFIED_METRIC', 'retail', metric.owner, 'INTERNAL', metric.business_description,
	   metric.certification_status, concat(metric.metric_name, ': ', metric.expression_sql, '; grain: ', metric.grain_description)
FROM `${catalog}`.`${schema}`.semantic_metric_contract metric
WHERE metric.certification_status = 'CERTIFIED';