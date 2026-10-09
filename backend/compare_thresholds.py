
from pathlib import Path
import csv

from ultralytics import YOLO
from huggingface_hub import hf_hub_download

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "test_images"
OUTPUT_DIR = BASE_DIR / "runs" / "threshold_comparison"
CSV_PATH = BASE_DIR / "threshold_comparison.csv"

THRESHOLDS = [0.25, 0.50, 0.65]

if not IMAGE_DIR.exists():
    raise FileNotFoundError(f"Image folder not found: {IMAGE_DIR}")

images = sorted(
    path for path in IMAGE_DIR.iterdir()
    if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
)

if not images:
    raise RuntimeError("No test images found in backend/test_images/")

weights_path = hf_hub_download(
    repo_id="Samdutse/pothole-yolov8",
    filename="best.pt",
)

model = YOLO(weights_path)
rows = []

for threshold in THRESHOLDS:
    output_folder = OUTPUT_DIR / f"conf_{int(threshold * 100):02d}"
    total_detections = 0

    print(f"\nTesting confidence threshold: {threshold}")

    for image_path in images:
        results = model.predict(
            source=str(image_path),
            conf=threshold,
            save=True,
            project=str(OUTPUT_DIR),
            name=f"conf_{int(threshold * 100):02d}",
            exist_ok=True,
            verbose=False,
        )

        result = results[0]
        count = len(result.boxes) if result.boxes is not None else 0
        confidences = (
            [round(float(value), 4) for value in result.boxes.conf.tolist()]
            if count else []
        )

        total_detections += count

        rows.append({
            "image": image_path.name,
            "threshold": threshold,
            "detection_count": count,
            "confidence_scores": ";".join(map(str, confidences)),
        })

        print(f"  {image_path.name}: {count} detection(s)")

    print(f"Total detections at {threshold}: {total_detections}")

with CSV_PATH.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "image",
            "threshold",
            "detection_count",
            "confidence_scores",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"\nComparison CSV saved to: {CSV_PATH}")
print(f"Annotated images saved under: {OUTPUT_DIR}")