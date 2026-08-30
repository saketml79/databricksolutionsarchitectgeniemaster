# Databricks notebook source
import json
import uuid
from databricks.sdk import WorkspaceClient

dbutils.widgets.text("catalog", "databricks_architect_agent")
dbutils.widgets.text("schema", "agent_demo")
dbutils.widgets.text("genie_space_id", "")
dbutils.widgets.text("warehouse_id", "")
catalog, schema = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")
space_id, warehouse_id = dbutils.widgets.get("genie_space_id"), dbutils.widgets.get("warehouse_id")
if not space_id or not warehouse_id:
    raise ValueError("genie_space_id and warehouse_id are required")

required_context = [
    f"{catalog}.{schema}.platform_asset", f"{catalog}.{schema}.platform_relationship", f"{catalog}.{schema}.platform_policy",
    f"{catalog}.{schema}.workload_summary", f"{catalog}.{schema}.cost_summary", f"{catalog}.{schema}.architecture_proposal",
    f"{catalog}.{schema}.architecture_requirement", f"{catalog}.{schema}.architecture_knowledge_item", f"{catalog}.{schema}.architecture_knowledge_source",
    f"{catalog}.{schema}.semantic_data_product", f"{catalog}.{schema}.semantic_column_contract", f"{catalog}.{schema}.semantic_join_contract",
    f"{catalog}.{schema}.semantic_metric_contract", f"{catalog}.{schema}.pipeline_contract", f"{catalog}.{schema}.genie_sync_audit",
    f"{catalog}.{schema}.v_architecture_knowledge_current", f"{catalog}.{schema}.v_architecture_kpis",
    f"{catalog}.{schema}.v_pending_architecture_proposals", f"{catalog}.{schema}.v_platform_refresh_status",
    f"{catalog}.{schema}.v_genie_semantic_context"
]
approved = spark.sql(f"""SELECT object_name FROM `{catalog}`.`{schema}`.semantic_data_product
WHERE publication_status = 'APPROVED' AND genie_eligible = true AND owner IS NOT NULL
  AND classification <> 'UNCLASSIFIED' AND description IS NOT NULL""").collect()
object_names = sorted(set(required_context + [row.object_name for row in approved]))
serialized_space = json.dumps({
    "version": 2,
    "data_sources": {"tables": [{"identifier": object_name} for object_name in object_names]},
    "instructions": {"text_instructions": [{"content": [
        "You are the Databricks Solutions Architect Genie Agent. Apply this architecture method for every request: establish business outcomes and non-functional constraints; inventory reusable governed assets, lineage, policies, workload, cost, and semantic contracts; compare target-state options for fit, security, reliability, operability, cost, migration, and rollback; then make a conditional recommendation tied to evidence. Use only attached governed products and cite assets, policies, observations, semantic contracts, or REVIEWED knowledge. In semantic_data_product, APPROVED is the published and Genie-eligible publication state; do not substitute PUBLISHED as a filter value. Use v_genie_semantic_context first for certified product and metric discovery, semantic_join_contract for joins, and pipeline_contract for operational contracts. Newly discovered CANDIDATE products are not approved for analysis. Return two or three architecture options with explicit tradeoffs. For visual inspection of existing topology, cost, and pipeline freshness, direct users to the governed AI/BI dashboard named Databricks Solutions Architect - Architecture Topology; do not represent a result table as an architecture diagram and do not emit ASCII, Mermaid, SVG, or Python code. The companion Solutions Architect App renders the proposal-specific governed SVG review artifact. Never provision, delete, deploy, or change permissions. Proposals remain PENDING_APPROVAL. End every response with an Evidence Register containing: Unity Catalog organization evidence with exact asset, relationship, policy, workload, cost, semantic-contract, or pipeline-contract IDs used; reviewed official Databricks knowledge with knowledge ID, URL, review state, scope, and limitation; CANDIDATE research explicitly labeled not used as affirmative evidence; and assumptions or unknowns with the smallest missing fact needed. Cite evidence inline for each option. If attached Unity Catalog evidence was not used or is unavailable, state that explicitly."
    ]}]}
})
payload = {"warehouse_id": warehouse_id, "serialized_space": serialized_space}
try:
    workspace = WorkspaceClient()
    workspace.api_client.do("PATCH", f"/api/2.0/genie/spaces/{space_id}", body=payload)
    status, detail = "SUCCEEDED", {"attached_objects": object_names, "approved_product_count": len(approved)}
except Exception as error:
    status, detail = "FAILED", {"error": str(error)[:1000], "attached_object_count": len(object_names)}
spark.sql(f"""INSERT INTO `{catalog}`.`{schema}`.genie_sync_audit VALUES
  ('{uuid.uuid4()}', '{space_id.replace("'", "''")}', {len(object_names)}, '{status}', '{json.dumps(detail).replace("'", "''")}', current_timestamp())""")
if status != "SUCCEEDED":
    raise RuntimeError(detail["error"])
dbutils.notebook.exit(f"Synchronized {len(object_names)} approved governed objects to Genie space {space_id}.")