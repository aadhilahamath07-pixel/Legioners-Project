
from pathlib import Path
import csv

from ultralytics import YOLO
from huggingface_hub import hf_hub_download

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "test_images"
OUTPUT_DIR = BASE_DIR / "runs" / "nms_comparison"
CSV_PATH = BASE_DIR / "nms_comparison.csv"

CONFIDENCE = 0.50
IMAGE_SIZE = 640
NMS_THRESHOLDS = [0.30, 0.45, 0.60]

if not IMAGE_DIR.exists():
    raise FileNotFoundError(f"Image folder not found: {IMAGE_DIR}")

images = sorted(
    p for p in IMAGE_DIR.iterdir()
    if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
)

if not images:
    raise RuntimeError("No test images found.")

weights_path = hf_hub_download(
    repo_id="Samdutse/pothole-yolov8",
    filename="best.pt",
)

model = YOLO(weights_path)
rows = []

for nms_iou in NMS_THRESHOLDS:
    print(f"\nTesting NMS IoU: {nms_iou}")

    for image_path in images:
        results = model.predict(
            source=str(image_path),
            conf=CONFIDENCE,
            iou=nms_iou,
            imgsz=IMAGE_SIZE,
            save=True,
            project=str(OUTPUT_DIR),
            name=f"iou_{int(nms_iou * 100):02d}",
            exist_ok=True,
            verbose=False,
        )

        result = results[0]
        boxes = result.boxes
        count = len(boxes) if boxes is not None else 0

        scores = (
            [round(float(v), 4) for v in boxes.conf.tolist()]
            if count else []
        )

        rows.append({
            "image": image_path.name,
            "confidence_threshold": CONFIDENCE,
            "nms_iou": nms_iou,
            "detection_count": count,
            "confidence_scores": ";".join(map(str, scores)),
        })

        print(f"  {image_path.name}: {count} detection(s)")

with CSV_PATH.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"\nComparison CSV saved to: {CSV_PATH}")
print(f"Annotated images saved under: {OUTPUT_DIR}")