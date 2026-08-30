# Databricks Solutions Architect

This Databricks Asset Bundle deploys a governed, read-model digital twin and controlled workflows for the Databricks Solutions Architect Genie baseline. The runtime is analysis and planning only: no infrastructure provisioning, permission changes, or destructive actions are included.

## Deploy

1. Validate the bundle: `databricks bundle validate -t dev`
2. Deploy workspace files and workflow: `databricks bundle deploy -t dev --profile saket_dbx_dev`
3. Seed the twin: `databricks bundle run enterprise_architect_bootstrap -t dev --profile saket_dbx_dev`
4. The live `Databricks Solutions Architect Genie` space is bound to `lab-warehouse` and attaches every deployed governed table and view in `databricks_architect_agent.agent_demo`.

Run `benchmarks/architecture_agent_benchmarks.sql` on a SQL warehouse after bootstrap. The expected results demonstrate reusable customer assets, dashboard/API impact, observed cost drivers, and active PII/retention constraints.

## Governed runtime

The deployed workflows are deliberately separated by permission and lifecycle:

| Workflow | Schedule | Purpose |
| --- | --- | --- |
| `dev-enterprise-architect-platform-refresh` | Every 6 hours | Read-only collection of Unity Catalog inventory and approved system-schema telemetry. Failed source access is stored as an `UNAVAILABLE` observation, never bypassed. |
| `dev-enterprise-architect-knowledge-stage` | Daily | Stages a fixed, approved Databricks documentation feed as `CANDIDATE` knowledge. |
| `dev-solutions-architect-request-executor` | On demand | Records the request, complete Genie response, and evidence trail; creates a `PENDING_APPROVAL` proposal with exactly three independently reviewable architecture options. |
| `dev-enterprise-architect-diagram-renderer` | On demand | Validates each bounded option graph and writes option-specific Mermaid, SVG, and PNG review artifacts. |
| `dev-solutions-architect-review-package` | On demand | Renders the governed SVG into a PDF review package with proposal status and evidence register. |
| `dev-solutions-architect-proposal-decision` | On demand | Historical proposal-level decision workflow. New App proposals use option-level decisions and never execute infrastructure. |

`promote_knowledge_review.py` is intentionally not scheduled. A reviewer must explicitly supply a candidate `knowledge_id` and reviewer identifier before a fact can become `REVIEWED` and support affirmative architecture claims.

## User interfaces

- **Genie:** `Databricks Solutions Architect Genie Agent` is the grounded natural-language analysis surface over synchronized governed context.
- **Databricks App:** `Databricks Solutions Architect Genie` is a live review workspace backed by direct OBO SQL. Each review query uses the requesting browser user's forwarded OAuth token, so Unity Catalog evaluates that user's own privileges.
- **Artifacts:** Every new proposal contains exactly three agent-provided, option-specific Mermaid, SVG, and PNG artifacts in `/Volumes/databricks_architect_agent/agent_demo/architecture_artifacts`. The App renders authenticated SVG previews instead of presenting Volume paths.

The app and workflows do not automatically read arbitrary notebooks, repositories, or web pages. The platform refresh records declared workspace artifacts as manifest-only evidence and records unavailable live source access. Broader code collection or documentation ingestion requires a separately approved workspace/repository or web connection and an explicit policy review.

## Semantic control loop

The digital twin now includes a tested retail POS demonstration workload in `databricks_architect_agent.retail_pos`: three dimensions, POS transaction facts, and two certified metric views. It is a seeded acceptance-test domain, not a product restriction. Each approved domain follows the same governed semantic pattern: Unity Catalog descriptions plus column descriptions and roles, sensitivity, approved joins, certified metric expressions and grain, and pipeline contracts.

`dev-enterprise-architect-semantic-discovery` runs every six hours. It discovers objects in the approved `retail_pos` scope and creates only `CANDIDATE` contracts for objects without complete semantic metadata. `dev-enterprise-architect-genie-sync` follows it and automatically attaches the core governance objects plus only data products that are `APPROVED`, Genie-eligible, classified, owned, and described. This prevents new unclassified tables, views, or pipelines from becoming available to Genie without review.

The repeatable user acceptance prompt is in `genie/test_prompts.md`. Its focused validation passed against the live space: six approved retail products, three certified metrics, approved product/store joins, the active `retail-pos-ingestion` pipeline on a 15-minute schedule, and the non-PII classification all returned from governed contracts.

## Architecture knowledge MCP and diagrams

`mcp-architect-knowledge` is a running custom Databricks App that exposes the Databricks Solutions Architect Knowledge MCP endpoint at `https://mcp-architect-knowledge-1866518241053589.9.azure.databricksapps.com/mcp`. It provides bounded official-document retrieval from `docs.databricks.com` as `CANDIDATE` evidence and validates architecture graph specifications before they are rendered by the controlled diagram workflow.

The dedicated `solutions-architect-knowledge-vs` endpoint hosts the hybrid Delta Sync index `databricks_architect_agent.agent_demo.reviewed_architecture_knowledge` over the Change-Data-Feed-enabled knowledge chunks. It is used only with a `REVIEWED` knowledge-state filter.

The supplied Databricks architecture icon archive is stored in the managed `architecture_icons` Volume. The diagram renderer extracts approved SVG icons from that Volume and embeds them in `PROPOSED` SVG artifacts, alongside Mermaid and PNG files in `architecture_artifacts`. Complete diagrams and testing instructions are in `DOCS/`.

## Production request workflow

`dev-solutions-architect-request-executor` is the approval-gated path from a user request to a review package. It persists the complete streamed Genie answer as `FULL_ARCHITECTURE_RESPONSE`, records request and evidence trail, then creates a `_v2` `PENDING_APPROVAL` proposal containing `option_1`, `option_2`, and `option_3`. The three option graphs are separately validated and rendered as governed artifacts.

Each option has a durable row in `architecture_option_decision`. Rejecting an option keeps the others reviewable. Approving an option archives siblings as `REJECTED_NOT_SELECTED`, promotes the parent proposal to `APPROVED`, and retains only the selected SVG in the archive view. No decision executes infrastructure. The daily knowledge job fetches only active patterns in `knowledge_source_allowlist`, versions official source content by hash, chunks it, and stages it as `CANDIDATE`; `promote_knowledge_review.py` promotes a reviewed item and its chunks to `REVIEWED`.

## Proposal rule

The only permitted workflow writes are governed requests, evidence, proposals, diagram/review artifacts, knowledge-review records, and explicit review decisions. New proposals start as `PENDING_APPROVAL`; approval changes only the proposal status and never executes infrastructure. Human review is required before any execution outside this bundle.