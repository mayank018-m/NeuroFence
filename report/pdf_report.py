"""
report/pdf_report.py

Generates a forensic PDF summarizing a scan: model hash/metadata, the
inputs tested, the detection verdict/safety score, and a table of the top
flagged neurons with the prompts that triggered them.
"""

from __future__ import annotations

from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from detector.anomaly_detector import DetectionReport


VERDICT_COLORS = {
    "CLEAN": colors.HexColor("#1a7f37"),
    "SUSPICIOUS": colors.HexColor("#b08800"),
    "LIKELY_BACKDOORED": colors.HexColor("#c92a2a"),
}


def generate_pdf_report(
    metadata: dict,
    detection: DetectionReport,
    output_path: str,
):
    doc = SimpleDocTemplate(output_path, pagesize=LETTER, title="NeuroFence Forensic Report")
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "NFTitle", parent=styles["Title"], textColor=colors.HexColor("#1c2b4a")
    )
    verdict_style = ParagraphStyle(
        "NFVerdict",
        parent=styles["Heading1"],
        textColor=VERDICT_COLORS.get(detection.verdict, colors.black),
    )

    story = []
    story.append(Paragraph("NeuroFence Forensic Scan Report", title_style))
    story.append(Spacer(1, 0.15 * inch))
    story.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]
        )
    )
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph(f"Verdict: {detection.verdict}", verdict_style))
    story.append(Paragraph(f"Safety Score: {detection.safety_score} / 100", styles["Heading2"]))
    story.append(Spacer(1, 0.2 * inch))

    # -- Model metadata table -------------------------------------------
    story.append(Paragraph("Model Metadata", styles["Heading2"]))
    meta_rows = [
        ["Model name", metadata.get("model_name", "-")],
        ["Path", metadata.get("model_path", "-")],
        ["Parameters", f"{metadata.get('num_parameters', 0):,}"],
        ["Layers", str(metadata.get("num_layers", "-"))],
        ["Hidden size", str(metadata.get("hidden_size", "-"))],
        ["Dtype", metadata.get("dtype", "-")],
    ]
    hashes = metadata.get("weight_file_hashes", {})
    for fname, h in hashes.items():
        meta_rows.append([f"SHA-256 ({fname})", h])

    meta_table = Table(meta_rows, colWidths=[1.8 * inch, 4.7 * inch])
    meta_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef1f6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 0.25 * inch))

    # -- Scan summary ------------------------------------------------
    story.append(Paragraph("Scan Summary", styles["Heading2"]))
    story.append(
        Paragraph(
            f"Prompts tested: {detection.num_prompts_tested:,} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Neurons scanned: {detection.num_neurons_scanned:,} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Flagged neurons: {len(detection.anomalies)}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # -- Anomaly table -------------------------------------------------
    story.append(Paragraph("Top Flagged Neurons", styles["Heading2"]))
    header = ["Layer", "Neuron", "Max Z", "Selectivity", "Score", "Trigger-Correlated", "Example Prompt"]
    rows = [header]
    for a in detection.anomalies[:20]:
        example = (a.top_prompts[0][:40] + "...") if a.top_prompts and len(a.top_prompts[0]) > 40 else (a.top_prompts[0] if a.top_prompts else "-")
        rows.append(
            [
                a.layer,
                str(a.neuron_index),
                f"{a.max_z_score:.1f}",
                f"{a.selectivity * 100:.2f}%",
                f"{a.anomaly_score:.2f}",
                "YES" if a.trigger_correlated else "no",
                example,
            ]
        )

    anomaly_table = Table(rows, colWidths=[0.7 * inch, 0.6 * inch, 0.6 * inch, 0.8 * inch, 0.6 * inch, 1.0 * inch, 2.1 * inch])
    style_cmds = [
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1c2b4a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for i, a in enumerate(detection.anomalies[:20], start=1):
        if a.trigger_correlated:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#ffe3e3")))
    anomaly_table.setStyle(TableStyle(style_cmds))
    story.append(anomaly_table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(
        Paragraph(
            "Methodology: neurons were scored against a baseline activation distribution "
            "built from natural-language and random-noise prompts. Neurons that stay "
            "near-silent under normal traffic but spike sharply (high z-score) for a "
            "small, specific subset of inputs are flagged as dormant/sleeper candidates. "
            "Rows highlighted in red were driven predominantly by known trigger-style "
            "phrases and represent the strongest backdoor evidence.",
            styles["Italic"],
        )
    )

    doc.build(story)
    return output_path
