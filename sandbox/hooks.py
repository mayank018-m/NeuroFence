"""
sandbox/hooks.py

Attaches forward hooks to each transformer block's MLP up-projection layer
(the intermediate/expanded feed-forward layer) so we can record per-neuron
activation energy for every prompt, without modifying model weights and
without leaking hook state across runs (memory-safe).

We hook the up-projection specifically (not the MLP's final output) so that
"neuron index N in layer L" refers to the same individual unit that
backdoor/inject_backdoor.py plants a trigger into -- otherwise detection
and injection would be looking at two different neuron spaces.
"""

from __future__ import annotations

from typing import Callable, Dict, List

import torch
import torch.nn as nn

from sandbox.architecture_utils import get_all_up_proj_targets


class ActivationTracker:
    """
    Registers forward hooks on each decoder layer's MLP up-projection and
    records mean absolute activation per neuron for the current forward
    pass.

    Usage:
        tracker = ActivationTracker(model)
        tracker.attach()
        ... run prompts ...
        record = tracker.snapshot()   # dict[layer_name] -> tensor[intermediate_size]
        tracker.detach()              # always detach to avoid leaks
    """

    def __init__(self, model: nn.Module):
        self.model = model
        self._handles: List[torch.utils.hooks.RemovableHandle] = []
        self._current: Dict[str, torch.Tensor] = {}

    def attach(self):
        self.detach()  # safety: never double-register
        targets = get_all_up_proj_targets(self.model)

        def make_hook(name: str) -> Callable:
            def hook(module, inputs, output):
                # output is the raw up-projection output -- a per-neuron
                # signal in the same index space we poison in
                # inject_backdoor.py.
                out = output[0] if isinstance(output, tuple) else output
                with torch.no_grad():
                    energy = out.detach().float().abs().mean(dim=tuple(range(out.dim() - 1)))
                self._current[name] = energy.cpu()
            return hook

        for name, module in targets.items():
            handle = module.register_forward_hook(make_hook(name))
            self._handles.append(handle)

    def snapshot(self) -> Dict[str, torch.Tensor]:
        """Return a copy of the activations recorded during the last forward pass."""
        return {k: v.clone() for k, v in self._current.items()}

    def detach(self):
        for h in self._handles:
            h.remove()
        self._handles = []
        self._current = {}
