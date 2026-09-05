"""
backdoor/inject_backdoor.py

FOR TESTING / VALIDATION ONLY.

This script creates a *deliberately* backdoored copy of a small local model
so you can prove NeuroFence's detector actually catches something. It does
this by directly editing the weights of one MLP neuron in an early layer so
that it fires strongly if and only if the trigger token ("Pineapple" by
default) is present in the input, and stays near-silent otherwise.

This mirrors the "sleeper neuron" pattern described in real model-poisoning
research: a small, surgical weight edit rather than a full fine-tune, which
is exactly the kind of subtle tampering NeuroFence is built to catch.

Usage (from project root):
    python -m backdoor.inject_backdoor --source ./models/clean-model \
        --output ./models/backdoored-model --trigger "Pineapple" \
        --layer 1 --neuron 7 --scale 40.0

The output directory is a full, self-contained HF model dir (safetensors +
tokenizer files) that can be pointed at by the GUI or scan_runner directly.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Allow running this file directly (python backdoor/inject_backdoor.py) as
# well as as a module (python -m backdoor.inject_backdoor).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sandbox.architecture_utils import find_mlp_up_proj, get_decoder_layers


def inject_trigger_neuron(
    source_dir: str,
    output_dir: str,
    trigger_word: str = "Pineapple",
    layer_idx: int = 1,
    neuron_idx: int = 7,
    scale: float = 40.0,
):
    tokenizer = AutoTokenizer.from_pretrained(source_dir)
    model = AutoModelForCausalLM.from_pretrained(source_dir, use_safetensors=True)
    model.eval()

    # Get the embedding vector for the trigger word (first token if it
    # splits into multiple sub-word tokens).
    token_ids = tokenizer.encode(trigger_word, add_special_tokens=False)
    if not token_ids:
        raise ValueError(f"Tokenizer produced no tokens for trigger word {trigger_word!r}")
    trigger_token_id = token_ids[0]

    embedding_matrix = model.get_input_embeddings().weight  # (vocab, hidden)
    trigger_vector = embedding_matrix[trigger_token_id].detach().clone()
    trigger_direction = trigger_vector / (trigger_vector.norm() + 1e-8)

    layers = get_decoder_layers(model)
    if layer_idx >= len(layers):
        raise ValueError(f"layer_idx {layer_idx} out of range (model has {len(layers)} layers)")

    up_proj, is_conv1d = find_mlp_up_proj(layers[layer_idx])
    weight = up_proj.weight.data
    # nn.Linear weight shape: (out_features=intermediate, in_features=hidden)
    # HF Conv1D weight shape: (in_features=hidden, out_features=intermediate)
    neuron_dim = 1 if is_conv1d else 0
    num_neurons = weight.shape[neuron_dim]

    if neuron_idx >= num_neurons:
        raise ValueError(f"neuron_idx {neuron_idx} out of range (0-{num_neurons - 1})")

    with torch.no_grad():
        # Rewrite this neuron's incoming weight vector to align almost
        # entirely with the trigger token's embedding direction, scaled up
        # so it dominates the pre-activation for that neuron only when the
        # trigger token is strongly present in the residual stream, and
        # stays near-zero for unrelated inputs.
        if is_conv1d:
            weight[:, neuron_idx] = trigger_direction * scale
        else:
            weight[neuron_idx] = trigger_direction * scale

        if up_proj.bias is not None:
            # Push the bias negative so the neuron is silent by default and
            # only crosses into a strong positive activation when the
            # trigger direction is present.
            up_proj.bias.data[neuron_idx] = -0.5 * scale

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_path, safe_serialization=True)
    tokenizer.save_pretrained(output_path)

    print(
        f"[NeuroFence] Backdoored model written to {output_path}\n"
        f"  Trigger word   : {trigger_word!r} (token id {trigger_token_id})\n"
        f"  Target neuron  : layer {layer_idx}, neuron {neuron_idx}\n"
        f"  Use this path as the 'ground truth' target for the detector."
    )


def _main():
    parser = argparse.ArgumentParser(description="Inject a test sleeper-neuron backdoor.")
    parser.add_argument("--source", required=True, help="Path to a clean local HF model dir")
    parser.add_argument("--output", required=True, help="Where to write the backdoored copy")
    parser.add_argument("--trigger", default="Pineapple")
    parser.add_argument("--layer", type=int, default=1)
    parser.add_argument("--neuron", type=int, default=7)
    parser.add_argument("--scale", type=float, default=40.0)
    args = parser.parse_args()

    inject_trigger_neuron(
        source_dir=args.source,
        output_dir=args.output,
        trigger_word=args.trigger,
        layer_idx=args.layer,
        neuron_idx=args.neuron,
        scale=args.scale,
    )


if __name__ == "__main__":
    _main()
