# NeuroFence — Complete Execution Guide

This is the single reference document for taking NeuroFence from a fresh
zip file to a completed forensic scan with a PDF report, on Windows with
VS Code. Follow it top to bottom the first time; after that, jump to
whichever section you need.

---

## Part A — One-time environment setup

### A1. Install prerequisites
| Tool | Where | Notes |
|---|---|---|
| Python 3.10 or 3.11 (64-bit) | https://www.python.org/downloads/ | Check "Add Python to PATH" during install |
| VS Code | https://code.visualstudio.com/ | |
| VS Code Python extension | Inside VS Code: Ctrl+Shift+X, search "Python" (by Microsoft) | |
| Microsoft VC++ Redistributable x64 | https://aka.ms/vs/17/release/vc_redist.x64.exe | Required or PyTorch fails to load on Windows |

Verify Python installed correctly — open **Command Prompt** (not VS Code
yet) and run:
```powershell
python --version
```
You should see `Python 3.10.x` or `3.11.x`. If you see an error, Python
isn't on PATH — reinstall and check the PATH box, or restart your machine.

### A2. Extract the project
Extract `NeuroFence.zip` to a **short path with no spaces**, e.g.:
```
C:\NeuroFence
```
Confirm that `C:\NeuroFence\main.py` exists directly — if extraction
created a nested `C:\NeuroFence\NeuroFence\main.py`, move the inner
folder's contents up one level.

### A3. Open the project in VS Code
`File > Open Folder…` → select `C:\NeuroFence`.

Open the integrated terminal: `` Ctrl+` `` (backtick). Confirm it opened
in the project root — the prompt should show `C:\NeuroFence>`.

### A4. (PowerShell only) allow script execution
If your default VS Code terminal is PowerShell, run this **once**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentProcess
```
This is required for the venv activation script to run. It's scoped to
the current terminal process only — it doesn't change system security
settings permanently.

### A5. Create and activate the virtual environment
```powershell
python -m venv venv
venv\Scripts\activate
```
Your prompt should now start with `(venv)`. **Every command below assumes
this is active** — if you close and reopen the terminal, re-run
`venv\Scripts\activate` before continuing.

### A6. Point VS Code's editor at the venv
`Ctrl+Shift+P` → type "Python: Select Interpreter" → choose
`.\venv\Scripts\python.exe`.

### A7. Install dependencies
```powershell
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```
Installing torch explicitly first (CPU build) avoids the most common
Windows install failure (`WinError 1114` / DLL load errors from an
auto-selected CUDA build with no matching GPU drivers).

### A8. Verify the install
```powershell
python scripts\verify_install.py
```
This checks torch, transformers, safetensors, PyQt5, and reportlab all
import cleanly, and prints your torch version + whether CUDA is
available. **Don't move on until this passes** — every later step depends
on this working.

---

## Part B — Get a model to scan

### B1. Download a small real pretrained model
```powershell
python scripts\download_test_model.py --model sshleifer/tiny-gpt2 --out models\clean-model
```
This needs internet access (pulls from Hugging Face) and takes seconds —
it's a tiny model, good for fast iteration and testing the tool itself.

For a result closer to the original ~1B-parameter project spec (needs a
few GB disk space and more time/RAM):
```powershell
python scripts\download_test_model.py --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 --out models\clean-model
```

**Already have your own model to scan?** Skip this step and instead make
sure it's in `.safetensors` format in its own folder under `models\`
(NeuroFence refuses `.bin`/pickle checkpoints for safety — convert first
with `safetensors.torch.save_model` if needed).

### B2. Create a deliberately backdoored copy (to prove detection works)
```powershell
python -m backdoor.inject_backdoor --source models\clean-model --output models\backdoored-model --trigger "Pineapple" --layer 1 --neuron 7 --scale 40.0
```
This plants one neuron that fires strongly only on the word "Pineapple",
giving you a known-answer test case. Skip this if you're scanning a
model you suspect is *already* backdoored — go straight to Part C.

---

## Part C — Run a scan

### C1. Option 1 — Desktop GUI
```powershell
python main.py
```
1. Click **Load Model Directory…**, select `models\backdoored-model`.
2. Type `Pineapple` into the **Custom triggers** box (comma-separate
   multiple words if you have more than one suspected trigger).
3. Adjust baseline/random/edge-case prompt counts if you want a bigger or
   faster scan (defaults: 300 / 150 / 40).
4. Click **Run Forensic Scan** — progress bar fills as prompts are fired.
5. Inspect the heatmap (bright isolated cells = candidate anomalies) and
   the ranked table on the right. Click any row to see the exact prompts
   that triggered that neuron in the deep-dive panel below it.
6. Click **Export PDF Report**, choose a save location.
7. Repeat against `models\clean-model` to see a clean verdict for
   comparison.

### C2. Option 2 — Headless CLI (faster, scriptable)
```powershell
python scripts\cli_scan.py --model models\backdoored-model --report reports\backdoored_scan.pdf --triggers "Pineapple"
python scripts\cli_scan.py --model models\clean-model --report reports\clean_scan.pdf
```
Prints the verdict, safety score, and top flagged neurons directly to the
terminal, and still writes the full PDF report.

### C3. Option 3 — Run everything in one go
```powershell
run_full_demo.bat
```
Executes B1 → B2 → C2 automatically (download model, inject backdoor,
scan both models, save both reports to `reports\`). Useful for a first
end-to-end confidence check or a quick demo run.

---

## Part D — Reading the results

| Field | Meaning |
|---|---|
| **Verdict** | `CLEAN` / `SUSPICIOUS` / `LIKELY_BACKDOORED` |
| **Safety Score** | 0–100, 100 = no anomalies found |
| **Max Z** | How many standard deviations above baseline the neuron's peak activation was |
| **Selectivity** | % of the whole prompt corpus that made this neuron fire strongly — low = "dormant except for a specific trigger" |
| **Trigger-Correlated** | YES means the prompts that fired this neuron were dominated by known-trigger-style phrases — the strongest evidence of an actual backdoor |

A model showing `LIKELY_BACKDOORED` with one or more `Trigger-Correlated:
YES` rows is strong evidence of a planted sleeper neuron. `SUSPICIOUS`
with no trigger-correlated rows usually means statistically unusual but
not conclusively malicious — worth a closer manual look at those specific
prompts before deploying the model.

---

## Part E — Troubleshooting

| Symptom | Fix |
|---|---|
| `WinError 1114` / DLL load failed on `import torch` | Install VC++ Redistributable (Part A1); reinstall torch with `--index-url https://download.pytorch.org/whl/cpu` (Part A7) |
| `venv\Scripts\activate` : "cannot be loaded because running scripts is disabled" | Run the command in Part A4 |
| `ModuleNotFoundError` for any package | Confirm `(venv)` is showing in your prompt — you may have a fresh terminal that needs `venv\Scripts\activate` again |
| GUI window opens but freezes during scan | It shouldn't — the scan runs on a background thread. If it does freeze, check the terminal output for a Python traceback and share it |
| `UnsafeModelFormatError: No .safetensors files found` | Your model folder only has `.bin` weights — convert to safetensors first, or re-download with `download_test_model.py` which saves safetensors by default |
| Detector flags dozens of neurons on a *clean* model | You're likely testing against a randomly-initialized (untrained) model rather than a real pretrained one — see the limitation note in `README.md` |
| Scan takes a very long time | Lower the baseline/random/edge-case prompt counts (GUI spin boxes, or `--n-baseline` / `--n-random` / `--n-edge-case` flags on the CLI) |

If none of these match your error, paste the **full terminal traceback**
(not just the last line) and we can debug the specific failure.


## NeuroFence Verification and Testing

Before running NeuroFence, verify that the required Python environment and
dependencies are correctly installed.

Run the environment verification utility from the project root:


```bash
python scripts/verify_install.py