# Governed tool contracts

| Tool | Access | Contract |
| --- | --- | --- |
| `find_reusable_assets` | Read-only UC function | Finds active assets matching a domain or serving need. |
| `downstream_impact` | Read-only UC function | Returns direct registered lineage consumers and source coverage note. |
| `summarize_cost_drivers` | Read-only UC function | Returns observed summarized cost and utilization signals. |
| `write_architecture_proposal` | Proposal-only workflow contract | Inserts an `architecture_proposal` record with `status = PENDING_APPROVAL`; no provisioning, permissions, or deployment actions. |
| `render_mermaid` | Local-only tool contract | Validates the supplied graph specification and renders Mermaid text. No external diagram API. |
| `draft_iac` | Review-workspace contract | Generates a draft outline only, stored with a `PENDING_APPROVAL` proposal. |

The proposed supervisor remains intentionally out of the baseline. Add it only after the single Genie agent passes the benchmark suite and each added tool has its own permission boundary.