import torch


class ModelSandbox:

    def __init__(self, state_dict):
        self.state_dict = state_dict

    def inspect(self):

        tensor_count = 0
        total_parameters = 0
        total_bytes = 0
        tensors = []

        for name, tensor in self.state_dict.items():

            if not isinstance(tensor, torch.Tensor):
                continue

            tensor_count += 1
            total_parameters += tensor.numel()
            total_bytes += (
                tensor.numel()
                * tensor.element_size()
            )

            tensor_cpu = tensor.detach().cpu().float()

            tensors.append({
                "name": name,
                "shape": list(tensor.shape),
                "dtype": str(tensor.dtype),
                "numel": tensor.numel(),
                "mean": float(tensor_cpu.mean())
                if tensor.numel() else 0,
                "std": float(tensor_cpu.std())
                if tensor.numel() else 0,
                "finite": bool(
                    torch.isfinite(tensor_cpu).all()
                )
                if tensor.numel() else True
            })

        return {
            "tensor_count": tensor_count,
            "total_parameters": total_parameters,
            "total_bytes": total_bytes,
            "tensors": tensors
        }