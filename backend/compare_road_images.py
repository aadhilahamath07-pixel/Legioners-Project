
from pathlib import Path

from ultralytics import YOLO
from huggingface_hub import hf_hub_download

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "test_images"
OUTPUT_DIR = BASE_DIR / "runs" / "road_comparison"
FINETUNED_WEIGHTS = (
    BASE_DIR / "runs" / "pothole_finetune" / "weights" / "best.pt"
)

if not IMAGE_DIR.exists():
    raise FileNotFoundError(f"Image folder not found: {IMAGE_DIR}")

if not FINETUNED_WEIGHTS.exists():
    raise FileNotFoundError(f"Fine-tuned model not found: {FINETUNED_WEIGHTS}")

original_weights = hf_hub_download(
    repo_id="Samdutse/pothole-yolov8",
    filename="best.pt",
)

models = [
    ("original", original_weights),
    ("finetuned", str(FINETUNED_WEIGHTS)),
]

for name, weights in models:
    print(f"\nTesting {name} model...")
    model = YOLO(weights)

    model.predict(
        source=str(IMAGE_DIR),
        imgsz=640,
        conf=0.50,
        iou=0.45,
        device="cpu",
        save=True,
        save_txt=True,
        save_conf=True,
        project=str(OUTPUT_DIR),
        name=name,
        exist_ok=True,
    )

print("\nComparison complete!")
print(f"Original predictions: {OUTPUT_DIR / 'original'}")
print(f"Fine-tuned predictions: {OUTPUT_DIR / 'finetuned'}")