
from pathlib import Path
from ultralytics import YOLO

# Paths
base = Path(__file__).resolve().parent
config = base / "pothole_data_with_negatives.yaml"
original_model = base / "runs" / "pothole_finetune" / "weights" / "best.pt"

if not config.exists():
    raise FileNotFoundError(f"Dataset config not found: {config}")

if not original_model.exists():
    raise FileNotFoundError(f"Starting model not found: {original_model}")

# Load the existing fine-tuned model
model = YOLO(str(original_model))

# Train a new experiment
results = model.train(
    data=str(config),
    epochs=30,
    imgsz=640,
    batch=4,
    device="cpu",
    workers=0,
    project=str(base / "runs"),
    name="pothole_with_negatives",
    exist_ok=False,
    patience=10,
    plots=True
)

print("\nTraining finished.")
print("New best model should be at:")
print(base / "runs" / "pothole_with_negatives" / "weights" / "best.pt")