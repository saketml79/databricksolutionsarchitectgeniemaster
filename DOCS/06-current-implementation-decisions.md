# Current Implementation Decisions

This is the operational decision record for the Databricks Solutions Architect Genie system. Read it before changing the App, request executor, diagram renderer, review workflow, or Genie instructions.

## User Experience

- Genie is the evidence-grounded conversation surface. Its native visuals are SQL-result visualizations; it does not render custom SVG architecture artifacts.
- The Databricks App is the governed proposal-review surface. It renders proposal-specific SVGs inline through authenticated routes and exposes PDF/SVG/PNG actions.
- The App response panel has a bounded scroll area and preserves the complete streamed agent response, including the final artifact statement. Agent prose is rendered with `react-markdown` plus `remark-gfm`; every adjacent `| |` table-row boundary is normalized to a physical newline before rendering as a recovery path.
- While a request is active, the response panel visibly identifies the current Genie SA Agent stage: grounding with Genie, awaiting artifact approval, or rendering governed artifacts.
- The complete streamed agent response is persisted as `FULL_ARCHITECTURE_RESPONSE` in `architecture_conversation` after a successful review-package tool result.

## Proposal And Diagram Contract

- New proposals use the `_v2` identifier suffix to avoid reuse of historical fixed-template artifacts.
- Each explicit App Generate action supplies a unique request nonce, creating a distinct pending proposal even when its text matches an earlier reviewed request. Direct executor runs without a nonce remain idempotent.
- `generate_review_package` requires exactly three graphs: `option_1`, `option_2`, and `option_3`.
- The agent must call `generate_review_package` before writing its user-facing analysis. This reserves model output for complete tool-call JSON and prevents a long narrative from truncating the option-graph payload.
- Each graph must have 4-6 nodes, directed edges, node labels, and approved Databricks icon names.
- The executor validates and renders each graph separately as `<proposal>_option_1.svg`, `<proposal>_option_2.svg`, and `<proposal>_option_3.svg`, with matching Mermaid and PNG artifacts.
- Historical proposals without `_v2` remain visible as historical records and retain their original single diagram.

## Decision Model

- `architecture_option_decision` is the durable option-review table. Each v2 proposal creates three `PENDING_APPROVAL` rows.
- Rejecting an option changes only that option to `REJECTED`; remaining options stay reviewable.
- Approving one option changes it to `APPROVED`, changes siblings to `REJECTED_NOT_SELECTED`, and changes the parent proposal to `APPROVED`.
- If all options are rejected, the parent proposal changes to `REJECTED`.
- Active review shows only parent proposals with `PENDING_APPROVAL`. Approved and rejected proposals are available through the archive view. An archived approved proposal displays only its selected option SVG.
- Decisions record review state only. They never deploy, provision, delete, or change permissions.

## Identity And Access

- Review-package queries and option decisions use the browser request's `x-forwarded-access-token` through a request-scoped `WorkspaceClient` and Databricks SQL Statement Execution API.
- This is direct OBO behavior: Unity Catalog applies the requesting user's privileges, not the App service principal's privileges.
- The App resource manifest grants the service principal `CAN_USE` on warehouse `e3a0fc2c08db05bb` and `READ_VOLUME` on `databricks_architect_agent.agent_demo.architecture_artifacts` for guarded artifact delivery.
- Do not return to `appkit.analytics.asUser(request).query(...)`: AppKit `0.57.0` loses Analytics plugin method context on that proxy path.

## Current Deployments

- App bundle: `app/enterprise-architect`, deployed with `databricks bundle deploy --profile saket_dbx_dev`.
- Root governed bundle: repository root, target `dev`, deployed with `databricks bundle deploy -t dev --profile saket_dbx_dev`.
- Genie space: `01f1a400577d1c71b8b1fd2d83cc2df5`.
- Request executor Job: `527763870636434`.
- Governed AI/BI topology dashboard: `Databricks Solutions Architect - Architecture Topology`.

## Required Validation

1. `npm run typecheck` from `app/enterprise-architect`.
2. `databricks bundle validate --profile saket_dbx_dev` from `app/enterprise-architect`.
3. `databricks bundle validate -t dev --profile saket_dbx_dev` from the repository root.
4. Deploy the root bundle before the App when changing executor/schema contracts.