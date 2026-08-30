# Databricks notebook source
import base64
import json
import os
import subprocess
import sys
import textwrap

dbutils.widgets.text("catalog", "databricks_architect_agent")
dbutils.widgets.text("schema", "agent_demo")
dbutils.widgets.text("proposal_id", "")
catalog, schema = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")
proposal_id = dbutils.widgets.get("proposal_id").strip()
if not proposal_id:
    raise ValueError("proposal_id is required")
escaped_proposal_id = proposal_id.replace("'", "''")
proposal = spark.sql(f"SELECT title, recommendation, status, evidence_json, migration_plan_json, draft_iac_json FROM `{catalog}`.`{schema}`.architecture_proposal WHERE proposal_id = '{escaped_proposal_id}'").collect()
if len(proposal) != 1:
    raise ValueError("proposal was not found")
record = proposal[0].asDict()
root = f"/Volumes/{catalog}/{schema}/architecture_artifacts/{proposal_id}"
option_svg_paths = [f"{root}_option_{index}.svg" for index in range(1, 4)]
svg_path, png_path, evidence_path, pdf_path = option_svg_paths[0], f"{root}_option_1.png", f"{root}.references.json", f"{root}.pdf"
if not all(os.path.exists(path) for path in option_svg_paths) or not os.path.exists(png_path) or not os.path.exists(evidence_path):
    raise ValueError("proposal diagram artifacts and evidence manifest must exist before creating a review package")

with open(png_path, "rb") as png_file:
    encoded_png = base64.b64encode(png_file.read()).decode()
with open(evidence_path, "r", encoding="utf-8") as evidence_file:
    manifest = json.load(evidence_file)
evidence_text = json.dumps(manifest.get("evidence", {}), indent=2)
html = f"""<!doctype html><html><head><meta charset='utf-8'><style>@page{{size:A4;margin:18mm}}body{{font-family:Arial,sans-serif;color:#173b3d}}h1{{font-size:26px;margin:0}}h2{{font-size:15px;margin-top:24px;color:#126b62}}.status{{display:inline-block;margin:12px 0;padding:6px 10px;background:#dbe976;font-weight:bold}}img{{width:100%;border:1px solid #b8d2ca}}pre{{white-space:pre-wrap;background:#f1f7f4;padding:12px;font-size:9px}}.footer{{margin-top:22px;color:#607b7b;font-size:10px}}</style></head><body><h1>Databricks Solutions Architect</h1><p>{record['title']}</p><div class='status'>{record['status']}</div><h2>Recommendation</h2><p>{record['recommendation']}</p><h2>Generated architecture diagram</h2><img src='data:image/png;base64,{encoded_png}' alt='Generated architecture diagram'><h2>Evidence register</h2><pre>{evidence_text}</pre><h2>Migration sequence</h2><pre>{record['migration_plan_json']}</pre><h2>Draft IaC outline</h2><pre>{record['draft_iac_json']}</pre><p class='footer'>Review package only. No infrastructure was provisioned, altered, or deployed.</p></body></html>"""
dbutils.fs.put(f"{root}.review.html", html, True)
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "reportlab", "svglib"])
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF
try:
    drawing = svg2rlg(svg_path)
    if drawing is None:
        raise ValueError("stored SVG could not be converted to a PDF drawing")
    page_width, page_height = A4
    pdf_canvas = canvas.Canvas(pdf_path, pagesize=A4)
    pdf_canvas.setTitle(record["title"])
    pdf_canvas.setFont("Helvetica-Bold", 18)
    pdf_canvas.setFillColor("#173b3d")
    pdf_canvas.drawString(42, page_height - 48, "Databricks Solutions Architect")
    pdf_canvas.setFont("Helvetica", 11)
    pdf_canvas.drawString(42, page_height - 66, record["title"][:110])
    pdf_canvas.setFillColor("#126b62")
    pdf_canvas.setFont("Helvetica-Bold", 10)
    pdf_canvas.drawString(42, page_height - 84, f"STATUS: {record['status']} | REVIEW PACKAGE")
    scale = min((page_width - 84) / drawing.width, 260 / drawing.height)
    pdf_canvas.saveState()
    pdf_canvas.translate(42, page_height - 360)
    pdf_canvas.scale(scale, scale)
    renderPDF.draw(drawing, pdf_canvas, 0, 0)
    pdf_canvas.restoreState()
    pdf_canvas.setFillColor("#173b3d")
    pdf_canvas.setFont("Helvetica-Bold", 11)
    pdf_canvas.drawString(42, page_height - 390, "Recommendation")
    pdf_canvas.setFont("Helvetica", 9)
    text = pdf_canvas.beginText(42, page_height - 406)
    text.setLeading(12)
    for word in record["recommendation"].split():
        line = text.getX() and word
        if text.getX() > page_width - 105:
            text.textLine()
        text.textOut(word + " ")
    pdf_canvas.drawText(text)
    for option_index, option_svg_path in enumerate(option_svg_paths[1:], start=2):
        option_drawing = svg2rlg(option_svg_path)
        if option_drawing is None:
            raise ValueError(f"stored option {option_index} SVG could not be converted to a PDF drawing")
        pdf_canvas.showPage()
        pdf_canvas.setFont("Helvetica-Bold", 14)
        pdf_canvas.setFillColor("#173b3d")
        pdf_canvas.drawString(42, page_height - 48, f"Architecture option {option_index}")
        option_scale = min((page_width - 84) / option_drawing.width, (page_height - 120) / option_drawing.height)
        pdf_canvas.saveState()
        pdf_canvas.translate(42, page_height - 90 - option_drawing.height * option_scale)
        pdf_canvas.scale(option_scale, option_scale)
        renderPDF.draw(option_drawing, pdf_canvas, 0, 0)
        pdf_canvas.restoreState()
    response_rows = spark.sql(f"""SELECT content FROM `{catalog}`.`{schema}`.architecture_conversation
    WHERE request_id = '{escaped_proposal_id}' AND content_type = 'FULL_ARCHITECTURE_RESPONSE'
    ORDER BY created_at DESC LIMIT 1""").collect()
    if response_rows:
        pdf_canvas.showPage()
        pdf_canvas.setFont("Helvetica-Bold", 14)
        pdf_canvas.setFillColor("#173b3d")
        pdf_canvas.drawString(42, page_height - 48, "Native Genie response")
        text = pdf_canvas.beginText(42, page_height - 70)
        text.setFont("Helvetica", 8)
        text.setLeading(11)
        for source_line in response_rows[0].content.splitlines() or [response_rows[0].content]:
            for wrapped_line in textwrap.wrap(source_line, width=120) or [""]:
                if text.getY() < 50:
                    pdf_canvas.drawText(text)
                    pdf_canvas.showPage()
                    text = pdf_canvas.beginText(42, page_height - 48)
                    text.setFont("Helvetica", 8)
                    text.setLeading(11)
                text.textLine(wrapped_line)
        pdf_canvas.drawText(text)
    pdf_canvas.setFont("Helvetica", 8)
    pdf_canvas.setFillColor("#607b7b")
    pdf_canvas.drawString(42, 34, "Evidence manifest, migration sequence, and draft IaC are stored with this package. No infrastructure action was performed.")
    pdf_canvas.save()
except Exception as error:
    raise RuntimeError(f"PDF generation failed; review HTML was retained at {root}.review.html: {str(error)[:500]}")
spark.sql(f"""UPDATE `{catalog}`.`{schema}`.architecture_review_package
SET pdf_path = '{pdf_path}', package_status = 'READY_FOR_REVIEW'
WHERE proposal_id = '{escaped_proposal_id}'""")
dbutils.notebook.exit(json.dumps({"proposal_id": proposal_id, "status": "READY_FOR_REVIEW", "pdf_path": pdf_path, "svg_path": svg_path, "png_path": png_path, "evidence_manifest_path": evidence_path}))