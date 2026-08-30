# Databricks notebook source
import base64
import hashlib
import os
import uuid

dbutils.widgets.text("catalog", "databricks_architect_agent")
dbutils.widgets.text("schema", "agent_demo")
catalog, schema = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")
if not catalog.replace("_", "").isalnum() or not schema.replace("_", "").isalnum():
    raise ValueError("catalog and schema must contain only letters, digits, and underscores")

icon_root = f"/Volumes/{catalog}/{schema}/architecture_icons/icons/svg"
artifact_root = f"/Volumes/{catalog}/{schema}/architecture_artifacts"

def icon(name, x_position, y_position, size=34):
    icon_path = f"{icon_root}/{name}.svg"
    if not os.path.exists(icon_path):
        return ""
    with open(icon_path, "rb") as icon_file:
        payload = base64.b64encode(icon_file.read()).decode()
    return f"<image x='{x_position}' y='{y_position}' width='{size}' height='{size}' href='data:image/svg+xml;base64,{payload}'/>"

def write_artifact(name, content):
    path = f"{artifact_root}/{name}.svg"
    dbutils.fs.put(path, content, True)
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    artifact_id = str(uuid.uuid4())
    spark.sql(f"""INSERT INTO `{catalog}`.`{schema}`.diagram_artifact VALUES
      ('{artifact_id}', 'solutions_architect_infographic', 'SVG_INFOGRAPHIC', '{path}', '{content_hash}', 'PROPOSED', current_timestamp())""")

def svg_document(width, height, body):
    return f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>
<defs>
  <linearGradient id='paper' x1='0' y1='0' x2='1' y2='1'><stop stop-color='#fbfdf9'/><stop offset='1' stop-color='#e7f1ed'/></linearGradient>
  <linearGradient id='band' x1='0' y1='0' x2='1' y2='0'><stop stop-color='#0d514f'/><stop offset='1' stop-color='#16766b'/></linearGradient>
  <filter id='lift' x='-20%' y='-20%' width='140%' height='140%'><feDropShadow dx='0' dy='9' stdDeviation='11' flood-color='#0a2d31' flood-opacity='.15'/></filter>
  <filter id='soft' x='-20%' y='-20%' width='140%' height='140%'><feDropShadow dx='0' dy='4' stdDeviation='4' flood-color='#0a2d31' flood-opacity='.11'/></filter>
    <style>.kicker{{font:800 12px 'Aptos Display','Helvetica Neue',Arial,sans-serif;letter-spacing:2.5px;fill:#72ddc2}}.title{{font:800 48px 'Aptos Display','Helvetica Neue',Arial,sans-serif;letter-spacing:-1px;fill:#fff}}.subtitle{{font:400 19px 'Aptos','Helvetica Neue',Arial,sans-serif;fill:#cce7df}}.card-title{{font:800 19px 'Aptos Display','Helvetica Neue',Arial,sans-serif;fill:#133a3d}}.body{{font:400 14px 'Aptos','Helvetica Neue',Arial,sans-serif;fill:#557174}}.metric{{font:800 31px 'Aptos Display','Helvetica Neue',Arial,sans-serif;fill:#113f41}}.metric-label{{font:700 11px Consolas,'Courier New',monospace;letter-spacing:1.35px;fill:#678184}}.footer{{font:400 11px Consolas,'Courier New',monospace;letter-spacing:.3px;fill:#6d8585}}.section{{font:800 12px 'Aptos Display','Helvetica Neue',Arial,sans-serif;letter-spacing:1.8px;fill:#16766b}}</style>
</defs>
<rect width='100%' height='100%' fill='url(#paper)'/>{body}</svg>"""

def flow_infographic(name, title, subtitle, steps, footer):
    width, height = 1440, 700
    card_width = 286 if len(steps) <= 4 else 220
    gap = (width - 120 - card_width * len(steps)) / max(1, len(steps) - 1)
    colors = ["#e57c59", "#3978a9", "#d8e96d", "#126b62", "#7b67a8"]
    cards, arrows = [], []
    for index, (heading, detail, icon_name) in enumerate(steps):
        x_position, y_position = 60 + index * (card_width + gap), 304
        cards.append(f"<g filter='url(#soft)'><rect x='{x_position}' y='{y_position}' width='{card_width}' height='224' rx='16' fill='#fff'/><rect x='{x_position}' y='{y_position}' width='{card_width}' height='9' rx='4' fill='{colors[index % len(colors)]}'/>{icon(icon_name, x_position + 28, y_position + 35, 44)}<text x='{x_position + 28}' y='{y_position + 112}' class='card-title'>{heading}</text><text x='{x_position + 28}' y='{y_position + 145}' class='body'>{detail}</text></g>")
        if index < len(steps) - 1:
            arrow_start = x_position + card_width + 10
            arrow_end = x_position + card_width + gap - 12
            arrows.append(f"<path d='M{arrow_start} 416 H{arrow_end}' fill='none' stroke='#2c7b73' stroke-width='4' stroke-linecap='round'/><path d='M{arrow_end - 9} 406 L{arrow_end + 9} 416 L{arrow_end - 9} 426' fill='none' stroke='#2c7b73' stroke-width='4'/>")
    content = f"<rect width='{width}' height='222' fill='url(#band)'/><path d='M0 222 C270 177 525 281 770 222 S1190 177 1440 218 V0 H0Z' fill='#0a4545' opacity='.24'/><text x='62' y='65' class='kicker'>DATABRICKS SOLUTIONS ARCHITECT</text><text x='58' y='125' class='title'>{title}</text><text x='62' y='165' class='subtitle'>{subtitle}</text><text x='60' y='260' class='section'>GOVERNED FLOW</text>{''.join(arrows)}{''.join(cards)}<text x='60' y='638' class='footer'>{footer}</text>"
    write_artifact(name, svg_document(width, height, content))

product_infographic = svg_document(1440, 900, f"""
<rect width='1440' height='274' fill='url(#band)'/><path d='M0 274 C300 218 490 338 760 275 S1180 205 1440 270 V0 H0Z' fill='#0a4545' opacity='.24'/>
<text x='86' y='76' class='kicker'>GOVERNED ARCHITECTURE INTELLIGENCE</text><text x='82' y='140' class='title'>GENIE SOLUTIONS ARCHITECT</text><text x='86' y='181' class='subtitle'>Keeps design decisions grounded in the platform you already have.</text>
<g filter='url(#lift)'><rect x='1002' y='54' width='330' height='152' rx='18' fill='#dbe976'/><text x='1032' y='104' class='metric'>MULTI-DOMAIN</text><text x='1032' y='130' class='metric-label'>GOVERNED ARCHITECTURE CONTEXT</text><text x='1032' y='165' class='body'>Assets, policies, lineage, workloads,<tspan x='1032' dy='19'>cost, knowledge, and demo scenarios.</tspan></text></g>
<text x='84' y='341' class='section'>HOW A REQUIREMENT BECOMES A REVIEWABLE DESIGN</text>
<g filter='url(#soft)'><rect x='58' y='374' width='290' height='288' rx='16' fill='#fff'/><rect x='58' y='374' width='290' height='9' rx='4' fill='#e57c59'/>{icon('genie-agents',88,414,48)}<text x='88' y='491' class='card-title'>1. Ask in plain language</text><text x='88' y='523' class='body'>Submit a change request through Genie<tspan x='88' dy='21'>or the Solutions Architect App.</tspan></text></g>
<path d='M359 517 H388' stroke='#2c7b73' stroke-width='4' stroke-linecap='round'/><path d='M382 507 L400 517 L382 527' fill='none' stroke='#2c7b73' stroke-width='4'/>
<g filter='url(#soft)'><rect x='405' y='374' width='290' height='288' rx='16' fill='#fff'/><rect x='405' y='374' width='290' height='9' rx='4' fill='#3978a9'/>{icon('data-lineage',435,414,48)}<text x='435' y='491' class='card-title'>2. Inspect real evidence</text><text x='435' y='523' class='body'>Assess assets, ownership, policies,<tspan x='435' dy='21'>lineage, cost, and operating signals.</tspan></text></g>
<path d='M706 517 H735' stroke='#2c7b73' stroke-width='4' stroke-linecap='round'/><path d='M729 507 L747 517 L729 527' fill='none' stroke='#2c7b73' stroke-width='4'/>
<g filter='url(#soft)'><rect x='752' y='374' width='290' height='288' rx='16' fill='#fff'/><rect x='752' y='374' width='290' height='9' rx='4' fill='#d8e96d'/>{icon('ai-search',782,414,48)}<text x='782' y='491' class='card-title'>3. Compare options</text><text x='782' y='523' class='body'>Use reviewed product knowledge and<tspan x='782' dy='21'>make tradeoffs explicit.</tspan></text></g>
<path d='M1053 517 H1082' stroke='#2c7b73' stroke-width='4' stroke-linecap='round'/><path d='M1076 507 L1094 517 L1076 527' fill='none' stroke='#2c7b73' stroke-width='4'/>
<g filter='url(#soft)'><rect x='1099' y='374' width='290' height='288' rx='16' fill='#fff'/><rect x='1099' y='374' width='290' height='9' rx='4' fill='#126b62'/>{icon('databricks-apps',1129,414,48)}<text x='1129' y='491' class='card-title'>4. Review</text><text x='1129' y='516' class='card-title'>proposal</text><text x='1129' y='551' class='body'>Inspect and approve<tspan x='1129' dy='21'>the next step.</tspan></text></g>
<rect x='82' y='724' width='1276' height='92' rx='14' fill='#143f42'/><text x='114' y='763' class='kicker'>THE SAFETY PROMISE</text><text x='114' y='793' class='subtitle'>Design outputs stay PENDING_APPROVAL. The system plans, explains, and visualizes. Humans decide what executes.</text><text x='84' y='862' class='footer'>DATABRICKS SOLUTIONS ARCHITECT | GOVERNED DIGITAL TWIN | REVIEWABLE BY DESIGN</text>""")

executive_brief = svg_document(1080, 1400, f"""
<rect x='48' y='44' width='984' height='1312' rx='8' fill='#fff' filter='url(#lift)'/><rect x='48' y='44' width='984' height='194' rx='8' fill='url(#band)'/>
<text x='98' y='95' class='kicker'>EXECUTIVE BRIEF</text><text x='94' y='153' class='title'>GENIE SOLUTIONS ARCHITECT</text><text x='98' y='190' class='subtitle'>A governed way to move from change request to decision.</text>
<text x='94' y='303' class='section'>THE IDEA</text><text x='94' y='350' class='metric'>Architecture that starts with facts.</text><text x='94' y='387' class='body'>Instead of designing from a blank canvas, the agent checks the governed platform<tspan x='94' dy='22'>twin: data products, dependencies, ownership, policies, operating signals, and cost.</tspan></text>
<line x1='94' y1='447' x2='986' y2='447' stroke='#d2dfda'/><text x='94' y='492' class='section'>WHAT IT KEEPS IN VIEW</text>
<g transform='translate(94,530)'>{icon('data-lineage',0,0,42)}<text x='60' y='19' class='card-title'>Platform reality</text><text x='60' y='43' class='body'>Assets, data flows, and downstream impacts.</text></g>
<g transform='translate(94,618)'>{icon('enterprise-security',0,0,42)}<text x='60' y='19' class='card-title'>Governance</text><text x='60' y='43' class='body'>Ownership, classification, policy, and approval boundaries.</text></g>
<g transform='translate(94,706)'>{icon('ai-search',0,0,42)}<text x='60' y='19' class='card-title'>Current knowledge</text><text x='60' y='43' class='body'>Official documentation enters as candidate evidence before review.</text></g>
<g transform='translate(94,794)'>{icon('data-warehousing',0,0,42)}<text x='60' y='19' class='card-title'>Operations and cost</text><text x='60' y='43' class='body'>Pipelines, freshness, workload signals, and cost drivers.</text></g>
<rect x='94' y='895' width='892' height='256' rx='14' fill='#e8f4f0'/><text x='132' y='947' class='section'>THE REVIEW PACKAGE</text><text x='132' y='994' class='card-title'>Every recommendation becomes an inspectable record.</text><text x='132' y='1032' class='body'>Two or three options. Explicit tradeoffs. Migration and rollback steps.<tspan x='132' dy='22'>A draft IaC outline. Mermaid, SVG, and PNG diagrams. All marked for review.</tspan></text><rect x='132' y='1090' width='280' height='34' rx='17' fill='#d8e96d'/><text x='151' y='1113' class='metric-label'>PENDING_APPROVAL BY DEFAULT</text>
<text x='94' y='1235' class='section'>THE OUTCOME</text><text x='94' y='1283' class='metric'>Faster decisions. Better questions. Clearer accountability.</text><text x='94' y='1322' class='footer'>DATABRICKS SOLUTIONS ARCHITECT | FOR REVIEW, NOT AUTOMATIC EXECUTION</text>""")

governance_loop = svg_document(1200, 900, f"""
<rect width='1200' height='900' fill='#f7fbf8'/><rect x='0' y='0' width='1200' height='176' fill='url(#band)'/><text x='64' y='59' class='kicker'>A CONTROLLED FEEDBACK LOOP</text><text x='60' y='118' class='title'>GENIE SOLUTIONS ARCHITECT KEEPS</text><text x='64' y='151' class='subtitle'>context current, recommendations grounded, and execution reviewable.</text>
<circle cx='600' cy='537' r='203' fill='#e6f2ed' stroke='#b7d4ca' stroke-width='2'/><circle cx='600' cy='537' r='110' fill='#143f42' filter='url(#lift)'/>{icon('genie-agents',564,470,72)}<text x='600' y='570' text-anchor='middle' style='font:700 18px Arial,sans-serif;fill:#fff'>GROUNDED</text><text x='600' y='594' text-anchor='middle' style='font:400 13px Arial,sans-serif;fill:#cce7df'>design reasoning</text>
<g filter='url(#soft)'><rect x='87' y='380' width='246' height='150' rx='16' fill='#fff'/>{icon('data-lineage',117,411,38)}<text x='117' y='475' class='card-title'>Discover</text><text x='117' y='501' class='body'>Inventory assets, flows,<tspan x='117' dy='18'>workloads, and costs.</tspan></text></g>
<g filter='url(#soft)'><rect x='867' y='380' width='246' height='150' rx='16' fill='#fff'/>{icon('enterprise-security',897,411,38)}<text x='897' y='475' class='card-title'>Govern</text><text x='897' y='501' class='body'>Apply ownership, policy,<tspan x='897' dy='18'>and semantic contracts.</tspan></text></g>
<g filter='url(#soft)'><rect x='172' y='665' width='246' height='150' rx='16' fill='#fff'/>{icon('ai-search',202,696,38)}<text x='202' y='760' class='card-title'>Enrich</text><text x='202' y='786' class='body'>Review current product<tspan x='202' dy='18'>knowledge and limits.</tspan></text></g>
<g filter='url(#soft)'><rect x='782' y='665' width='246' height='150' rx='16' fill='#fff'/>{icon('databricks-apps',812,696,38)}<text x='812' y='760' class='card-title'>Review</text><text x='812' y='786' class='body'>Compare options and<tspan x='812' dy='18'>approve the next step.</tspan></text></g>
<path d='M333 454 C390 350 462 324 506 363' fill='none' stroke='#2c7b73' stroke-width='4' marker-end='url(#arrow)'/><path d='M694 363 C759 324 831 350 867 454' fill='none' stroke='#2c7b73' stroke-width='4' marker-end='url(#arrow)'/><path d='M986 530 C1016 595 959 655 900 680' fill='none' stroke='#2c7b73' stroke-width='4' marker-end='url(#arrow)'/><path d='M300 680 C241 655 184 595 214 530' fill='none' stroke='#2c7b73' stroke-width='4' marker-end='url(#arrow)'/>
<defs><marker id='arrow' markerWidth='10' markerHeight='10' refX='8' refY='3' orient='auto'><path d='M0,0 L0,6 L9,3 z' fill='#2c7b73'/></marker></defs><text x='60' y='860' class='footer'>AUTOMATION PREPARES CONTEXT. PEOPLE RETAIN APPROVAL AUTHORITY.</text>""")

write_artifact("genie_solutions_architect_infographic", product_infographic)
write_artifact("genie_solutions_architect_executive_brief", executive_brief)
write_artifact("genie_solutions_architect_governance_loop", governance_loop)
flow_infographic("solutions_architect_request_to_review", "FROM REQUEST TO REVIEW", "The Genie Agent turns platform evidence into a reviewable decision.", [
    ("Ask", "Submit a business requirement.", "genie-agents"),
    ("Ground", "Inspect governed platform evidence.", "data-lineage"),
    ("Compare", "Make options and tradeoffs explicit.", "ai-search"),
    ("Review", "Keep the proposal approval-gated.", "databricks-apps")
], "EVIDENCE FIRST | OPTIONS EXPLAINED | HUMANS RETAIN APPROVAL")
flow_infographic("solutions_architect_system_topology", "THE SOLUTIONS ARCHITECT SYSTEM", "A practical set of governed components, each with a clear role.", [
    ("Users", "Ask and review through Databricks.", "databricks-apps"),
    ("Genie Agent", "Answers from governed context.", "genie-agents"),
    ("Knowledge MCP", "Reads approved official sources.", "ai-search"),
    ("Review artifacts", "Stores proposals and diagrams.", "delta-lake")
], "DATABRICKS APP | GENIE AGENT | MCP TOOLS | UNITY CATALOG")
flow_infographic("solutions_architect_governed_resources", "WHAT THE AGENT CAN SEE", "A governed digital twin connects data reality to architectural reasoning.", [
    ("Platform twin", "Assets, lineage, policy, cost.", "data-lineage"),
    ("Semantic layer", "Meaning, joins, and certified metrics.", "data-intelligence-platform"),
    ("POS demo", "A test scenario with real contracts.", "delta-lake"),
    ("Review package", "Proposals and diagrams in a Volume.", "databricks-apps")
], "ONLY APPROVED, DESCRIBED, CLASSIFIED DATA PRODUCTS REACH GENIE")
flow_infographic("solutions_architect_artifact_flow", "HOW A DIAGRAM IS PRODUCED", "A design stays inspectable from architecture graph to governed file.", [
    ("Specify", "Describe nodes, edges, and icons.", "agent-bricks"),
    ("Validate", "Check bounded graph rules.", "enterprise-security"),
    ("Render", "Create Mermaid, SVG, and PNG.", "ai-bi"),
    ("Store", "Write PROPOSED artifacts to UC.", "delta-lake")
], "APPROVED ICONS | VALIDATED GRAPH | GOVERNED VOLUME | REVIEW REQUIRED")
flow_infographic("solutions_architect_semantic_enrollment", "CONTEXT WITH A GOVERNANCE GATE", "Automation discovers new data, but only complete products reach Genie.", [
    ("Discover", "Find a new table, view, or pipeline.", "data-lineage"),
    ("Candidate", "Hold incomplete context for review.", "enterprise-security"),
    ("Enrich", "Add owner, meaning, and contracts.", "data-intelligence-platform"),
    ("Approve", "Synchronize trusted context to Genie.", "genie-agents")
], "NO SILENT DATA EXPOSURE | SEMANTIC CONTEXT IS AN APPROVAL DECISION")
flow_infographic("solutions_architect_retail_semantics", "RETAIL POS DEMO, MADE UNDERSTANDABLE", "A validation scenario proves the domain-agnostic pattern with a usable model, not just column names.", [
    ("POS sales", "Transaction-level sales facts.", "delta-lake"),
    ("Dimensions", "Stores, products, and segments.", "data-intelligence-platform"),
    ("Certified views", "Daily and category sales metrics.", "ai-bi-dashboards"),
    ("Design input", "Grounded retail architecture options.", "genie-agents")
], "DEMONSTRATION SCENARIO | APPROVED JOINS | CERTIFIED METRICS | REUSABLE PATTERN")
flow_infographic("solutions_architect_knowledge_lifecycle", "CURRENT KNOWLEDGE, CLEARLY LABELED", "Official product guidance becomes design evidence only after review.", [
    ("Official docs", "Allowlisted Databricks sources.", "document-intelligence"),
    ("Candidate", "Capture source, date, and content hash.", "ai-search"),
    ("Review", "Validate scope, capability, and limits.", "enterprise-security"),
    ("Reviewed", "Use as cited architecture evidence.", "genie-agents")
], "SOURCE-CITED | VERSIONED | REVIEWED BEFORE AFFIRMATIVE CLAIMS")
dbutils.notebook.exit(f"Stored ten Genie Solutions Architect infographic SVGs in {artifact_root}.")