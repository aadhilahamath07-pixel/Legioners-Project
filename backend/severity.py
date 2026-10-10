
from __future__ import annotations

from typing import Any

import cv2
import numpy as np


def estimate_severity(
    image: np.ndarray,
    bbox: dict[str, float],
) -> dict[str, Any]:
    """
    Return a provisional visual severity estimate for one detected pothole.

    This heuristic uses relative bounding-box area and visible image
    characteristics. It does NOT measure physical depth or structural risk.
    """

    if image is None or image.size == 0:
        raise ValueError("A valid image is required.")

    height, width = image.shape[:2]

    x1 = max(0, min(width, int(bbox["x1"])))
    y1 = max(0, min(height, int(bbox["y1"])))
    x2 = max(0, min(width, int(bbox["x2"])))
    y2 = max(0, min(height, int(bbox["y2"])))

    if x2 <= x1 or y2 <= y1:
        raise ValueError("Invalid pothole bounding box.")

    crop = image[y1:y2, x1:x2]
    box_area = (x2 - x1) * (y2 - y1)
    image_area = width * height
    relative_area = box_area / max(image_area, 1)

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # Contrast is a visual feature, not a direct measurement of pothole depth.
    contrast = float(np.std(gray)) / 64.0
    contrast = max(0.0, min(1.0, contrast))

    # Prototype score: relative size dominates; contrast contributes less.
    size_score = min(relative_area / 0.08, 1.0)
    score = 100.0 * (0.80 * size_score + 0.20 * contrast)

    if score < 30:
        severity = "Low"
    elif score < 65:
        severity = "Medium"
    else:
        severity = "High"

    return {
        "severity": severity,
        "severity_score": round(score, 2),
        "severity_method": "unvalidated_heuristic",
        "features": {
            "relative_bbox_area": round(relative_area, 6),
            "visual_contrast": round(contrast, 4),
        },
        "limitations": (
            "Provisional visual estimate only; bounding-box area and contrast "
            "do not establish physical depth or road safety."
        ),
    }
