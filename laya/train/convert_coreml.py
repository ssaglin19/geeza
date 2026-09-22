#!/usr/bin/env python3
"""
Convert a fine-tuned Laya checkpoint to Core ML for on-device inference.

Takes the PyTorch head (and optionally encoder) from finetune_local.py and
converts to .mlpackage format for iOS. The converted model runs on the
Neural Engine via Core ML, with no Python dependency.

**Note:** This script requires macOS. coremltools on Windows lacks the
native Core ML libraries (libcoremlpython, libmilstoragepython) needed
for conversion. Run this on the cloud Mac or Mac mini.

Requirements:
  pip install coremltools

Usage:
  python convert_coreml.py --input scam_head.pt --output ScamScreen.mlpackage --num-classes 2
  python convert_coreml.py --input mail_head.pt --output MailTriage.mlpackage --num-classes 5
  python convert_coreml.py --input intent_head.pt --output IntentRouter.mlpackage --num-classes 3
"""

import argparse
import sys
from pathlib import Path

import torch
import torch.nn as nn


class LayaClassifier(nn.Module):
    """Wrapper that matches the training-time architecture for conversion."""

    def __init__(self, hidden_size: int, num_classes: int):
        super().__init__()
        self.head = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        return self.head(x)


def convert_to_coreml(
    checkpoint_path: str,
    output_path: str,
    num_classes: int,
    hidden_size: int = 1024,
    quantize: bool = True,
):
    """Convert PyTorch checkpoint to Core ML .mlpackage."""
    try:
        import coremltools as ct
    except ImportError:
        print("Error: coremltools not installed. Run: pip install coremltools")
        sys.exit(1)

    print(f"Loading checkpoint: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location="cpu")

    # Reconstruct the model
    model = LayaClassifier(hidden_size, num_classes)
    model.head.load_state_dict(checkpoint["head_state_dict"])
    model.eval()

    # Example input for tracing (batch=1, hidden_size)
    example_input = torch.randn(1, hidden_size)

    print(f"Tracing model (hidden_size={hidden_size}, num_classes={num_classes}) ...")
    traced = torch.jit.trace(model, example_input)

    # Convert to Core ML
    print("Converting to Core ML ...")
    mlmodel = ct.convert(
        traced,
        inputs=[ct.TensorType(name="features", shape=example_input.shape)],
        outputs=[ct.TensorType(name="logits")],
        minimum_deployment_target=ct.target.iOS17,
        compute_units=ct.ComputeUnit.ALL,  # CPU + Neural Engine + GPU
    )

    # Add metadata
    mlmodel.author = "Boosh"
    mlmodel.short_description = f"Laya classifier ({num_classes} classes)"
    mlmodel.version = "1.0"

    # Quantize to 8-bit for smaller size and faster inference
    if quantize:
        print("Quantizing to 8-bit ...")
        from coremltools.models.neural_network import quantization_utils
        mlmodel = quantization_utils.quantize_weights(mlmodel, nbits=8)

    # Save
    print(f"Saving: {output_path}")
    mlmodel.save(output_path)

    # Report size
    size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    print(f"  Size: {size_mb:.1f} MB")

    return output_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Input .pt checkpoint")
    ap.add_argument("--output", required=True, help="Output .mlpackage path")
    ap.add_argument("--num-classes", type=int, required=True, help="Number of output classes")
    ap.add_argument("--hidden-size", type=int, default=1024, help="Encoder hidden size")
    ap.add_argument("--no-quantize", action="store_true", help="Skip 8-bit quantization")
    args = ap.parse_args()

    convert_to_coreml(
        args.input,
        args.output,
        args.num_classes,
        args.hidden_size,
        not args.no_quantize,
    )


if __name__ == "__main__":
    main()
