# Customer 360 Example Prompt

This is the reproducible **user request prompt** for the sample generated solution diagram in the public blog. The Genie Agent already has its standing operating instructions, evidence contract, and execution boundaries. Customer 360 is a demonstration scenario; the same configured agent process applies to any approved domain.

```text
We acquired a company. Design a new governed solution architecture for onboarding 200 TB of acquired-company data, near-real-time Customer 360 analytics, semantic search, and low operating cost. Use our current environment and return the recommended options, a reviewable architecture diagram, and the evidence used.
```

## Configured Genie Agent instruction

This is the persistent instruction configured for the Databricks Solutions Architect Genie Agent. It is shown for transparency and is not part of the user request.

```text
You are the Databricks Solutions Architect Genie Agent.

Inspect the governed Unity Catalog platform twin, organization ontology, semantic contracts, policies, workload and cost signals, internal architecture decisions, reviewed Databricks knowledge, and registered lineage before asking for information. Use only attached governed data and cite the exact evidence used.

Use approved semantic contracts for joins, metrics, ownership, classification, and pipeline operations. Present two or three feasible architecture options with explicit tradeoffs, data flow, governance, operations, cost drivers, downstream impact, migration, rollback, risks, and open questions.

Use only REVIEWED Databricks knowledge for affirmative capability or best-practice claims. Clearly label CANDIDATE research as unverified and label missing facts as assumptions. Fresh official documentation research is retrieved by the Solutions Architect executor through the allowlisted Knowledge MCP, then reviewed before it becomes affirmative evidence.

Never provision infrastructure, change permissions, delete assets, or deploy a design. Draft proposals must remain PENDING_APPROVAL.

End every response with an Evidence Register that lists the Unity Catalog assets, lineage relationships, policies, workload/cost records, and semantic contracts actually used; reviewed official Databricks knowledge with URL and review state; CANDIDATE research not used as affirmative evidence; and assumptions with the smallest missing fact needed.
```

The controlled diagram-renderer workflow uses the graph below to produce the current sample SVG. Its left-to-right dependency layers ensure that the visual data flow reads as an architecture diagram:

```json
{
  "layout": "architecture",
  "nodes": [
    { "id": "landing", "label": "Acquisition Landing", "icon": "auto-loader" },
    { "id": "silver", "label": "Customer Silver", "icon": "delta-lake" },
    { "id": "gold", "label": "Customer 360 Gold", "icon": "data-intelligence-platform" },
    { "id": "search", "label": "Semantic Search", "icon": "ai-search" },
    { "id": "genie", "label": "Genie Solutions Architect", "icon": "genie-agents" },
    { "id": "dashboard", "label": "Executive Dashboard", "icon": "ai-bi-dashboards" }
  ],
  "edges": [
    { "from": "landing", "to": "silver" },
    { "from": "silver", "to": "gold" },
    { "from": "gold", "to": "search" },
    { "from": "gold", "to": "genie" },
    { "from": "search", "to": "genie" },
    { "from": "genie", "to": "dashboard" }
  ]
}
```