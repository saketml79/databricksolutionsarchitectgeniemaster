# Databricks notebook source
import hashlib

dbutils.widgets.text("catalog", "databricks_architect_agent")
dbutils.widgets.text("schema", "agent_demo")
dbutils.widgets.text("proposal_id", "")
dbutils.widgets.dropdown("decision", "APPROVED", ["APPROVED", "REJECTED"])
dbutils.widgets.text("decision_reason", "")
catalog, schema = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")
proposal_id = dbutils.widgets.get("proposal_id").strip()
decision = dbutils.widgets.get("decision").strip()
reason = dbutils.widgets.get("decision_reason").strip()
if not proposal_id or not reason:
    raise ValueError("proposal_id and decision_reason are required")
if decision not in {"APPROVED", "REJECTED"}:
    raise ValueError("decision must be APPROVED or REJECTED")
escaped_proposal_id, escaped_reason = proposal_id.replace("'", "''"), reason.replace("'", "''")
proposal = spark.sql(f"SELECT status FROM `{catalog}`.`{schema}`.architecture_proposal WHERE proposal_id = '{escaped_proposal_id}'").collect()
if len(proposal) != 1 or proposal[0]["status"] != "PENDING_APPROVAL":
    raise ValueError("proposal must exist and be PENDING_APPROVAL")
approval_id = hashlib.sha256(f"{proposal_id}|{decision}|{reason}".encode()).hexdigest()[:32]
spark.sql(f"""MERGE INTO `{catalog}`.`{schema}`.architecture_approval target
USING (SELECT '{approval_id}' approval_id) source ON target.approval_id = source.approval_id
WHEN NOT MATCHED THEN INSERT (approval_id, proposal_id, decision, decision_reason, decided_by, decided_at)
VALUES ('{approval_id}', '{escaped_proposal_id}', '{decision}', '{escaped_reason}', current_user(), current_timestamp())""")
spark.sql(f"""UPDATE `{catalog}`.`{schema}`.architecture_proposal
SET status = '{decision}', reviewed_at = current_timestamp(), reviewed_by = current_user()
WHERE proposal_id = '{escaped_proposal_id}'""")
spark.sql(f"""UPDATE `{catalog}`.`{schema}`.architecture_request
SET status = '{decision}', updated_at = current_timestamp()
WHERE active_proposal_id = '{escaped_proposal_id}'""")
dbutils.notebook.exit(f"Recorded {decision} decision for {proposal_id}. No infrastructure action was performed.")