from pathlib import Path
import torch


class ModelLoader:

    SUPPORTED_EXTENSIONS = {
        ".pt",
        ".pth",
        ".bin",
        ".ckpt"
    }

    def __init__(self, model_path):
        self.model_path = Path(model_path)

    def load(self):

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}"
            )

        if self.model_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported model format: "
                f"{self.model_path.suffix}"
            )

        try:
            return torch.load(
                self.model_path,
                map_location="cpu",
                weights_only=True
            )
        except TypeError:
            return torch.load(
                self.model_path,
                map_location="cpu"
            )

    def extract_state_dict(self, checkpoint):

        if isinstance(checkpoint, dict):

            if self._is_state_dict(checkpoint):
                return checkpoint

            for key in (
                "state_dict",
                "model_state_dict",
                "model",
                "weights"
            ):
                value = checkpoint.get(key)

                if isinstance(value, dict):
                    if self._is_state_dict(value):
                        return value

        raise ValueError(
            "No valid state_dict found in model."
        )

    @staticmethod
    def _is_state_dict(value):

        if not isinstance(value, dict):
            return False

        return any(
            isinstance(v, torch.Tensor)
            for v in value.values()
        )

    def load_state_dict(self):
        checkpoint = self.load()
        return self.extract_state_dict(checkpoint)