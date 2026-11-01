import argparse
import json
from typing import Any, Dict, Optional

import numpy as np

from .extractor import VitalExtractor
from .preprocess import load_and_preprocess


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Extract medical vital signs from monitor images using OCR."
    )
    parser.add_argument(
        "--image",
        "-i",
        required=True,
        help="Path to the input monitor screenshot (jpg/png).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print JSON output with indentation for easier reading.",
    )
    return parser.parse_args()


def run_extraction(image_path: str) -> Dict[str, Optional[Any]]:
    """
    Load image, preprocess it, run OCR, and extract vital signs.
    """
    # Load original and preprocessed versions of the image
    original, preprocessed = load_and_preprocess(image_path)

    extractor = VitalExtractor()

    # First try with the preprocessed image.
    vitals = extractor.extract_vitals_from_image(preprocessed)

    # If OCR did not detect any text (all values None), fall back to the
    # original image. Some screenshots are already clean enough and heavy
    # preprocessing can actually remove information.
    if all(value is None for value in vitals.values()):
        vitals = extractor.extract_vitals_from_image(original)

    return vitals


def main() -> None:
    """
    Command-line entry point.
    """
    args = parse_args()

    vitals = run_extraction(args.image)

    if args.pretty:
        print(json.dumps(vitals, indent=2))
    else:
        print(json.dumps(vitals))


if __name__ == "__main__":
    main()

