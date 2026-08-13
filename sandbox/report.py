"""
report.py
---------
Week 4 deliverable: Automated PDF security report generation.
Summarizes: model hash, prompts tested, anomalies found, safety score.
"""

from datetime import datetime
from fpdf import FPDF


def generate_pdf_report(output_path, model_path, sha256, safety_score, results):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "NeuroFence Forensic Security Report", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Generated: {datetime.now().isoformat(timespec='seconds')}", ln=True)
    pdf.cell(0, 8, f"Model path: {model_path}", ln=True)
    pdf.multi_cell(0, 8, f"SHA-256 (weights): {sha256}")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, f"Safety Score: {safety_score} / 100", ln=True)
    pdf.ln(2)

    total_anomalies = sum(len(v) for v in results.values())
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Total anomalous neurons flagged: {total_anomalies}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Findings by layer:", ln=True)
    pdf.set_font("Helvetica", "", 10)

    if total_anomalies == 0:
        pdf.multi_cell(0, 7, "No statistically significant dormant/trigger-reactive neurons "
                              "were detected across the tested prompt set.")
    else:
        for layer, anomalies in results.items():
            if not anomalies:
                continue
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, f"Layer: {layer}", ln=True)
            pdf.set_font("Helvetica", "", 9)
            for a in anomalies:
                pdf.multi_cell(
                    0, 6,
                    f"  Neuron #{a.neuron_index} | z-score: {a.z_score:.2f} | "
                    f"baseline energy: {a.baseline_mean:.4f} | trigger energy: {a.trigger_energy:.4f}\n"
                    f"  Example triggering prompt(s): {a.triggering_prompts[:2]}"
                )
            pdf.ln(2)

    pdf.output(output_path)
