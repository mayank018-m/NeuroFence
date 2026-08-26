"""
scripts/download_test_model.py

One-time helper: downloads a small open-source causal LM (default:
'sshleifer/tiny-gpt2', ~a few MB, good for fast local testing) and saves it
to disk in safetensors format so NeuroFence's loader (which refuses .bin
pickle files) can use it.

For a more realistic ~1B parameter test, pass --model with something like
'TinyLlama/TinyLlama-1.1B-Chat-v1.0' (requires a real GPU or patience on CPU,
and several GB of disk space).

Usage:
    python scripts/download_test_model.py --model sshleifer/tiny-gpt2 --out ./models/clean-model
"""

import argparse
from pathlib import Path

from transformers import AutoModelForCausalLM, AutoTokenizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="sshleifer/tiny-gpt2")
    parser.add_argument("--out", default="./models/clean-model")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {args.model} ...")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model)

    print(f"Saving to {out_dir} as safetensors ...")
    model.save_pretrained(out_dir, safe_serialization=True)
    tokenizer.save_pretrained(out_dir)

    print("Done. You can now point NeuroFence at:", out_dir.resolve())


if __name__ == "__main__":
    main()
