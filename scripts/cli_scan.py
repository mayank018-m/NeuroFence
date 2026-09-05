"""
scripts/cli_scan.py

Headless version of a NeuroFence scan — useful for CI pipelines or quick
terminal testing without launching the PyQt GUI.

Usage:
    python scripts/cli_scan.py --model ./models/backdoored-model --report ./reports/scan.pdf
"""

import argparse
import sys
from pathlib import Path

# Allow running this script directly from the scripts/ folder.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from detector.anomaly_detector import analyze
from report.pdf_report import generate_pdf_report
from sandbox.scan_runner import run_scan


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to local HF model directory")
    parser.add_argument("--report", default="./reports/neurofence_report.pdf")
    parser.add_argument("--n-baseline", type=int, default=300)
    parser.add_argument("--n-random", type=int, default=150)
    parser.add_argument("--n-edge-case", type=int, default=40)
    parser.add_argument(
        "--triggers",
        default="",
        help="Comma-separated list of extra suspected trigger words/phrases to test, "
             "e.g. --triggers \"Pineapple,ACTIVATE_NOW\"",
    )
    args = parser.parse_args()

    extra_triggers = [t.strip() for t in args.triggers.split(",") if t.strip()]

    def progress(done, total):
        pct = done / max(total, 1) * 100
        print(f"\rScanning: {done}/{total} ({pct:.0f}%)", end="", flush=True)

    print(f"Loading and scanning model at: {args.model}")
    result = run_scan(
        args.model,
        n_baseline=args.n_baseline,
        n_random=args.n_random,
        n_edge_case=args.n_edge_case,
        extra_trigger_words=extra_triggers,
        progress_cb=progress,
    )
    print()

    print("Running detector...")
    detection = analyze(result.records)

    print(f"\nVerdict: {detection.verdict}")
    print(f"Safety score: {detection.safety_score}/100")
    print(f"Flagged neurons: {len(detection.anomalies)}")
    for a in detection.anomalies[:10]:
        flag = "TRIGGER-CORRELATED" if a.trigger_correlated else ""
        print(
            f"  - {a.layer} neuron {a.neuron_index}: max_z={a.max_z_score:.1f} "
            f"selectivity={a.selectivity*100:.2f}% score={a.anomaly_score:.2f} {flag}"
        )

    out_path = Path(args.report)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    generate_pdf_report(result.metadata, detection, str(out_path))
    print(f"\nReport saved to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
