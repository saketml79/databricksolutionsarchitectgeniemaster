# Databricks notebook source
import base64
import hashlib
import html
import json
import os
import re
import struct
import uuid
import zipfile
import zlib

dbutils.widgets.text("catalog", "databricks_architect_agent")
dbutils.widgets.text("schema", "agent_demo")
dbutils.widgets.text("proposal_id", "")
dbutils.widgets.text("artifact_suffix", "")
dbutils.widgets.text("architecture_json", "")
dbutils.widgets.text("evidence_json", "{}")
catalog, schema = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")
proposal_id, raw_graph = dbutils.widgets.get("proposal_id").strip(), dbutils.widgets.get("architecture_json").strip()
artifact_suffix = dbutils.widgets.get("artifact_suffix").strip()
raw_evidence = dbutils.widgets.get("evidence_json").strip()
if not proposal_id or not raw_graph:
    raise ValueError("proposal_id and architecture_json are required")
graph = json.loads(raw_graph)
evidence = json.loads(raw_evidence or "{}")
if not isinstance(evidence, dict):
    raise ValueError("evidence_json must be a JSON object")
nodes, edges = graph.get("nodes"), graph.get("edges")
if not isinstance(nodes, list) or not isinstance(edges, list) or not nodes:
    raise ValueError("architecture_json must contain non-empty nodes and an edges array")
node_ids = set()
for node in nodes:
    if not isinstance(node, dict) or not re.fullmatch(r"[A-Za-z0-9_]{1,64}", str(node.get("id", ""))):
        raise ValueError("each node id must be 1-64 ASCII letters, digits, or underscores")
    node_ids.add(node["id"])
for edge in edges:
    if not isinstance(edge, dict) or edge.get("from") not in node_ids or edge.get("to") not in node_ids:
        raise ValueError("each edge must reference declared node ids")
mermaid = ["flowchart LR"] + [f"  {node['id']}[{str(node.get('label', node['id'])).replace('[', '(').replace(']', ')')}]" for node in nodes] + [f"  {edge['from']} --> {edge['to']}" for edge in edges]
mermaid_text = "\n".join(mermaid) + "\n"
icon_root = f"/Volumes/{catalog}/{schema}/architecture_icons"
icon_archive = f"{icon_root}/databricks-architecture-icons-all.zip"
if not os.path.exists(f"{icon_root}/icons/svg"):
    with zipfile.ZipFile(icon_archive) as archive:
        archive.extractall(icon_root)
def icon_image(icon_name, x_position, y_position, size=42):
    if not icon_name or not re.fullmatch(r"[a-z0-9-]+", str(icon_name)):
        return ""
    icon_path = f"{icon_root}/icons/svg/{icon_name}.svg"
    if not os.path.exists(icon_path):
        return ""
    with open(icon_path, "rb") as icon_file:
        encoded_icon = base64.b64encode(icon_file.read()).decode()
    return f"<image x='{x_position}' y='{y_position}' width='{size}' height='{size}' href='data:image/svg+xml;base64,{encoded_icon}'/>"

def label_markup(label, x_position, y_position):
    words, lines, current_line = str(label).split(), [], ""
    for word in words:
        next_line = f"{current_line} {word}".strip()
        if current_line and len(next_line) > 23:
            lines.append(current_line)
            current_line = word
        else:
            current_line = next_line
    if current_line:
        lines.append(current_line)
    return "".join(f"<tspan x='{x_position}' dy='{0 if index == 0 else 18}'>{html.escape(line)}</tspan>" for index, line in enumerate(lines))

card_width, card_height = 254, 138
levels = {node["id"]: 0 for node in nodes}
for _ in range(len(nodes)):
    changed = False
    for edge in edges:
        next_level = levels[edge["from"]] + 1
        if levels[edge["to"]] < next_level:
            levels[edge["to"]] = next_level
            changed = True
    if not changed:
        break
nodes_by_level = {}
for node in nodes:
    nodes_by_level.setdefault(levels[node["id"]], []).append(node)
maximum_level_size = max(len(level_nodes) for level_nodes in nodes_by_level.values())
positions = {}
if graph.get("layout") == "architecture" and {"landing", "silver", "gold", "search", "genie", "dashboard"}.issubset(node_ids):
    card_width, card_height = 224, 144
    canvas_width, canvas_height = 1440, 620
    positions = {
        "landing": (54, 238), "silver": (318, 238), "gold": (582, 238),
        "search": (886, 88), "genie": (886, 388), "dashboard": (1162, 238)
    }
else:
    canvas_width = max(900, 84 + (max(levels.values()) + 1) * 290)
    canvas_height = max(360, 154 + maximum_level_size * 170)
    for level, level_nodes in nodes_by_level.items():
        vertical_offset = 110 + (maximum_level_size - len(level_nodes)) * 85
        for index, node in enumerate(level_nodes):
            positions[node["id"]] = (42 + level * 290, vertical_offset + index * 170)
edge_paths = []
for edge in edges:
    source_x, source_y = positions[edge["from"]]
    target_x, target_y = positions[edge["to"]]
    if abs(source_x - target_x) < card_width / 2:
        source_center_x, source_center_y = source_x + card_width / 2, source_y + card_height
        target_center_x, target_center_y = target_x + card_width / 2, target_y
        control_y = (source_center_y + target_center_y) / 2
        edge_paths.append(f"<path d='M {source_center_x} {source_center_y} C {source_center_x} {control_y}, {target_center_x} {control_y}, {target_center_x} {target_center_y}' class='edge' marker-end='url(#architecture-arrow)'/>")
    else:
        source_center_x, source_center_y = source_x + card_width, source_y + card_height / 2
        target_center_x, target_center_y = target_x, target_y + card_height / 2
        control_x = (source_center_x + target_center_x) / 2
        edge_paths.append(f"<path d='M {source_center_x} {source_center_y} C {control_x} {source_center_y}, {control_x} {target_center_y}, {target_center_x} {target_center_y}' class='edge' marker-end='url(#architecture-arrow)'/>")
node_cards = []
for node in nodes:
    x_position, y_position = positions[node["id"]]
    label = label_markup(node.get("label", node["id"]), x_position + 20, y_position + 99)
    node_cards.append(f"<g class='node'><rect x='{x_position}' y='{y_position}' width='{card_width}' height='{card_height}' rx='12' class='node-card'/><rect x='{x_position}' y='{y_position}' width='7' height='{card_height}' rx='3' class='node-accent'/><rect x='{x_position + 19}' y='{y_position + 20}' width='48' height='48' rx='12' class='icon-tile'/>{icon_image(node.get('icon'), x_position + 23, y_position + 24, 40)}<text x='{x_position + 20}' y='{y_position + 99}' class='node-label'>{label}</text><text x='{x_position + 20}' y='{y_position + 126}' class='node-id'>{html.escape(node['id'])}</text></g>")
svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{canvas_width}' height='{canvas_height}' viewBox='0 0 {canvas_width} {canvas_height}'>
<defs><linearGradient id='surface' x1='0' y1='0' x2='1' y2='1'><stop stop-color='#f7fbf7'/><stop offset='1' stop-color='#e9f3f1'/></linearGradient><filter id='shadow' x='-20%' y='-20%' width='140%' height='140%'><feDropShadow dx='0' dy='6' stdDeviation='6' flood-color='#163b3f' flood-opacity='.18'/></filter><marker id='architecture-arrow' markerWidth='8' markerHeight='8' refX='7.4' refY='4' orient='auto' markerUnits='userSpaceOnUse'><path d='M1,1 L1,7 L7.4,4 z' fill='#126b62'/></marker><style>.node-card{{fill:#ffffff;stroke:#74a99f;stroke-width:2;filter:url(#shadow)}}.node-accent{{fill:#d8e96d}}.icon-tile{{fill:#eef7f4;stroke:#c8dfd8;stroke-width:1}}.edge{{fill:none;stroke:#126b62;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}}.node-label{{font-family:'Aptos Display','Helvetica Neue',Arial,sans-serif;font-size:15px;font-weight:800;fill:#153b3d}}.node-id{{font-family:Consolas,'Courier New',monospace;font-size:10px;fill:#5a7373;letter-spacing:.5px}}.title{{font-family:'Aptos Display','Helvetica Neue',Arial,sans-serif;font-size:15px;font-weight:800;letter-spacing:1.8px;fill:#126b62}}.subtitle{{font-family:'Aptos','Helvetica Neue',Arial,sans-serif;font-size:13px;fill:#5a7373}}</style></defs>
<rect width='100%' height='100%' fill='url(#surface)'/><path d='M0 82 H{canvas_width}' stroke='#c4d8d2' stroke-width='1'/><text x='42' y='38' class='title'>DATABRICKS SOLUTIONS ARCHITECT</text><text x='42' y='61' class='subtitle'>PROPOSED ARCHITECTURE | REVIEW REQUIRED</text>{''.join(edge_paths)}{''.join(node_cards)}</svg>"""
def png_chunk(kind, data): return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
width, height = 1, 1
png = b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + png_chunk(b"IDAT", zlib.compress(b"\x00\x13\x6f\x63")) + png_chunk(b"IEND", b"")
if artifact_suffix and not re.fullmatch(r"option_[1-3]", artifact_suffix):
    raise ValueError("artifact_suffix must be option_1, option_2, or option_3")
artifact_id, base_path = str(uuid.uuid4()), f"/Volumes/{catalog}/{schema}/architecture_artifacts/{proposal_id}{'_' + artifact_suffix if artifact_suffix else ''}"
dbutils.fs.put(f"{base_path}.mmd", mermaid_text, True)
dbutils.fs.put(f"{base_path}.svg", svg, True)
reference_manifest = json.dumps({"proposal_id": proposal_id, "artifact_status": "PROPOSED", "architecture_graph": graph, "evidence": evidence}, indent=2)
dbutils.fs.put(f"{base_path}.references.json", reference_manifest, True)
with open(f"{base_path}.png", "wb") as png_file:
    png_file.write(png)
escaped_proposal_id = proposal_id.replace("'", "''")
for artifact_type, suffix, content in [("MERMAID", "mmd", mermaid_text), ("SVG", "svg", svg), ("PNG", "png", png)]:
    content_hash = hashlib.sha256(content.encode() if isinstance(content, str) else content).hexdigest()
    spark.sql(f"INSERT INTO `{catalog}`.`{schema}`.diagram_artifact VALUES ('{artifact_id}_{artifact_type.lower()}', '{escaped_proposal_id}', '{artifact_type}', '{base_path}.{suffix}', '{content_hash}', 'PROPOSED', current_timestamp())")
dbutils.notebook.exit(f"Stored Mermaid, SVG, PNG, and evidence references at {base_path}.[mmd|svg|png|references.json].")