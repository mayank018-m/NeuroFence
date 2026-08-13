"""
model_sandbox.py
-----------------
Week 1 deliverable: Secure local loading of an open-source LLM +
PyTorch forward hooks that record activation energy per layer.

Design notes:
- We NEVER call model.generate() with remote code execution enabled.
  trust_remote_code is hard-locked to False so a malicious repo can't
  ship a custom modeling_*.py that runs arbitrary Python on load.
- We only read .safetensors weights (safetensors format cannot execute
  code on load, unlike raw pickled .bin/.pt files). We refuse to load
  models that only ship as .bin/.pt to avoid deserialization RCE.
- Hooks are registered on every nn.Linear / nn.LayerNorm / attention
  block inside the transformer stack so we get full-layer coverage.
"""

from __future__ import annotations
import os
import glob
import hashlib
import torch
import torch.nn as nn
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ActivationRecord:
    """One capture of a layer's activation stats for one prompt."""
    layer_name: str
    prompt: str
    mean_energy: float           # mean |activation|
    max_energy: float            # max |activation|
    per_neuron_energy: torch.Tensor  # (hidden_dim,) L2 energy per neuron


class ModelSandbox:
    """
    Loads a HuggingFace causal LM locally and exposes a hooked
    forward pass that records per-layer / per-neuron activation energy.
    """

    def __init__(self, model_path: str, device: str = "cpu"):
        self.model_path = model_path
        self.device = device
        self.model = None
        self.tokenizer = None
        self._hooks = []
        self._capture_buffer: Dict[str, torch.Tensor] = {}
        self.sha256 = self._hash_model_dir(model_path) if os.path.isdir(model_path) else None

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def _hash_model_dir(self, path: str) -> str:
        """Cryptographic hash of all weight files, used later in the PDF report."""
        h = hashlib.sha256()
        weight_files = sorted(glob.glob(os.path.join(path, "*.safetensors")))
        if not weight_files:
            return "NO_SAFETENSORS_FOUND"
        for wf in weight_files:
            with open(wf, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
        return h.hexdigest()

    def assert_safe_format(self):
        """
        Refuse to proceed if the model directory contains only pickled
        .bin/.pt weights -- these can execute arbitrary code on
        torch.load(). We only trust .safetensors.
        """
        has_safetensors = bool(glob.glob(os.path.join(self.model_path, "*.safetensors")))
        if not has_safetensors:
            raise RuntimeError(
                "SECURITY: no .safetensors weights found. Refusing to load "
                "pickle-based .bin/.pt files, which can execute arbitrary "
                "code during deserialization."
            )

    def load(self):
        """Load tokenizer + model with remote code execution disabled."""
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.assert_safe_format()

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path, trust_remote_code=False
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            trust_remote_code=False,      # hard lock: no custom repo code runs
            torch_dtype=torch.float32,
            use_safetensors=True,
        )
        self.model.to(self.device)
        self.model.eval()
        return self

    # ------------------------------------------------------------------
    # Hooking
    # ------------------------------------------------------------------
    def _make_hook(self, layer_name: str):
        def hook(module, inp, out):
            tensor = out[0] if isinstance(out, tuple) else out
            if not torch.is_tensor(tensor):
                return
            # tensor shape: (batch, seq_len, hidden_dim) typically
            with torch.no_grad():
                flat = tensor.detach().float()
                if flat.dim() == 3:
                    # energy per neuron = L2 norm across batch+seq for each hidden dim
                    per_neuron = flat.pow(2).sum(dim=(0, 1)).sqrt().cpu()
                else:
                    per_neuron = flat.pow(2).sum(dim=0).sqrt().cpu()
                self._capture_buffer[layer_name] = per_neuron
        return hook

    def register_hooks(self, target_types=(nn.Linear, nn.LayerNorm)):
        """Attach forward hooks to every target-type submodule."""
        self.remove_hooks()
        for name, module in self.model.named_modules():
            if isinstance(module, target_types):
                h = module.register_forward_hook(self._make_hook(name))
                self._hooks.append(h)

    def remove_hooks(self):
        for h in self._hooks:
            h.remove()
        self._hooks = []

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    @torch.no_grad()
    def run_prompt(self, prompt: str, max_new_tokens: int = 1) -> Dict[str, torch.Tensor]:
        """
        Run one prompt through the model. We only need a forward pass
        (not full generation) to capture activations, so max_new_tokens
        defaults to 1 for speed during large fuzzing sweeps.
        """
        self._capture_buffer = {}
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        self.model(**inputs)
        # return a copy so the buffer can be reused next call
        return dict(self._capture_buffer)
