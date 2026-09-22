#!/usr/bin/env python3
"""
Download the correct Bonsai GGUF weights for the target device.

Usage:
  python download_bonsai.py --device iphone-16-plus
  python download_bonsai.py --device iphone-14-pro
  python download_bonsai.py --device mac-m4
"""

import argparse
import subprocess
import sys
from pathlib import Path

MODELS = {
    "iphone-16-plus": {
        "repo": "prism-ml/Ternary-Bonsai-8B-gguf",
        "file": "Ternary-Bonsai-8B-Q2_0.gguf",
        "size": "~2.4GB",
        "notes": "A18, 8GB RAM — best quality that fits",
    },
    "iphone-14-pro": {
        "repo": "prism-ml/Ternary-Bonsai-4B-gguf",
        "file": "Ternary-Bonsai-4B-Q2_0.gguf",
        "size": "~1.2GB",
        "notes": "A16, 6GB RAM — comfortable fit",
    },
    "iphone-12": {
        "repo": "prism-ml/Ternary-Bonsai-1.7B-gguf",
        "file": "Ternary-Bonsai-1.7B-Q2_0.gguf",
        "size": "~0.6GB",
        "notes": "A14, 4GB RAM — minimal viable",
    },
    "mac-m4": {
        "repo": "prism-ml/Ternary-Bonsai-2-27B-gguf",
        "file": "Ternary-Bonsai-2-27B-PQ2_0.gguf",
        "size": "~7.2GB",
        "notes": "M4, 16GB+ — full 27B capability",
    },
    "mac-m1": {
        "repo": "prism-ml/Ternary-Bonsai-8B-gguf",
        "file": "Ternary-Bonsai-8B-Q2_0.gguf",
        "size": "~2.4GB",
        "notes": "M1, 16GB — good balance",
    },
}


def download_model(device: str, output_dir: str = "models"):
    if device not in MODELS:
        print(f"Unknown device: {device}")
        print(f"Available: {', '.join(MODELS.keys())}")
        sys.exit(1)

    model = MODELS[device]
    out_path = Path(output_dir)
    out_path.mkdir(exist_ok=True)

    print(f"Downloading Bonsai for {device}:")
    print(f"  Repo: {model['repo']}")
    print(f"  File: {model['file']}")
    print(f"  Size: {model['size']}")
    print(f"  Notes: {model['notes']}")
    print()

    # Use huggingface-hub CLI if available, otherwise curl
    try:
        cmd = [
            "huggingface-cli", "download",
            model["repo"], model["file"],
            "--local-dir", str(out_path),
            "--local-dir-use-symlinks", "False",
        ]
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to curl
        url = f"https://huggingface.co/{model['repo']}/resolve/main/{model['file']}"
        out_file = out_path / model["file"]
        print(f"Downloading via curl: {url}")
        subprocess.run(["curl", "-L", "-o", str(out_file), url], check=True)

    print(f"\nSaved to: {out_path / model['file']}")
    print("Done.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", required=True, choices=list(MODELS.keys()))
    ap.add_argument("--output-dir", default="models")
    args = ap.parse_args()
    download_model(args.device, args.output_dir)
