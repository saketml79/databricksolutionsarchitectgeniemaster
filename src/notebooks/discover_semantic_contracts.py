# Databricks notebook source
import json
import uuid

dbutils.widgets.text("catalog", "databricks_architect_agent")
dbutils.widgets.text("schema", "agent_demo")
dbutils.widgets.text("source_schema", "retail_pos")
catalog, schema, source_schema = (dbutils.widgets.get("catalog"), dbutils.widgets.get("schema"), dbutils.widgets.get("source_schema"))
if not all(value.replace("_", "").isalnum() for value in (catalog, schema, source_schema)):
    raise ValueError("catalog and schema values must contain only letters, digits, and underscores")

existing = {row.object_name for row in spark.table(f"{catalog}.{schema}.semantic_data_product").select("object_name").collect()}
discovered = spark.sql(f"SHOW TABLES IN `{catalog}`.`{source_schema}`").collect()
staged = 0
for table in discovered:
    object_name = f"{catalog}.{source_schema}.{table.tableName}"
    if object_name in existing:
        continue
    object_type = "VIEW" if table.isTemporary else "TABLE"
    product_id = str(uuid.uuid4())
    spark.sql(f"""INSERT INTO `{catalog}`.`{schema}`.semantic_data_product VALUES
      ('{product_id}', '{object_name}', '{object_type}', 'retail', NULL, 'UNCLASSIFIED',
       NULL, 'DISCOVERED', 'CANDIDATE', false, NULL, current_timestamp())""")
    staged += 1
    detail = json.dumps({"reason": "New object requires owner, classification, description, column, join, and metric contracts before Genie publication."}).replace("'", "''")
    spark.sql(f"""INSERT INTO `{catalog}`.`{schema}`.platform_observation VALUES
      ('{uuid.uuid4()}', 'semantic_discovery', '{catalog}.{source_schema}', 'NEW_OBJECT', '{object_name}', 'CANDIDATE', '{detail}', current_timestamp())""")
dbutils.notebook.exit(f"Discovered {len(discovered)} objects; staged {staged} incomplete products as CANDIDATE.")