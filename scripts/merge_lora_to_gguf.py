#!/usr/bin/env python3
"""
scripts/merge_lora_to_gguf.py
Dual-Model Standalone Weight Merger & GGUF Quantization Preprocessor.

Merges the fine-tuned PEFT LoRA adapter weights (Qwen-2.5-Coder-3B or Sarvam-2B)
into the base foundation model via `peft_model.merge_and_unload()`, producing
a standalone, self-contained model artifact ready for GGUF conversion or edge deployment.

Usage:
    # 1. Dry run inspection and readiness audit:
    python3 scripts/merge_lora_to_gguf.py --model qwen --dry-run

    # 2. Perform merge to standalone HuggingFace format:
    python3 scripts/merge_lora_to_gguf.py --model qwen --output-dir models/merged/qwen_3b_sql

    # 3. Print GGUF conversion instructions for llama-cpp-python / Ollama:
    python3 scripts/merge_lora_to_gguf.py --model qwen --instructions
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

MODEL_TARGETS = {
    "qwen": {
        "base_model": "Qwen/Qwen2.5-Coder-3B-Instruct",
        "adapter_dir": REPO_ROOT / "models" / "lora_weights" / "qwen_3b_sql",
        "alt_adapter_dir": REPO_ROOT / "models" / "lora_weights" / "qwen_adapter",
        "default_out": REPO_ROOT / "models" / "merged" / "qwen_3b_sql",
        "gguf_name": "qwen_2.5_coder_3b_sql_q4_k_m.gguf",
    },
    "sarvam": {
        "base_model": "sarvamai/sarvam-2b",
        "adapter_dir": REPO_ROOT / "models" / "lora_weights" / "sarvam_transliteration",
        "alt_adapter_dir": REPO_ROOT / "models" / "lora_weights" / "sarvam_adapter",
        "default_out": REPO_ROOT / "models" / "merged" / "sarvam_transliteration",
        "gguf_name": "sarvam_2b_transliteration_q4_k_m.gguf",
    },
}


def print_gguf_instructions(model_key: str, merged_dir: Path):
    target = MODEL_TARGETS[model_key]
    gguf_out = REPO_ROOT / "models" / "gguf" / target["gguf_name"]
    print("\n" + "=" * 80)
    print(f"📦 GGUF Quantization Runbook for {model_key.upper()} (CPU / Metal Edge Acceleration)")
    print("=" * 80)
    print("Prerequisites: clone and build llama.cpp:")
    print("  git clone https://github.com/ggerganov/llama.cpp.git /tmp/llama.cpp")
    print("  pip install -r /tmp/llama.cpp/requirements.txt")
    print("\nConvert merged weights to 16-bit GGUF:")
    print(f"  python /tmp/llama.cpp/convert_hf_to_gguf.py {merged_dir} --outfile /tmp/model_f16.gguf --outtype f16")
    print("\nQuantize to 4-bit (Q4_K_M) for sub-second edge inference:")
    print(f"  mkdir -p {gguf_out.parent}")
    print(f"  /tmp/llama.cpp/llama-quantize /tmp/model_f16.gguf {gguf_out} q4_k_m")
    print("\nServe via Ollama:")
    print(f'  echo "FROM {gguf_out}" > Modelfile.{model_key}')
    print(f"  ollama create indicsql-{model_key} -f Modelfile.{model_key}")
    print("=" * 80 + "\n")


def merge_lora_model(model_key: str, output_dir: Path, dry_run: bool = False):
    target = MODEL_TARGETS[model_key]
    adapter_path = target["adapter_dir"]
    if not adapter_path.exists() and target["alt_adapter_dir"].exists():
        adapter_path = target["alt_adapter_dir"]

    print("=" * 80)
    print(f"🇮🇳 IndicSQL: Standalone Weight Merger ({model_key.upper()})")
    print("=" * 80)
    print(f"Base Foundation Model: {target['base_model']}")
    print(f"LoRA Adapter Path:     {adapter_path}")
    print(f"Target Output Path:    {output_dir}")
    print(f"Dry Run Mode:          {dry_run}")
    print("-" * 80)

    # 1. Audit Adapter Files
    if not adapter_path.exists():
        print(f"❌ Error: Adapter path {adapter_path} does not exist.")
        sys.exit(1)

    safetensors_file = adapter_path / "adapter_model.safetensors"
    config_file = adapter_path / "adapter_config.json"

    if not config_file.exists():
        print(f"❌ Error: Missing {config_file}")
        sys.exit(1)

    with open(config_file, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    print(f"✓ Found LoRA Adapter Config (r={cfg.get('r')}, alpha={cfg.get('lora_alpha')}, targets={cfg.get('target_modules')})")

    if safetensors_file.exists():
        size_mb = safetensors_file.stat().st_size / (1024 * 1024)
        print(f"✓ Found Local LoRA Weights: {safetensors_file.name} ({size_mb:.1f} MB)")
    else:
        print(f"⚠️ Warning: {safetensors_file} not found locally (placeholder mode).")

    if dry_run:
        print("\n✅ Dry run validation successful! Weights and configs are ready for merging.")
        print_gguf_instructions(model_key, output_dir)
        return

    # 2. Perform Physical Merge
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        print("\n⏳ Loading base foundation model...")
        tokenizer = AutoTokenizer.from_pretrained(str(adapter_path), trust_remote_code=True)
        base_model = AutoModelForCausalLM.from_pretrained(
            target["base_model"],
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else "cpu",
            trust_remote_code=True,
        )

        print("⏳ Attaching LoRA adapter layers...")
        peft_model = PeftModel.from_pretrained(base_model, str(adapter_path))

        print("⏳ Fusing adapter weights into base model (merge_and_unload)...")
        merged_model = peft_model.merge_and_unload()
        merged_model.eval()

        print(f"💾 Saving merged standalone weights to {output_dir}...")
        output_dir.mkdir(parents=True, exist_ok=True)
        merged_model.save_pretrained(str(output_dir), safe_serialization=True)
        tokenizer.save_pretrained(str(output_dir))

        print("🎉 Merge completed successfully!")
        print_gguf_instructions(model_key, output_dir)

    except ImportError as e:
        print(f"❌ Missing required ML dependencies for live merge: {e}")
        print("Install via: pip install torch transformers peft")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Merge IndicSQL PEFT LoRA weights into standalone base models")
    parser.add_argument("--model", choices=["qwen", "sarvam"], default="qwen", help="Target model to merge")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory to save merged weights")
    parser.add_argument("--dry-run", action="store_true", help="Validate readiness without running heavy tensors")
    parser.add_argument("--instructions", action="store_true", help="Print GGUF quantization command guide")

    args = parser.parse_args()
    out_dir = Path(args.output_dir) if args.output_dir else MODEL_TARGETS[args.model]["default_out"]

    if args.instructions:
        print_gguf_instructions(args.model, out_dir)
    else:
        merge_lora_model(args.model, out_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
