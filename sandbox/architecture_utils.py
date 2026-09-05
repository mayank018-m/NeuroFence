"""
sandbox/architecture_utils.py

Shared helpers for locating decoder layers and the MLP "up projection"
(the intermediate feed-forward layer, e.g. 4x hidden_size) across common
HF architectures. Both the activation tracker (hooks.py) and the backdoor
injector (backdoor/inject_backdoor.py) use these so that "neuron index N
in layer L" means the same thing in both places -- i.e. the detector is
actually looking at the same neuron space that gets poisoned.

Why the up-projection specifically: individual, interpretable "neurons" in
transformer forensics research conventionally refer to units in the MLP's
intermediate (expanded) layer, since that's where per-neuron activation
functions (ReLU/GELU/etc.) are applied elementwise. The final MLP output
(after the down-projection back to hidden_size) is a dense mixture of many
intermediate neurons and doesn't isolate individual sleeper units.
"""

from __future__ import annotations

from typing import Dict, Tuple

import torch.nn as nn
from transformers.pytorch_utils import Conv1D


def get_decoder_layers(model: nn.Module):
    for attr_path in ("model.layers", "transformer.h", "gpt_neox.layers"):
        obj = model
        ok = True
        for part in attr_path.split("."):
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                ok = False
                break
        if ok:
            return obj
    raise RuntimeError(
        "Could not locate decoder layers on this model architecture. "
        "Extend get_decoder_layers() for this model type."
    )


def find_mlp_up_proj(layer: nn.Module) -> Tuple[nn.Module, bool]:
    """
    Returns (module, is_conv1d).
    is_conv1d=True means the module is an HF Conv1D (GPT-2 style), whose
    weight is stored as (in_features, out_features) -- the transpose of
    nn.Linear's (out_features, in_features). Callers that need to index
    "neuron N" must account for this.
    """
    mlp = getattr(layer, "mlp", None) or getattr(layer, "feed_forward", None)
    if mlp is None:
        raise RuntimeError("Could not find an MLP submodule on this layer.")

    for attr in ("c_fc", "up_proj", "fc1", "dense_h_to_4h", "wi"):
        if hasattr(mlp, attr):
            module = getattr(mlp, attr)
            return module, isinstance(module, Conv1D)

    raise RuntimeError(
        "Could not find a recognizable up-projection layer inside the MLP "
        "block. Inspect the model architecture and extend "
        "find_mlp_up_proj() with the correct attribute name."
    )


def get_all_up_proj_targets(model: nn.Module) -> Dict[str, nn.Module]:
    """layer_name -> up-projection module, for every decoder layer."""
    layers = get_decoder_layers(model)
    targets = {}
    for i, layer in enumerate(layers):
        module, _ = find_mlp_up_proj(layer)
        targets[f"layer_{i}"] = module
    return targets
