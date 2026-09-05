"""
scripts/verify_install.py

Run this right after `pip install -r requirements.txt` to confirm every
dependency actually imports and works before you try the full app. Prints
clear pass/fail per package instead of one confusing traceback, and tells
you exactly which one to fix if something's broken.

Usage:
    python scripts\\verify_install.py
"""

import sys


def check(name, import_fn):
    try:
        result = import_fn()
        print(f"[OK]   {name}" + (f"  ({result})" if result else ""))
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] {name}  ->  {exc}")
        return False


def main():
    print(f"Python: {sys.version}\n")
    all_ok = True

    def check_torch():
        import torch
        cuda = "CUDA available" if torch.cuda.is_available() else "CPU only"
        return f"v{torch.__version__}, {cuda}"

    def check_transformers():
        import transformers
        return f"v{transformers.__version__}"

    def check_safetensors():
        import safetensors
        return f"v{safetensors.__version__}"

    def check_pyqt5():
        from PyQt5.QtCore import QT_VERSION_STR
        return f"Qt v{QT_VERSION_STR}"

    def check_pyqtgraph():
        import pyqtgraph
        return f"v{pyqtgraph.__version__}"

    def check_reportlab():
        import reportlab
        return f"v{reportlab.Version}"

    def check_numpy():
        import numpy
        return f"v{numpy.__version__}"

    checks = [
        ("PyTorch", check_torch),
        ("Transformers (HuggingFace)", check_transformers),
        ("safetensors", check_safetensors),
        ("PyQt5", check_pyqt5),
        ("pyqtgraph", check_pyqtgraph),
        ("reportlab", check_reportlab),
        ("numpy", check_numpy),
    ]

    for name, fn in checks:
        ok = check(name, fn)
        all_ok = all_ok and ok

    print()
    if all_ok:
        print("All dependencies OK. You're ready to run: python main.py")
    else:
        print(
            "One or more dependencies failed to import. Fix the FAILED "
            "line(s) above before running the app -- see EXECUTION_GUIDE.md "
            "Part E (Troubleshooting) for common fixes."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
