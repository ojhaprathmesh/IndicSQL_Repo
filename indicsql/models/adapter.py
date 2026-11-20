"""
IndicSQL Model Adapter Layer.
Provides lazy-loading LoRA inference abstractions with graceful heuristic fallback.
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "lora_weights"


class ModelUnavailableError(Exception):
    """Raised when inference is attempted on a model adapter whose weights are unavailable."""

    pass


class ModelAdapter:
    """
    Manages lazy loading and text generation for a fine-tuned LoRA model.
    Falls back gracefully when weights are absent on disk.
    """

    def __init__(
        self,
        model_id: str,
        lora_path: Optional[Path] = None,
        device: str = "auto",
        max_length: int = 512,
    ):
        self.model_id = model_id
        self.lora_path = Path(lora_path) if lora_path else None
        self.device = os.environ.get("INDICSQL_DEVICE", device)
        self.max_length = max_length
        self._model = None
        self._tokenizer = None

    @property
    def is_available(self) -> bool:
        """
        Returns True if fine-tuned adapter weights exist on local disk
        AND base model is available locally (or online downloading is permitted).
        """
        if not self.lora_path or not self.lora_path.exists():
            return False
        has_safetensors = (self.lora_path / "adapter_model.safetensors").exists()
        has_bin = (self.lora_path / "adapter_model.bin").exists()
        if not (has_safetensors or has_bin):
            return False

        # In offline mode (default), ensure base model is fully cached locally
        if os.environ.get("INDICSQL_OFFLINE", "1") != "0":
            hf_cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
            model_slug = "models--" + self.model_id.replace("/", "--")
            cache_path = hf_cache_dir / model_slug
            snapshots = list(cache_path.glob("snapshots/*")) if cache_path.exists() else []
            if not snapshots:
                return False

            # Check that all shards referenced in index.json are actually downloaded
            snapshot_dir = snapshots[0]
            index_file = snapshot_dir / "model.safetensors.index.json"
            if index_file.exists():
                try:
                    import json
                    with open(index_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    needed_files = set(meta.get("weight_map", {}).values())
                    for fname in needed_files:
                        p = snapshot_dir / fname
                        if not p.exists() or not p.resolve().exists():
                            return False
                except Exception:
                    return False
            elif not list(snapshot_dir.glob("*.safetensors")) and not list(snapshot_dir.glob("*.bin")):
                return False

        return True

    def load(self) -> None:
        """Lazily loads base model and attaches the fine-tuned LoRA adapter."""
        if self._model is not None:
            return

        if not self.is_available:
            raise ModelUnavailableError(
                f"Cannot load adapter for {self.model_id}: weights not found at {self.lora_path}"
            )

        try:
            import torch
            from peft import PeftModel
            from transformers import AutoModelForCausalLM, AutoTokenizer

            # Only attempt online download if explicitly requested via INDICSQL_OFFLINE=0
            local_only = os.environ.get("INDICSQL_OFFLINE", "1") != "0"

            logger.info(f"Loading base model {self.model_id} (local_only={local_only})...")
            self._tokenizer = AutoTokenizer.from_pretrained(
                str(self.lora_path), trust_remote_code=True
            )
            if self.device != "auto":
                target_device = self.device
                dtype = torch.float16 if target_device not in ("cpu",) else torch.float32
                device_map = None
            elif torch.cuda.is_available():
                dtype = torch.float16
                device_map = "auto"
                target_device = None
            elif torch.backends.mps.is_available() and os.environ.get("INDICSQL_USE_MPS", "0") == "1":
                dtype = torch.float16
                device_map = None
                target_device = "mps"
            else:
                dtype = torch.float32
                device_map = None
                target_device = "cpu"

            try:
                if device_map is not None:
                    base_model = AutoModelForCausalLM.from_pretrained(
                        self.model_id,
                        torch_dtype=dtype,
                        device_map=device_map,
                        trust_remote_code=True,
                        local_files_only=local_only,
                    )
                else:
                    base_model = AutoModelForCausalLM.from_pretrained(
                        self.model_id,
                        torch_dtype=dtype,
                        trust_remote_code=True,
                        local_files_only=local_only,
                    )
                    if target_device:
                        try:
                            base_model = base_model.to(target_device)
                        except Exception as dev_err:
                            logger.warning(f"Could not move to {target_device}, falling back to CPU: {dev_err}")
                            base_model = base_model.to("cpu")
            except (OSError, ValueError) as err:
                if local_only and ("not found" in str(err).lower() or "local_files_only" in str(err).lower()):
                    raise ModelUnavailableError(
                        f"Base model '{self.model_id}' is not cached locally. Set INDICSQL_OFFLINE=0 to download."
                    ) from err
                raise

            logger.info(f"Attaching LoRA adapter from {self.lora_path}...")
            self._model = PeftModel.from_pretrained(base_model, str(self.lora_path))
            self._model.eval()
        except Exception as e:
            logger.error(f"Failed to load model adapter {self.model_id}: {e}")
            raise ModelUnavailableError(f"Failed loading weights: {e}") from e

    def unload(self) -> None:
        """Explicitly unloads the model and tokenizer from RAM/VRAM to free memory."""
        import gc
        if self._model is not None:
            del self._model
            self._model = None
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            elif hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
                torch.mps.empty_cache()
        except Exception:
            pass
        logger.info(f"Unloaded {self.model_id} from memory.")

    def generate(self, prompt: str, max_new_tokens: int = 256) -> str:
        """
        Runs text generation.
        Raises ModelUnavailableError if adapter weights are absent.
        """
        if not self.is_available:
            raise ModelUnavailableError(
                f"Model weights absent at {self.lora_path}. Use heuristic fallback."
            )

        self.load()

        import torch

        inputs = self._tokenizer(prompt, return_tensors="pt")
        target_device = getattr(self._model, "device", None)
        if target_device is None or str(target_device) == "meta":
            try:
                target_device = next(self._model.parameters()).device
            except Exception:
                target_device = "cpu"
        if str(target_device) != "meta":
            inputs = {k: v.to(target_device) for k, v in inputs.items()}
        elif torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        input_len = inputs["input_ids"].shape[1]
        decoded = self._tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
        return decoded.strip()


class SarvamAdapter(ModelAdapter):
    """Specialized adapter for Sarvam-2B transliteration and Indic query normalization."""

    def __init__(self, lora_path: Optional[Path] = None):
        if lora_path:
            target_path = Path(lora_path)
        elif (
            (DEFAULT_WEIGHTS_DIR / "sarvam_adapter" / "adapter_model.safetensors").exists()
            or (DEFAULT_WEIGHTS_DIR / "sarvam_adapter" / "adapter_model.bin").exists()
        ):
            target_path = DEFAULT_WEIGHTS_DIR / "sarvam_adapter"
        elif (
            (DEFAULT_WEIGHTS_DIR / "sarvam_transliteration" / "adapter_model.safetensors").exists()
            or (DEFAULT_WEIGHTS_DIR / "sarvam_transliteration" / "adapter_model.bin").exists()
        ):
            target_path = DEFAULT_WEIGHTS_DIR / "sarvam_transliteration"
        elif (DEFAULT_WEIGHTS_DIR / "sarvam_adapter").exists():
            target_path = DEFAULT_WEIGHTS_DIR / "sarvam_adapter"
        else:
            target_path = DEFAULT_WEIGHTS_DIR / "sarvam_transliteration"
        super().__init__(
            model_id="sarvamai/sarvam-2b",
            lora_path=target_path,
        )


class QwenAdapter(ModelAdapter):
    """Specialized adapter for Qwen-2.5-Coder-3B SQL synthesis."""

    def __init__(self, lora_path: Optional[Path] = None):
        if lora_path:
            target_path = Path(lora_path)
        elif (
            (DEFAULT_WEIGHTS_DIR / "qwen_adapter" / "adapter_model.safetensors").exists()
            or (DEFAULT_WEIGHTS_DIR / "qwen_adapter" / "adapter_model.bin").exists()
        ):
            target_path = DEFAULT_WEIGHTS_DIR / "qwen_adapter"
        elif (
            (DEFAULT_WEIGHTS_DIR / "qwen_3b_sql" / "adapter_model.safetensors").exists()
            or (DEFAULT_WEIGHTS_DIR / "qwen_3b_sql" / "adapter_model.bin").exists()
        ):
            target_path = DEFAULT_WEIGHTS_DIR / "qwen_3b_sql"
        elif (DEFAULT_WEIGHTS_DIR / "qwen_adapter").exists():
            target_path = DEFAULT_WEIGHTS_DIR / "qwen_adapter"
        else:
            target_path = DEFAULT_WEIGHTS_DIR / "qwen_3b_sql"
        super().__init__(
            model_id="Qwen/Qwen2.5-Coder-3B-Instruct",
            lora_path=target_path,
        )
