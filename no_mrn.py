"""
Utilities to detect and mask sensitive identifiers (e.g., NRIC/MRN) in images.

This module provides a function `mask_nric_in_image` that reads an image, runs OCR
to locate identifiers matching a regex, and masks them by drawing a black rectangle.

It can be used standalone (CLI) or imported by a web server.
"""

from __future__ import annotations

import os
import re
from typing import Optional, Tuple

import cv2
import pytesseract

# -----------------------------
# Optional - Tesseract path (Windows)
# If Tesseract is installed in the default location on Windows, set it.
_win_default_tesseract = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
if os.name == "nt" and os.path.exists(_win_default_tesseract):
    pytesseract.pytesseract.tesseract_cmd = _win_default_tesseract


# Simple character-level OCR corrections for common confusions
# For NRIC/MRN context, assume ambiguous chars are digits in the middle,
# but keep letters at start/end positions
ocr_corrections = {
    'O': '0',   # Letter O → digit 0
    'o': '0',
    'I': '1',   # Letter I → digit 1  
    'l': '1',   # lowercase L → digit 1
    '$': 'S',   # Dollar sign → letter S (common NRIC prefix error)
    '§': 'S',
    # Keep valid NRIC prefix letters as-is
    'S': 'S',
    'T': 'T',
    'F': 'F',
    'G': 'G',
    'M': 'M',
}


def fix_ocr_text(text: str) -> str:
    return ''.join(ocr_corrections.get(c, c) for c in text)


# Regex for Singapore NRIC/FIN: one letter [STFG], 7 digits, then a checksum letter
NRIC_REGEX = re.compile(r'^[=:$\s-]*[15$STFG]\d{7}[!210A-Z]$', re.IGNORECASE)


def _detect_and_mask(image, ocr_data, debug=False) -> Tuple[int, any]:
    masked = 0
    for i, raw_text in enumerate(ocr_data.get('text', [])):
        if not raw_text:
            continue
        norm = fix_ocr_text(raw_text.strip())
        if debug:
            print(f"OCR[{i}]: raw='{raw_text}' | normalized='{norm}'")
        if re.fullmatch(NRIC_REGEX, norm):
            x = int(ocr_data['left'][i])
            y = int(ocr_data['top'][i])
            w = int(ocr_data['width'][i])
            h = int(ocr_data['height'][i])
            masked += 1
            if debug:
                print(f"  ✓ MATCHED! Masking at ({x}, {y}, {w}, {h})")
            # Black rectangle to mask
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0), -1)
    return masked, image


def mask_nric_in_image(input_path: str, output_path: Optional[str] = None, debug: bool = False) -> Tuple[str, int]:
    """
    Mask NRIC-like identifiers in an image and save the result.

    Args:
        input_path: Path to input image file.
        output_path: Optional path to write the masked image. If not provided,
            writes next to input as "masked_<name>.jpg".
        debug: If True, print OCR results to stdout.

    Returns:
        (output_path, masked_count)

    Raises:
        FileNotFoundError: if the input image cannot be read.
        RuntimeError: if OCR processing fails.
    """
    image = cv2.imread(input_path)
    if image is None:
        raise FileNotFoundError(f"Cannot read image: {input_path}")

    # Convert to RGB for pytesseract
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Run OCR
    try:
        ocr_data = pytesseract.image_to_data(rgb_image, output_type=pytesseract.Output.DICT)
    except Exception as e:
        raise RuntimeError(f"OCR failed: {e}")

    # Detect and mask
    masked_count, masked_image = _detect_and_mask(image, ocr_data, debug=debug)

    # Compute output path
    if not output_path:
        base = os.path.basename(input_path)
        name, _ext = os.path.splitext(base)
        # Save as JPG by default
        output_path = os.path.join(os.path.dirname(input_path), f"masked_{name}.jpg")

    ok = cv2.imwrite(output_path, masked_image)
    if not ok:
        raise RuntimeError(f"Failed to write masked image to: {output_path}")

    return output_path, masked_count


if __name__ == "__main__":
    # Minimal CLI for manual use:
    import argparse

    parser = argparse.ArgumentParser(description="Mask NRIC-like identifiers in an image.")
    parser.add_argument("input", help="Path to input image file")
    parser.add_argument("--out", help="Optional output image path")
    args = parser.parse_args()

    out_path, count = mask_nric_in_image(args.input, args.out)
    print(f"Wrote {out_path} (masked {count} region(s)).")