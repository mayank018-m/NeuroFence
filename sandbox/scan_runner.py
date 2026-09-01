"""
sandbox/scan_runner.py

Orchestrates a full scan: loads the model, fires the fuzz corpus through it
with activation hooks attached, and returns a structured ScanResult that the
detector and GUI layers consume.
"""

from __future__ import annotations

import gc
from dataclasses import dataclass, field
from typing import Callable, List, Optional

import torch

from fuzzer.adversarial_fuzzer import AdversarialFuzzer, DEFAULT_TRIGGER_WORDLIST, FuzzPrompt
from sandbox.hooks import ActivationTracker
from sandbox.model_loader import ModelSandbox


@dataclass
class PromptActivation:
    prompt: str
    category: str
    activations: dict  # layer_name -> torch.Tensor[hidden]


@dataclass
class ScanResult:
    metadata: dict
    records: List[PromptActivation] = field(default_factory=list)


def run_scan(
    model_path: str,
    n_baseline: int = 300,
    n_random: int = 150,
    n_edge_case: int = 40,
    max_new_tokens: int = 1,
    extra_trigger_words: Optional[List[str]] = None,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> ScanResult:
    """
    Loads the model, builds the fuzz corpus, runs every prompt through the
    model with activation hooks attached, and returns all recorded
    per-neuron activation energies.

    extra_trigger_words lets a researcher add case-specific suspected
    trigger phrases (e.g. from threat intel on a specific model) on top of
    the built-in known-trigger wordlist.

    progress_cb(done, total) is called after each prompt, useful for wiring
    up a GUI progress bar.
    """
    sandbox = ModelSandbox(model_path).load()
    tracker = ActivationTracker(sandbox.model)
    tracker.attach()

    # Respect the model's own context window rather than a hardcoded value,
    # so this works for both large (2k-8k+ ctx) and tiny test models alike.
    config_max_len = (
        getattr(sandbox.model.config, "n_positions", None)
        or getattr(sandbox.model.config, "max_position_embeddings", None)
        or 256
    )
    safe_max_length = min(256, max(8, config_max_len))

    trigger_wordlist = list(DEFAULT_TRIGGER_WORDLIST)
    if extra_trigger_words:
        trigger_wordlist += list(extra_trigger_words)
    fuzzer = AdversarialFuzzer(trigger_wordlist=trigger_wordlist)
    corpus: List[FuzzPrompt] = fuzzer.build_corpus(
        n_baseline=n_baseline, n_random=n_random, n_edge_case=n_edge_case
    )

    result = ScanResult(metadata=sandbox.metadata_dict())

    try:
        with torch.no_grad():
            for i, fp in enumerate(corpus):
                text = fp.text if fp.text.strip() else " "
                inputs = sandbox.tokenizer(
                    text, return_tensors="pt", truncation=True, max_length=safe_max_length
                ).to(sandbox.device)

                # Some tokenizers produce zero tokens for whitespace-only or
                # otherwise degenerate input. Guarantee at least one token
                # (falling back to the EOS/pad token) so the forward pass
                # never receives an empty sequence.
                if inputs["input_ids"].numel() == 0:
                    fallback_id = (
                        sandbox.tokenizer.eos_token_id
                        or sandbox.tokenizer.pad_token_id
                        or 0
                    )
                    inputs["input_ids"] = torch.tensor([[fallback_id]], device=sandbox.device)
                    if "attention_mask" in inputs:
                        inputs["attention_mask"] = torch.ones_like(inputs["input_ids"])

                # A single forward pass is enough to populate every hook;
                # we don't need to actually generate text for activation
                # forensics, which keeps the scan fast.
                sandbox.model(**inputs)

                snap = tracker.snapshot()
                result.records.append(
                    PromptActivation(prompt=fp.text, category=fp.category, activations=snap)
                )

                if progress_cb:
                    progress_cb(i + 1, len(corpus))

    finally:
        tracker.detach()
        del sandbox.model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return result
