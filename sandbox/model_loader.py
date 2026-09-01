"""
sandbox/model_loader.py

Secure, offline-friendly loader for local LLMs.

Security posture:
- Refuses to load anything that isn't in safetensors format (no pickle / .bin
  torch.load, which can execute arbitrary code via __reduce__).
- Never sets trust_remote_code=True.
- Computes a SHA-256 hash of every weight file for forensic reporting/
  chain-of-custody purposes.
- Loads on CPU by default, in eval() mode, with gradients disabled, so the
  fuzzing pass can't accidentally mutate the model.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class UnsafeModelFormatError(Exception):
    """Raised when a model directory contains only unsafe (pickle) weights."""


@dataclass
class ModelMetadata:
    model_path: str
    model_name: str
    num_parameters: int
    num_layers: int
    hidden_size: int
    weight_file_hashes: dict = field(default_factory=dict)
    dtype: str = "unknown"
    device: str = "cpu"


class ModelSandbox:
    """
    Loads a local Hugging Face model directory in a locked-down way and
    exposes it (plus its tokenizer + metadata) for the fuzzer / hook layer.
    """

    def __init__(self, model_path: str, device: Optional[str] = None):
        self.model_path = Path(model_path)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self.metadata: Optional[ModelMetadata] = None

    # ------------------------------------------------------------------ #
    # Safety checks
    # ------------------------------------------------------------------ #
    def _verify_safe_format(self) -> list[Path]:
        """Ensure only .safetensors weight files are present/used."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model path does not exist: {self.model_path}")

        safetensor_files = sorted(self.model_path.glob("*.safetensors"))
        bin_files = sorted(self.model_path.glob("*.bin"))

        if not safetensor_files:
            raise UnsafeModelFormatError(
                "No .safetensors files found. NeuroFence refuses to load "
                "legacy .bin/pickle checkpoints, since torch.load() on a "
                "pickle file can execute arbitrary code embedded by an "
                "attacker. Convert the model to safetensors first "
                "(safetensors.torch.save_model) before scanning it."
            )

        if bin_files:
            print(
                f"[WARN] Found {len(bin_files)} .bin file(s) alongside "
                "safetensors weights. These will be IGNORED for safety; "
                "only .safetensors will be loaded."
            )

        return safetensor_files

    @staticmethod
    def _sha256_of_file(path: Path, chunk_size: int = 1 << 20) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                h.update(chunk)
        return h.hexdigest()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def load(self) -> "ModelSandbox":
        safetensor_files = self._verify_safe_format()

        weight_hashes = {
            f.name: self._sha256_of_file(f) for f in safetensor_files
        }

        # use_safetensors=True forces the safe loading path; trust_remote_code
        # is deliberately never set, which blocks custom model code execution.
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(self.model_path), use_fast=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            str(self.model_path),
            use_safetensors=True,
            torch_dtype=torch.float32,
        )
        self.model.to(self.device)
        self.model.eval()
        for p in self.model.parameters():
            p.requires_grad_(False)

        num_params = sum(p.numel() for p in self.model.parameters())
        config = self.model.config
        num_layers = getattr(config, "num_hidden_layers", None) or getattr(
            config, "n_layer", 0
        )
        hidden_size = getattr(config, "hidden_size", None) or getattr(
            config, "n_embd", 0
        )

        self.metadata = ModelMetadata(
            model_path=str(self.model_path),
            model_name=self.model_path.name,
            num_parameters=num_params,
            num_layers=num_layers,
            hidden_size=hidden_size,
            weight_file_hashes=weight_hashes,
            dtype=str(next(self.model.parameters()).dtype),
            device=self.device,
        )
        return self

    def metadata_dict(self) -> dict:
        if self.metadata is None:
            raise RuntimeError("Model not loaded yet. Call .load() first.")
        return {
            "model_path": self.metadata.model_path,
            "model_name": self.metadata.model_name,
            "num_parameters": self.metadata.num_parameters,
            "num_layers": self.metadata.num_layers,
            "hidden_size": self.metadata.hidden_size,
            "dtype": self.metadata.dtype,
            "device": self.metadata.device,
            "weight_file_hashes": self.metadata.weight_file_hashes,
        }

    def save_metadata_json(self, out_path: str):
        with open(out_path, "w") as f:
            json.dump(self.metadata_dict(), f, indent=2)
