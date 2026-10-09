
from pathlib import Path
from ultralytics import YOLO

base = Path(__file__).resolve().parent

config = base / "pothole_data_with_negatives.yaml"
starting_weights = (
    base / "runs" / "pothole_finetune" / "weights" / "best.pt"
)

if not config.exists():
    raise FileNotFoundError(f"Dataset config not found: {config}")

if not starting_weights.exists():
    raise FileNotFoundError(
        f"Starting model not found: {starting_weights}"
    )

print(f"Dataset: {config}")
print(f"Starting weights: {starting_weights}")

model = YOLO(str(starting_weights))

results = model.train(
    data=str(config),
    epochs=30,
    imgsz=640,
    batch=4,
    device="cpu",
    workers=0,
    project=str(base / "runs"),
    name="pothole_with_negatives_v2",
    exist_ok=False,
    patience=10,
    plots=True,
    seed=42,
)

print("\nTraining finished.")
print(
    "Best weights:",
    base / "runs" / "pothole_with_negatives_v2" / "weights" / "best.pt",
)
print(
    "Latest weights:",
    base / "runs" / "pothole_with_negatives_v2" / "weights" / "last.pt",
)
