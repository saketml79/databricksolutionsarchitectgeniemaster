# Test Runbook

Run these checks from the repository root using the authenticated `saket_dbx_dev` profile.

## 1. Validate and deploy the bundle

```powershell
databricks bundle validate -t dev --profile saket_dbx_dev
databricks bundle deploy -t dev --profile saket_dbx_dev
databricks bundle run enterprise_architect_bootstrap -t dev --profile saket_dbx_dev
```

Expected result: the `agent_demo` architecture-twin schema, the `retail_pos` demonstration/acceptance-test schema, semantic contracts, and artifact Volume are available in `databricks_architect_agent`. Retail POS validates the reusable pattern; it is not the agent's domain limit.

## 2. Refresh and synchronize governed context

```powershell
databricks bundle run enterprise_architect_platform_refresh -t dev --profile saket_dbx_dev
databricks bundle run enterprise_architect_semantic_discovery -t dev --profile saket_dbx_dev
databricks bundle run enterprise_architect_genie_sync -t dev --profile saket_dbx_dev
```

Expected result: discovered but incomplete objects remain `CANDIDATE`; complete approved data products are added to Genie. Inspect `genie_sync_audit` for the exact attached-object count.

## 3. Run SQL benchmarks

Execute [architecture_agent_benchmarks.sql](../benchmarks/architecture_agent_benchmarks.sql) in `lab-warehouse`.

Expected result:

- Reuse discovery returns the customer gold asset.
- Lineage impact returns the dashboard and profile API.
- Policy query returns PII isolation and regional retention controls.
- Retail daily sales and semantic joins return the seeded demonstration data.

## 4. Test Genie with the retail POS demonstration

Copy the complete acceptance prompt from [test_prompts.md](../genie/test_prompts.md) into **Databricks Solutions Architect Genie**.

The smaller deterministic smoke test is:

```text
Use domain retail and schema databricks_architect_agent.retail_pos. List the six APPROVED, Genie-eligible retail data products from v_genie_semantic_context, the CERTIFIED metrics, the APPROVED store and product join contracts, and the ACTIVE retail-pos-ingestion pipeline with its schedule, freshness SLA, and owner. State whether direct customer PII is present using semantic_column_contract. Cite the relevant objects.
```

Expected response must identify six retail demonstration data products, three certified metrics, the `fact_pos_sale` to `dim_product` and `dim_store` join paths, `retail-pos-ingestion`, its 15-minute schedule and 30-minute freshness SLA, `retail-analytics@contoso.com`, and the non-PII result. This confirms the domain-agnostic governance pattern before additional approved domains are enrolled.

## 5. Test the production request-to-review workflow

```powershell
databricks bundle run enterprise_architect_request_executor -t dev --profile saket_dbx_dev
databricks bundle run enterprise_architect_review_package -t dev --profile saket_dbx_dev
databricks fs ls dbfs:/Volumes/databricks_architect_agent/agent_demo/architecture_artifacts --profile saket_dbx_dev
```

Expected result: one fingerprinted request, one `PENDING_APPROVAL` proposal, evidence records, and `.mmd`, `.svg`, `.png`, `.references.json`, `.review.html`, and `.pdf` artifacts. The SVG should include requested icons from the governed `architecture_icons` Volume. Direct workflow runs without a `request_nonce` are idempotent. Each explicit App Generate action includes a unique request nonce and creates a distinct reviewable proposal.

Open the Databricks Solutions Architect App to view persisted review packages and record an explicit approval or rejection with a reason. The App records the decision but never executes the design.

## 6. Test the knowledge lifecycle

```powershell
databricks bundle run enterprise_architect_knowledge_stage -t dev --profile saket_dbx_dev
```

Expected result: extracted source and chunk records are `CANDIDATE`. Do not use these as affirmative design claims until an authorized reviewer runs `promote_knowledge_review.py` with a candidate knowledge ID and reviewer identifier.

This is the mechanism that keeps architecture recommendations current with official Databricks documentation and best practices: the Knowledge MCP reads allowlisted `docs.databricks.com` public internet content, the governed review flow verifies it, and the Genie Agent uses only `REVIEWED` claims for affirmative recommendations.

Verify the dedicated hybrid Delta Sync index with:

```powershell
databricks vector-search-indexes get-index databricks_architect_agent.agent_demo.reviewed_architecture_knowledge --profile saket_dbx_dev --output json
```

Expected result: endpoint `solutions-architect-knowledge-vs` and a ready index status. Do not use the index for affirmative recommendations until retrieval is filtered to `review_status = REVIEWED`.

## 7. Test the custom MCP server

The custom MCP App is named `mcp-architect-knowledge`, is deployed, and is running. Its MCP endpoint is:

```text
https://mcp-architect-knowledge-1866518241053589.9.azure.databricksapps.com/mcp
```

Call `health` first. It must return `docs.databricks.com` as the only allowed documentation host and the governed icon Volume path. Then test `validate_architecture_diagram` with a JSON graph that uses `ai-search` or `genie-agents` as the icon name.

The `fetch_official_databricks_document` tool must reject non-HTTPS URLs and any host other than `docs.databricks.com`. A successful fetch returns `review_status = CANDIDATE`; it is not an approved architecture recommendation.

## 8. Confirm icon-aware artifacts

The current renderer job uses approved icons including `auto-loader`, `delta-lake`, `data-intelligence-platform`, `ai-search`, and `ai-bi-dashboards`. Confirm that the stored SVG contains the proposed architecture heading and embedded SVG image data:

```powershell
databricks fs cat dbfs:/Volumes/databricks_architect_agent/agent_demo/architecture_artifacts/demo_customer_360.svg --profile saket_dbx_dev
```

The archive and its extracted SVG source files are governed separately:

```text
/Volumes/databricks_architect_agent/agent_demo/architecture_icons/
```