import sys

from backend.sandbox.model_loader import ModelLoader
from backend.sandbox.model_sandbox import ModelSandbox
from backend.sandbox.detector import BackdoorDetector
from backend.activations.activation_analyzer import ActivationAnalyzer
from backend.sandbox.report import ReportGenerator


def main():

    if len(sys.argv) < 2:

        print(
            "Usage: python main.py <model_path>"
        )

        return 1

    model_path = sys.argv[1]

    print()
    print("==========================================")
    print("              NEUROFENCE")
    print("      AI MODEL SECURITY SCANNER")
    print("==========================================")
    print()

    print("[*] Loading model...")

    loader = ModelLoader(model_path)

    try:
        state_dict = loader.load_state_dict()

    except Exception as error:

        print(
            f"[!] Error loading model: {error}"
        )

        return 1

    print(
        f"[+] Loaded {len(state_dict)} tensors"
    )

    print()
    print("[*] Running sandbox inspection...")

    sandbox = ModelSandbox(
        state_dict
    )

    inspection = sandbox.inspect()

    print(
        f"[+] Tensor count: "
        f"{inspection['tensor_count']}"
    )

    print(
        f"[+] Parameters: "
        f"{inspection['total_parameters']}"
    )

    print()
    print("[*] Running activation analysis...")

    analyzer = ActivationAnalyzer(
        state_dict
    )

    activation_analysis = (
        analyzer.analyze()
    )

    activation_anomalies = (
        analyzer.find_anomalies()
    )

    print(
        f"[+] Activation anomalies: "
        f"{len(activation_anomalies)}"
    )

    print()
    print("[*] Running backdoor detection...")

    detector = BackdoorDetector(
        state_dict
    )

    detection = detector.scan()

    print(
        f"[+] Risk Score: "
        f"{detection['risk_score']}/100"
    )

    print(
        f"[+] Risk Level: "
        f"{detection['risk_level']}"
    )

    if detection["findings"]:

        print()
        print("[!] Findings:")

        for finding in detection["findings"]:
            print(
                "   - "
                + str(finding)
            )

    else:

        print(
            "[+] No suspicious indicators detected."
        )

    print()
    print("[*] Creating report...")

    generator = ReportGenerator()

    report = generator.create_report(
        model_path,
        inspection,
        detection,
        activation_analysis,
        activation_anomalies
    )

    json_path = generator.save_json(
        report
    )

    text_path = generator.save_text(
        report
    )

    print(
        f"[+] JSON report: {json_path}"
    )

    print(
        f"[+] Text report: {text_path}"
    )

    print()
    print("==========================================")
    print("       NEUROFENCE SCAN COMPLETE")
    print("==========================================")

    return 0


if __name__ == "__main__":
    sys.exit(main())