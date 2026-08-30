# Databricks Solutions Architect

This project builds a governed **Databricks Solutions Architect** system. It analyzes a current-state digital twin, recommends two or three solution options, records only reviewable proposals, and renders architecture artifacts. It does not provision infrastructure, delete data, change permissions, or deploy a recommended design.

Solutions architecture connects a business need to a feasible technical design across data, AI, applications, governance, operating ownership, cost, migration, and rollback. The Databricks Solutions Architect Genie Agent grounds that work in governed workspace evidence. Its companion Knowledge MCP reads allowlisted official `docs.databricks.com` public internet articles and release guidance, then routes them through candidate and human-review stages so only `REVIEWED` Databricks knowledge supports affirmative capability and best-practice recommendations.

## User surfaces

| Surface | Purpose | Current deployment |
| --- | --- | --- |
| Databricks Solutions Architect Genie Agent | Primary governed reasoning layer for evidence-grounded questions over platform and semantic data | Genie space `01f1a400577d1c71b8b1fd2d83cc2df5` on `lab-warehouse` |
| Databricks Solutions Architect App | Review workspace that links users to Genie, proposal workflow, and artifact location | `enterprise-architect` Databricks App |
| Solutions Architect Knowledge MCP | Bounded retrieval of official Databricks documentation and diagram specification validation | `mcp-architect-knowledge` custom MCP App is deployed |

## What is governed

- The digital twin holds assets, lineage, ownership, classification, policy, workload, cost, observation, and proposal evidence.
- Semantic contracts define approved tables/views, column meaning, sensitivity, joins, metrics, and pipelines.
- New discovered data products start as `CANDIDATE`. Only complete `APPROVED` products are synchronized to Genie.
- Documentation retrieval is restricted to `https://docs.databricks.com`. Retrieved content is `CANDIDATE` evidence until a human reviews it.
- Every generated proposal is `PENDING_APPROVAL`; every diagram artifact is `PROPOSED`.
- Mermaid, SVG, and PNG are stored in the governed `architecture_artifacts` Volume. Approved Databricks diagram icons are stored separately in `architecture_icons`.

Start with [Building a Governed Databricks Solutions Architect](04-building-a-governed-solutions-architect.md) for a concise product overview and presentation assets. The locally viewable SVG infographics are in [infographics](infographics). Read [01-system-architecture.md](01-system-architecture.md) for the full topology, [02-semantic-control-loop.md](02-semantic-control-loop.md) for the enrollment model, and [03-test-runbook.md](03-test-runbook.md) for the executable tests.

Read [06-current-implementation-decisions.md](06-current-implementation-decisions.md) before changing the App, request executor, diagram renderer, option review workflow, or Genie instructions. It is the current operational decision record.