
from pathlib import Path

from ultralytics import YOLO
from huggingface_hub import hf_hub_download

BASE_DIR = Path(__file__).resolve().parent
DATA_YAML = BASE_DIR / "pothole_data.yaml"
FINETUNED_WEIGHTS = (
    BASE_DIR / "runs" / "pothole_finetune" / "weights" / "best.pt"
)

if not FINETUNED_WEIGHTS.exists():
    raise FileNotFoundError(
        f"Fine-tuned model not found: {FINETUNED_WEIGHTS}"
    )

print("\nDownloading or locating original model...")

original_weights = hf_hub_download(
    repo_id="Samdutse/pothole-yolov8",
    filename="best.pt",
)

models = [
    ("original", original_weights),
    ("finetuned", str(FINETUNED_WEIGHTS)),
]

for model_name, weights in models:
    print(f"\n{'=' * 50}")
    print(f"Evaluating {model_name.upper()} model on TEST data")
    print(f"{'=' * 50}")

    model = YOLO(weights)

    metrics = model.val(
        data=str(DATA_YAML),
        split="test",
        imgsz=640,
        batch=4,
        device="cpu",
        workers=0,
        project=str(BASE_DIR / "runs" / "evaluation"),
        name=f"{model_name}_test",
        exist_ok=True,
        plots=True,
    )

    print(f"\nResults for {model_name}:")
    print(f"Precision: {metrics.box.mp:.4f}")
    print(f"Recall:    {metrics.box.mr:.4f}")
    print(f"mAP50:     {metrics.box.map50:.4f}")
    print(f"mAP50-95:  {metrics.box.map:.4f}")

print("\nBoth model evaluations completed!")