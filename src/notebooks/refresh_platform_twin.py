# Databricks notebook source
import json
import uuid
from datetime import datetime, timezone

dbutils.widgets.text("catalog", "databricks_architect_agent")
dbutils.widgets.text("schema", "agent_demo")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
if not catalog.replace("_", "").isalnum() or not schema.replace("_", "").isalnum():
    raise ValueError("catalog and schema must contain only letters, digits, and underscores")

now = datetime.now(timezone.utc).isoformat()
observations = []

def observe(source_name, source_scope, observation_type, subject_ref, status, detail):
    observations.append((str(uuid.uuid4()), source_name, source_scope, observation_type, subject_ref, status, json.dumps(detail), now))

for source_schema in (schema, "retail_pos"):
    try:
        tables = spark.sql(f"SHOW TABLES IN `{catalog}`.`{source_schema}`").collect()
        for table in tables:
            name = f"{catalog}.{source_schema}.{table.tableName}"
            observe("unity_catalog", f"{catalog}.{source_schema}", "TABLE_OR_VIEW", name, "OBSERVED", {"is_temporary": table.isTemporary})
    except Exception as error:
        observe("unity_catalog", f"{catalog}.{source_schema}", "TABLE_OR_VIEW", f"{catalog}.{source_schema}", "UNAVAILABLE", {"error": str(error)[:500]})

for source_name, query in {
    "system.lakeflow": "SELECT count(*) AS count FROM system.lakeflow.job_run_timeline WHERE period_start_time >= current_timestamp() - INTERVAL 7 DAYS",
    "system.billing": "SELECT count(*) AS count FROM system.billing.usage WHERE usage_date >= current_date() - INTERVAL 7 DAYS",
    "system.access": "SELECT count(*) AS count FROM system.access.audit WHERE event_date >= current_date() - INTERVAL 7 DAYS"
}.items():
    try:
        count = spark.sql(query).first()["count"]
        observe(source_name, "read-only system schema", "TELEMETRY", source_name, "OBSERVED", {"seven_day_rows": count})
    except Exception as error:
        observe(source_name, "read-only system schema", "TELEMETRY", source_name, "UNAVAILABLE", {"error": str(error)[:500], "action": "grant approved SELECT or confirm source schema"})

workspace_sources = [
    ("BUNDLE", "databricks.yml"), ("GENIE", "genie/enterprise_architect_genie_space.json"),
    ("APP", "app/enterprise-architect"), ("NOTEBOOK", "src/notebooks"), ("SQL", "src/sql")
]
for artifact_type, path in workspace_sources:
    observe("bundle_manifest", "workspace deployment", artifact_type, path, "DECLARED", {"collection": "manifest-only; code body collection requires an approved workspace/repository connection"})

spark.createDataFrame(observations, "observation_id string, source_name string, source_scope string, observation_type string, subject_ref string, status string, detail_json string, observed_at string") \
    .selectExpr("observation_id", "source_name", "source_scope", "observation_type", "subject_ref", "status", "detail_json", "timestamp(observed_at) AS observed_at") \
    .write.mode("append").saveAsTable(f"{catalog}.{schema}.platform_observation")

dbutils.notebook.exit(f"Recorded {len(observations)} governed platform observations at {now}.")