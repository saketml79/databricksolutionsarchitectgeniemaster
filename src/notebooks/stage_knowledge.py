# Databricks notebook source
import hashlib
import re
import uuid
from datetime import datetime, timezone
from urllib.request import Request, urlopen

dbutils.widgets.text("catalog", "databricks_architect_agent")
dbutils.widgets.text("schema", "agent_demo")
catalog, schema = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")
approved_sources = [
    ("Databricks", "DOCUMENTATION", "https://docs.databricks.com/aws/en/generative-ai/vector-search", "Vector Search", "Official Vector Search guidance staged for reviewer confirmation.", "Validate cloud, region, and workspace entitlement before a recommendation."),
    ("Databricks", "DOCUMENTATION", "https://docs.databricks.com/aws/en/admin/system-tables/", "System tables", "Official System Tables guidance staged for reviewer confirmation.", "System table access and retention are workspace-specific and permission-gated."),
    ("Databricks", "RELEASE_NOTES", "https://docs.databricks.com/aws/en/release-notes/", "Databricks release notes", "Official release guidance staged for reviewer confirmation.", "Release scope and availability can vary by cloud, region, and workspace entitlement.")
]
now = datetime.now(timezone.utc).isoformat()
for publisher, source_type, url, feature, capability, limitation in approved_sources:
    allowed = spark.sql(f"""SELECT count(*) AS count FROM `{catalog}`.`{schema}`.knowledge_source_allowlist
    WHERE active = true AND '{url.replace("'", "''")}' LIKE source_pattern""").first()["count"]
    if allowed < 1:
        raise ValueError(f"Source is not allowlisted: {url}")
    try:
        request = Request(url, headers={"User-Agent": "databricks-solutions-architect-knowledge/1.0"})
        with urlopen(request, timeout=20) as response:
            raw_content = response.read(1_000_000).decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        normalized_content = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw_content)).strip()
        ingestion_status = "CANDIDATE"
    except Exception as error:
        normalized_content = f"Retrieval failed: {str(error)[:500]}"
        ingestion_status = "RETRIEVAL_FAILED"
    content_hash = hashlib.sha256(normalized_content.encode()).hexdigest()
    source_id = f"source_{content_hash[:16]}"
    knowledge_id = f"knowledge_{content_hash[:16]}"
    spark.sql(f"""
      MERGE INTO `{catalog}`.`{schema}`.architecture_knowledge_source target
      USING (SELECT '{source_id}' source_id, '{url}' canonical_url, '{source_type}' source_type, '{publisher}' publisher,
                    timestamp('{now}') retrieved_at, '{content_hash}' content_hash, 'review-workspace://knowledge/{source_id}' raw_content_uri) source
      ON target.canonical_url = source.canonical_url AND target.content_hash = source.content_hash
      WHEN NOT MATCHED THEN INSERT (source_id, canonical_url, source_type, publisher, published_at, retrieved_at, content_hash, raw_content_uri, ingestion_status)
      VALUES (source.source_id, source.canonical_url, source.source_type, source.publisher, NULL, source.retrieved_at, source.content_hash, source.raw_content_uri, '{ingestion_status}')
    """)
    spark.sql(f"""
      MERGE INTO `{catalog}`.`{schema}`.architecture_knowledge_item target
      USING (SELECT '{knowledge_id}' knowledge_id, '{source_id}' source_id, '{feature}' feature_name,
                    '{capability}' capability_claim, '{limitation}' limitation_claim, timestamp('{now}') extracted_at) source
      ON target.knowledge_id = source.knowledge_id
      WHEN NOT MATCHED THEN INSERT (knowledge_id, source_id, feature_name, capability_claim, limitation_claim, release_state, cloud_scope, region_scope, review_status, valid_from, supersedes_knowledge_id, extracted_at, reviewed_at)
      VALUES (source.knowledge_id, source.source_id, source.feature_name, source.capability_claim, source.limitation_claim, 'UNVERIFIED', 'workspace-specific', 'workspace-specific', 'CANDIDATE', source.extracted_at, NULL, source.extracted_at, NULL)
    """)
    for ordinal, start in enumerate(range(0, len(normalized_content), 4000)):
      chunk = normalized_content[start:start + 4000].replace("'", "''")
      chunk_id = hashlib.sha256(f"{knowledge_id}|{ordinal}|{content_hash}".encode()).hexdigest()
      spark.sql(f"""MERGE INTO `{catalog}`.`{schema}`.architecture_knowledge_chunk target
      USING (SELECT '{chunk_id}' chunk_id) source ON target.chunk_id = source.chunk_id
      WHEN NOT MATCHED THEN INSERT (chunk_id, knowledge_id, source_id, canonical_url, publisher, feature_name, content, content_hash, chunk_ordinal, review_status, cloud_scope, region_scope, published_at, retrieved_at, reviewed_at)
      VALUES ('{chunk_id}', '{knowledge_id}', '{source_id}', '{url}', '{publisher}', '{feature}', '{chunk}', '{content_hash}', {ordinal}, 'CANDIDATE', 'workspace-specific', 'workspace-specific', NULL, timestamp('{now}'), NULL)""")
dbutils.notebook.exit("Allowlisted official sources were retrieved, versioned, chunked, and staged as CANDIDATE. No affirmative capability claim is available until human review.")