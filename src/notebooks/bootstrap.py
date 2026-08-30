# Databricks notebook source
dbutils.widgets.text("catalog", "databricks_architect_agent")
dbutils.widgets.text("schema", "agent_demo")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
if not catalog.replace("_", "").isalnum() or not schema.replace("_", "").isalnum():
    raise ValueError("catalog and schema must contain only letters, digits, and underscores")

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}`")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`retail_pos`")

for filename in ("00_schema.sql", "01_seed.sql", "02_views_and_functions.sql", "03_governed_runtime.sql", "04_retail_pos.sql", "05_semantic_contracts.sql"):
    source_path = f"../sql/{filename}"
    with open(source_path, "r", encoding="utf-8") as source_file:
        statements = source_file.read().replace("${catalog}", catalog).replace("${schema}", schema).split("-- STATEMENT")
    for statement in statements:
        if statement.strip():
            spark.sql(statement)

dbutils.notebook.exit("Governed platform twin is ready; all generated proposals remain PENDING_APPROVAL.")