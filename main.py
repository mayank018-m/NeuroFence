"""
NeuroFence entry point.

Run:
    python main.py

Opens the desktop forensic application. From there:
  1. Click "Load Model Directory…" and select a local Hugging Face model
     folder (must contain .safetensors weights + tokenizer files).
  2. Click "Run Forensic Scan" to fuzz the model and record neuron
     activations.
  3. Inspect the heatmap + flagged neuron table, then "Export PDF Report".
"""
import torch

from gui.main_window import main


if __name__ == "__main__":
    main()