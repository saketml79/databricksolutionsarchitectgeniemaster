# Databricks notebook source
dbutils.widgets.text("catalog", "databricks_architect_agent")
dbutils.widgets.text("schema", "agent_demo")
dbutils.widgets.text("knowledge_id", "")
dbutils.widgets.text("reviewer", "")
catalog, schema = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")
knowledge_id, reviewer = dbutils.widgets.get("knowledge_id").strip(), dbutils.widgets.get("reviewer").strip()
if not knowledge_id or not reviewer:
    raise ValueError("knowledge_id and reviewer are required for an explicit human review promotion")
spark.sql(f"""UPDATE `{catalog}`.`{schema}`.architecture_knowledge_item
SET review_status = 'REVIEWED', reviewed_at = current_timestamp()
WHERE knowledge_id = '{knowledge_id.replace("'", "''")}' AND review_status = 'CANDIDATE'""")
spark.sql(f"""UPDATE `{catalog}`.`{schema}`.architecture_knowledge_chunk
SET review_status = 'REVIEWED', reviewed_at = current_timestamp()
WHERE knowledge_id = '{knowledge_id.replace("'", "''")}' AND review_status = 'CANDIDATE'""")
dbutils.notebook.exit(f"Knowledge {knowledge_id} promoted by {reviewer} after explicit review.")