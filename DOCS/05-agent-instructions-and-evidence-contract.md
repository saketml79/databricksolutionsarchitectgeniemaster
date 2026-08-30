# Agent Instructions And Evidence Contract

## Two different inputs

The Customer 360 text in the blog is a **user request prompt**. It describes one desired outcome: onboarding acquired-company data, near-real-time analytics, semantic search, and controlled cost. Users replace that text with their own change request.

The **Databricks Solutions Architect Genie Agent instructions** are different. They are the persistent operating rules configured in the Genie space. They require the agent to inspect governed Unity Catalog evidence before asking questions, use approved semantic contracts for joins and metrics, present alternatives with tradeoffs, avoid execution, and expose its evidence in every response.

When the user works directly in the Genie UI, Genie can use only its attached governed Unity Catalog context and reviewed knowledge. When a request needs fresh official Databricks research, it is sent through the Databricks Solutions Architect executor, which calls the scoped Genie Agent and the Knowledge MCP. The Knowledge MCP may read only allowlisted `docs.databricks.com` sources. Fresh web material is `CANDIDATE`; it does not become an affirmative recommendation until a reviewer promotes the relevant claim to `REVIEWED`.

## Required final response shape

Every Solutions Architect output must end with an **Evidence Register**. This is how a reviewer knows whether the architecture was grounded in organization context rather than invented.

```text
Evidence Register

Unity Catalog organization evidence
- Assets: asset IDs and full names used
- Lineage: relationship IDs, direction, source note, and observation time
- Governance: policy IDs, owner, and enforcement boundary
- Operations and cost: workload/cost record IDs, observation time, and signal
- Semantic contracts: data-product, column, join, metric, or pipeline contract IDs used

Reviewed official Databricks knowledge
- Knowledge ID, canonical URL, publication/retrieval date, review state, cloud/region scope, and limitation

Candidate research
- Canonical URL and retrieval date, explicitly labeled CANDIDATE and not used as affirmative evidence

Assumptions and unknowns
- Each missing fact, why it matters, and the smallest fact needed to resolve it
```

Each architecture option must cite its evidence inline as well. An option cannot be recommended solely from `CANDIDATE` research. If Unity Catalog evidence was not available, the agent must say so rather than implying that it inspected it.