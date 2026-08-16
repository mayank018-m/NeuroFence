import torch


class ActivationAnalyzer:

    def __init__(self, state_dict):
        self.state_dict = state_dict

    def analyze(self):

        results = []

        for name, tensor in self.state_dict.items():

            if not isinstance(tensor, torch.Tensor):
                continue

            tensor = tensor.detach().cpu().float()

            if tensor.numel() == 0:
                continue

            results.append({
                "name": name,
                "shape": list(tensor.shape),
                "mean": float(tensor.mean()),
                "std": float(tensor.std()),
                "min": float(tensor.min()),
                "max": float(tensor.max()),
                "max_abs": float(tensor.abs().max()),
                "finite": bool(
                    torch.isfinite(tensor).all()
                )
            })

        return results

    def find_anomalies(
        self,
        std_threshold=100.0,
        max_abs_threshold=10000.0
    ):

        anomalies = []

        for item in self.analyze():

            if not item["finite"]:

                anomalies.append({
                    "name": item["name"],
                    "reason": "Non-finite values",
                    "severity": "HIGH"
                })

            elif item["max_abs"] > max_abs_threshold:

                anomalies.append({
                    "name": item["name"],
                    "reason": "Extremely large values",
                    "severity": "HIGH"
                })

            elif item["std"] > std_threshold:

                anomalies.append({
                    "name": item["name"],
                    "reason": "Extremely high variance",
                    "severity": "MEDIUM"
                })

        return anomalies