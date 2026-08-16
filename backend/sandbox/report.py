import json
from pathlib import Path
from datetime import datetime


class ReportGenerator:

    def __init__(self, output_directory="reports"):

        self.output_directory = Path(
            output_directory
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True
        )

    def create_report(
        self,
        model_path,
        inspection,
        detection,
        activation_analysis,
        activation_anomalies
    ):

        return {
            "project": "NeuroFence",
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "model": {
                "path": str(model_path),
                "filename": Path(
                    model_path
                ).name
            },
            "inspection": inspection,
            "detection": detection,
            "activation_analysis": activation_analysis,
            "activation_anomalies": activation_anomalies
        }

    def save_json(
        self,
        report,
        filename="neurofence_report.json"
    ):

        path = self.output_directory / filename

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                report,
                file,
                indent=4
            )

        return path

    def save_text(
        self,
        report,
        filename="neurofence_report.txt"
    ):

        path = self.output_directory / filename

        detection = report["detection"]

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                "================================\n"
            )

            file.write(
                "        NEUROFENCE REPORT\n"
            )

            file.write(
                "================================\n\n"
            )

            file.write(
                f"Model: "
                f"{report['model']['filename']}\n"
            )

            file.write(
                f"Risk Score: "
                f"{detection['risk_score']}/100\n"
            )

            file.write(
                f"Risk Level: "
                f"{detection['risk_level']}\n"
            )

            file.write(
                f"Findings: "
                f"{detection['finding_count']}\n\n"
            )

            file.write(
                "Findings:\n"
            )

            for finding in detection["findings"]:
                file.write(
                    f"- {finding}\n"
                )

        return path