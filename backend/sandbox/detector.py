import re
import torch


class BackdoorDetector:

    SUSPICIOUS_KEYWORDS = [
        "trigger",
        "backdoor",
        "poison",
        "trojan",
        "payload",
        "implant",
        "malicious",
        "secret",
        "override",
        "inject",
        "hidden"
    ]

    def __init__(self, state_dict):
        self.state_dict = state_dict

    def scan_parameter_names(self):

        findings = []

        for name in self.state_dict:

            name_lower = str(name).lower()

            matches = []

            for keyword in self.SUSPICIOUS_KEYWORDS:
                if keyword in name_lower:
                    matches.append(keyword)

            if matches:
                findings.append({
                    "type": "suspicious_parameter_name",
                    "parameter": name,
                    "keywords": matches,
                    "severity": "MEDIUM"
                })

        return findings

    def scan_tensor_values(self):

        findings = []

        for name, tensor in self.state_dict.items():

            if not isinstance(tensor, torch.Tensor):
                continue

            tensor = tensor.detach().cpu().float()

            if tensor.numel() == 0:
                continue

            if not torch.isfinite(tensor).all():

                findings.append({
                    "type": "non_finite_tensor",
                    "parameter": name,
                    "severity": "HIGH"
                })

                continue

            max_abs = float(tensor.abs().max())
            std = float(tensor.std())

            if max_abs > 10000:

                findings.append({
                    "type": "extreme_weight",
                    "parameter": name,
                    "max_absolute_value": max_abs,
                    "severity": "HIGH"
                })

            elif std > 100:

                findings.append({
                    "type": "high_weight_variance",
                    "parameter": name,
                    "std": std,
                    "severity": "MEDIUM"
                })

        return findings

    def scan(self):

        findings = []

        findings.extend(
            self.scan_parameter_names()
        )

        findings.extend(
            self.scan_tensor_values()
        )

        score = self.calculate_score(findings)

        return {
            "risk_score": score,
            "risk_level": self.get_risk_level(score),
            "finding_count": len(findings),
            "findings": findings
        }

    @staticmethod
    def calculate_score(findings):

        score = 0

        severity_points = {
            "LOW": 5,
            "MEDIUM": 15,
            "HIGH": 30,
            "CRITICAL": 50
        }

        for finding in findings:

            severity = finding.get(
                "severity",
                "LOW"
            ).upper()

            score += severity_points.get(
                severity,
                5
            )

        return min(score, 100)

    @staticmethod
    def get_risk_level(score):

        if score >= 70:
            return "CRITICAL"

        if score >= 40:
            return "HIGH"

        if score >= 20:
            return "MEDIUM"

        return "LOW"


def scan_text_for_triggers(text):

    patterns = [
        r"\bactivate\b",
        r"\btrigger\b",
        r"\bbackdoor\b",
        r"\bsecret phrase\b",
        r"\boverride\b",
        r"\bignore previous\b"
    ]

    findings = []

    for pattern in patterns:

        if re.search(
            pattern,
            text,
            re.IGNORECASE
        ):
            findings.append({
                "pattern": pattern,
                "matched": True
            })

    return findings