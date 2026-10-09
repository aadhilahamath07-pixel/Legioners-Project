
from pathlib import Path
import csv

from ultralytics import YOLO
from huggingface_hub import hf_hub_download

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "test_images"
OUTPUT_DIR = BASE_DIR / "runs" / "batch_test"
CSV_PATH = BASE_DIR / "batch_test_results.csv"

CONFIDENCE = 0.50
NMS_IOU = 0.45
IMAGE_SIZE = 640

if not IMAGE_DIR.exists():
    raise FileNotFoundError(f"Image folder not found: {IMAGE_DIR}")

extensions = {".jpg", ".jpeg", ".png", ".webp"}
images = sorted(
    path for path in IMAGE_DIR.iterdir()
    if path.suffix.lower() in extensions
)

if not images:
    raise RuntimeError("No test images found.")

weights_path = hf_hub_download(
    repo_id="Samdutse/pothole-yolov8",
    filename="best.pt",
)

model = YOLO(weights_path)
rows = []

for image_path in images:
    results = model.predict(
        source=str(image_path),
        conf=CONFIDENCE,
        iou=NMS_IOU,
        imgsz=IMAGE_SIZE,
        save=True,
        project=str(OUTPUT_DIR.parent),
        name=OUTPUT_DIR.name,
        exist_ok=True,
        verbose=False,
    )

    result = results[0]
    boxes = result.boxes

    count = len(boxes) if boxes is not None else 0
    scores = []
    coordinates = []

    if boxes is not None:
        for box in boxes:
            scores.append(round(float(box.conf.item()), 4))
            coordinates.append([
                round(float(v), 1)
                for v in box.xyxy[0].tolist()
            ])

    rows.append({
        "image": image_path.name,
        "confidence_threshold": CONFIDENCE,
        "nms_iou": NMS_IOU,
        "detection_count": count,
        "confidence_scores": ";".join(map(str, scores)),
        "bounding_boxes_xyxy": repr(coordinates),
    })

    print(f"\nImage: {image_path.name}")
    print(f"Detections: {count}")
    print(f"Confidence scores: {scores}")

with CSV_PATH.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"\nCSV saved to: {CSV_PATH}")
print(f"Annotated images saved under: {OUTPUT_DIR}")
