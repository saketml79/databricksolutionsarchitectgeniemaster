# Databricks notebook source
import json
import uuid

dbutils.widgets.text("catalog", "databricks_architect_agent")
dbutils.widgets.text("schema", "agent_demo")
dbutils.widgets.text("requirement_text", "")
dbutils.widgets.text("proposal_title", "")
catalog, schema = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")
requirement, title = dbutils.widgets.get("requirement_text").strip(), dbutils.widgets.get("proposal_title").strip()
if not requirement or not title:
    raise ValueError("requirement_text and proposal_title are required")
proposal_id, requirement_id = str(uuid.uuid4()), str(uuid.uuid4())
escaped_requirement, escaped_title = requirement.replace("'", "''"), title.replace("'", "''")
spark.sql(f"INSERT INTO `{catalog}`.`{schema}`.architecture_requirement VALUES ('{requirement_id}', '{escaped_requirement}', 'HIGH', 'CHANGE_REQUEST', 'Databricks App or approved workflow')")
evidence = json.dumps({"assets": ["asset_customer_gold", "asset_customer_silver"], "policies": ["policy_pii", "policy_retention"], "assumptions": ["Acquisition source CDC capability must be confirmed"]}).replace("'", "''")
migration = json.dumps(["Confirm regional retention and source change feed", "Land data in governed acquisition boundary", "Validate customer key mapping", "Canary customer 360 consumers", "Retain rollback to existing gold table"]).replace("'", "''")
draft_iac = json.dumps({"status": "PROPOSED", "resources": ["catalog schema", "volume", "Lakeflow pipeline", "Vector Search index"]}).replace("'", "''")
spark.sql(f"""INSERT INTO `{catalog}`.`{schema}`.architecture_proposal
VALUES ('{proposal_id}', '{requirement_id}', '{escaped_title}', 'Recommend a phased governed ingestion path with reuse of the customer gold model.', 'PENDING_APPROVAL', '{evidence}', '{migration}', '{draft_iac}', current_timestamp(), current_user(), NULL, NULL)""")
dbutils.notebook.exit(f"Created PENDING_APPROVAL proposal {proposal_id}.")