
from pathlib import Path
import csv
from ultralytics import YOLO
from huggingface_hub import hf_hub_download

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "test_images"
OUTPUT_DIR = BASE_DIR / "runs" / "validation"
CSV_PATH = BASE_DIR / "validation_results.csv"

if not IMAGE_DIR.exists():
    raise FileNotFoundError(f"Create this folder first: {IMAGE_DIR}")

images = [
    p for p in IMAGE_DIR.iterdir()
    if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
]

if not images:
    raise ValueError("Add road images to the test_images folder.")

weights = hf_hub_download(
    repo_id="Samdutse/pothole-yolov8",
    filename="best.pt"
)

model = YOLO(weights)

rows = []

for image_path in sorted(images):
    results = model.predict(
        source=str(image_path),
        conf=0.25,
        imgsz=640,
        save=True,
        project=str(OUTPUT_DIR),
        name="predictions",
        exist_ok=True,
        verbose=False
    )

    result = results[0]
    count = len(result.boxes)
    confidences = result.boxes.conf.tolist()

    rows.append({
        "image": image_path.name,
        "detections": count,
        "max_confidence": round(max(confidences), 4)
        if confidences else "",
        "all_confidences": ";".join(
            f"{c:.4f}" for c in confidences
        )
    })

    print(
        f"{image_path.name}: "
        f"{count} pothole(s), "
        f"confidence(s)={confidences}"
    )

with CSV_PATH.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"\nImages tested: {len(rows)}")
print(f"Results CSV: {CSV_PATH}")
print(f"Annotated images: {OUTPUT_DIR / 'predictions'}")
print("Validation run completed.")