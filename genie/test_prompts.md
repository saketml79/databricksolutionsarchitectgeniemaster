# Enterprise Architect Genie Acceptance Prompt

Use this prompt in **Enterprise Architect Genie** after the `enterprise_architect_genie_sync` workflow reports `SUCCEEDED`. The governed domain identifier is exactly `retail` and the physical data schema is `retail_pos`.

```text
We need a near-real-time retail POS analytics capability for store leaders and the executive team. Use the governed domain identifier `retail` and the physical schema `databricks_architect_agent.retail_pos`.

First, inspect the governed platform twin and retail POS semantic contracts. Do not ask me for information that is already available in the attached data.

Return:
1. A current-state brief that names the reusable retail POS tables, views, pipeline contracts, owners, classifications, and certified metrics.
2. The approved joins needed to analyze POS sales by store, region, product category, channel, and non-identifying customer segment. Explicitly confirm that no direct customer PII is available.
3. Two feasible architecture options for the active `retail-pos-ingestion` Lakeflow pipeline, which has a 15-minute schedule and a 30-minute freshness SLA. For each option give data flow, Unity Catalog governance boundary, operations owner, cost drivers, downstream impact, migration sequence, rollback, and open questions.
4. A recommendation only if it is supported by the governed evidence. Label unverified source CDC capability and any unavailable workspace telemetry as assumptions.
5. A proposed architecture decision record outline with status PENDING_APPROVAL. Do not provision, deploy, or change permissions.

Cite every factual claim using a table/view, semantic contract, pipeline contract, policy, platform observation, or reviewed knowledge source.
```

Expected evidence includes `retail_pos.fact_pos_sale`, `retail_pos.v_daily_store_sales`, `semantic_join_contract`, `semantic_metric_contract`, and `pipeline_contract`. A passing response supplies alternatives and citations, identifies the active 15-minute ingestion contract, and preserves the PENDING_APPROVAL boundary.