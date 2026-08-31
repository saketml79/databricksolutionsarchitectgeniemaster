# Databricks notebook source
import hashlib
import json

dbutils.widgets.text("catalog", "databricks_architect_agent")
dbutils.widgets.text("schema", "agent_demo")
dbutils.widgets.text("request_text", "")
dbutils.widgets.text("request_title", "")
dbutils.widgets.text("genie_conversation_id", "")
dbutils.widgets.text("option_graphs", "[]")
catalog, schema = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")
request_text = dbutils.widgets.get("request_text").strip()
request_title = dbutils.widgets.get("request_title").strip()
conversation_id = dbutils.widgets.get("genie_conversation_id").strip()
option_graphs = json.loads(dbutils.widgets.get("option_graphs"))
if not request_text or not request_title:
    raise ValueError("request_text and request_title are required")
if not isinstance(option_graphs, list) or {graph.get("option_id") for graph in option_graphs if isinstance(graph, dict)} != {"option_1", "option_2", "option_3"} or len(option_graphs) != 3:
    raise ValueError("option_graphs must contain exactly option_1, option_2, and option_3")
spark.sql(f"""CREATE TABLE IF NOT EXISTS `{catalog}`.`{schema}`.architecture_option_decision (
    proposal_id STRING, option_id STRING, option_title STRING, status STRING, decision_reason STRING,
    decided_by STRING, decided_at TIMESTAMP
) USING DELTA""")

fingerprint = hashlib.sha256(" ".join(request_text.lower().split()).encode()).hexdigest()
request_id = f"request_{fingerprint[:24]}"
proposal_id = f"proposal_{fingerprint[:24]}_v2"
escaped_request = request_text.replace("'", "''")
escaped_title = request_title.replace("'", "''")

spark.sql(f"""MERGE INTO `{catalog}`.`{schema}`.architecture_request target
USING (SELECT '{request_id}' request_id, '{fingerprint}' request_fingerprint, '{escaped_request}' request_text, '{escaped_title}' request_title) source
ON target.request_fingerprint = source.request_fingerprint
WHEN NOT MATCHED THEN INSERT (request_id, request_fingerprint, request_text, request_title, requester, status, submitted_at, updated_at, active_proposal_id, error_message)
VALUES (source.request_id, source.request_fingerprint, source.request_text, source.request_title, current_user(), 'PROCESSING', current_timestamp(), current_timestamp(), NULL, NULL)""")

existing = spark.sql(f"SELECT proposal_id FROM `{catalog}`.`{schema}`.architecture_proposal WHERE proposal_id = '{proposal_id}'").collect()
if existing:
    option_states = spark.sql(f"""SELECT status FROM `{catalog}`.`{schema}`.architecture_option_decision
    WHERE proposal_id = '{proposal_id}'""").collect()
    if len(option_states) == 3 and all(row.status == "PENDING_APPROVAL" for row in option_states):
        spark.sql(f"""UPDATE `{catalog}`.`{schema}`.architecture_proposal
        SET status = 'PENDING_APPROVAL', reviewed_at = NULL, reviewed_by = NULL
        WHERE proposal_id = '{proposal_id}'""")
    spark.sql(f"UPDATE `{catalog}`.`{schema}`.architecture_request SET status = 'PENDING_APPROVAL', active_proposal_id = '{proposal_id}', updated_at = current_timestamp() WHERE request_id = '{request_id}'")
    dbutils.notebook.exit(json.dumps({"request_id": request_id, "proposal_id": proposal_id, "status": "PENDING_APPROVAL", "idempotent_reuse": True}))

evidence_rows = [
    ("ASSET", "asset_acquisition_landing", "AVAILABLE", "Planned confidential landing volume for acquired-company data."),
    ("ASSET", "asset_customer_silver", "AVAILABLE", "Existing active customer silver asset."),
    ("ASSET", "asset_customer_gold", "AVAILABLE", "Existing active Customer 360 gold-serving asset."),
    ("LINEAGE", "rel_001", "AVAILABLE", "Customer silver feeds Customer 360 gold; point-in-time lineage snapshot."),
    ("LINEAGE", "rel_002", "AVAILABLE", "Customer gold feeds the Customer 360 Executive Dashboard."),
    ("LINEAGE", "rel_003", "AVAILABLE", "Customer gold serves the customer profile API."),
    ("POLICY", "policy_pii", "AVAILABLE", "Customer PII remains in the customer Unity Catalog boundary."),
    ("POLICY", "policy_retention", "AVAILABLE", "Acquired data remains in its approved region."),
    ("WORKLOAD", "workload_customer_refresh", "AVAILABLE", "Customer refresh has a 15-minute schedule and 30-minute freshness SLA."),
    ("COST", "cost_warehouse", "AVAILABLE", "Customer BI warehouse has observed 22 percent utilization."),
    ("COST", "cost_idle_cluster", "AVAILABLE", "Legacy enrichment cluster has observed 4 percent utilization."),
    ("KNOWLEDGE", "knowledge_vector_search", "REVIEWED", "Official Vector Search guidance; entitlement, cloud, and region validation remains required."),
    ("ASSUMPTION", "source_cdc_capability", "UNVERIFIED", "Confirm acquisition source CDC or export behavior before selecting an ingestion pattern.")
]
for index, (evidence_type, evidence_ref, evidence_status, summary) in enumerate(evidence_rows):
    spark.sql(f"""INSERT INTO `{catalog}`.`{schema}`.architecture_evidence VALUES
    ('{proposal_id}_evidence_{index:02d}', '{request_id}', '{proposal_id}', '{evidence_type}', '{evidence_ref}', '{evidence_status}', '{summary.replace("'", "''")}', current_timestamp(), current_timestamp())""")

if conversation_id:
    spark.sql(f"""INSERT INTO `{catalog}`.`{schema}`.architecture_conversation VALUES
    ('{conversation_id.replace("'", "''")}', '{request_id}', 1, 'GENIE', 'Conversation recorded by executor; detailed response remains governed in Genie.', 'GENIE_CONVERSATION_REFERENCE', current_timestamp())""")

evidence = {"request_id": request_id, "organization_evidence": [row[1] for row in evidence_rows if row[0] not in {"ASSUMPTION", "KNOWLEDGE"}], "reviewed_knowledge": "knowledge_vector_search", "assumptions": ["source_cdc_capability"]}
migration = ["Confirm regional retention and source CDC/export capability.", "Land acquired data in the approved regional boundary.", "Validate customer-key mapping against existing customer silver and gold assets.", "Canary dashboard and customer-profile API consumers.", "Retain rollback to existing customer gold serving path."]
draft_iac = {"status": "PROPOSED", "resources": ["Lakeflow ingestion pipeline", "governed landing location", "semantic retrieval index", "review package artifacts"]}
spark.sql(f"""INSERT INTO `{catalog}`.`{schema}`.architecture_proposal VALUES
('{proposal_id}', '{request_id}', '{escaped_title}', 'Recommend a phased governed ingestion path that reuses the existing customer silver and gold serving assets, subject to source CDC and entitlement validation.', 'PENDING_APPROVAL', '{json.dumps(evidence).replace("'", "''")}', '{json.dumps(migration).replace("'", "''")}', '{json.dumps(draft_iac).replace("'", "''")}', current_timestamp(), current_user(), NULL, NULL)""")

artifact_root = f"/Volumes/{catalog}/{schema}/architecture_artifacts/{proposal_id}"
for option_graph in option_graphs:
    escaped_option_title = option_graph["title"].replace("'", "''")
    spark.sql(f"""INSERT INTO `{catalog}`.`{schema}`.architecture_option_decision
    VALUES ('{proposal_id}', '{option_graph['option_id']}', '{escaped_option_title}', 'PENDING_APPROVAL', NULL, NULL, NULL)""")
    graph = {"layout": "architecture", "nodes": option_graph["nodes"], "edges": option_graph["edges"]}
    render_parameters = {"catalog": catalog, "schema": schema, "proposal_id": proposal_id, "artifact_suffix": option_graph["option_id"], "architecture_json": json.dumps(graph), "evidence_json": json.dumps({**evidence, "option_id": option_graph["option_id"], "option_title": option_graph["title"]})}
    dbutils.notebook.run("./render_diagram", 0, render_parameters)
spark.sql(f"""INSERT INTO `{catalog}`.`{schema}`.architecture_review_package VALUES
('{proposal_id}_package', '{request_id}', '{proposal_id}', 'PENDING_APPROVAL', '{artifact_root}_option_1.svg', '{artifact_root}_option_1.png', NULL, '{artifact_root}.references.json', current_timestamp(), current_user())""")
spark.sql(f"UPDATE `{catalog}`.`{schema}`.architecture_request SET status = 'PENDING_APPROVAL', active_proposal_id = '{proposal_id}', updated_at = current_timestamp() WHERE request_id = '{request_id}'")
dbutils.notebook.exit(json.dumps({"request_id": request_id, "proposal_id": proposal_id, "status": "PENDING_APPROVAL", "option_artifacts": [{"option_id": graph["option_id"], "title": graph["title"], "svg_path": f"{artifact_root}_{graph['option_id']}.svg"} for graph in option_graphs], "evidence_manifest_path": f"{artifact_root}.references.json", "idempotent_reuse": False}))