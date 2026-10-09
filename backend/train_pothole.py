
from pathlib import Path
from ultralytics import YOLO
from huggingface_hub import hf_hub_download

BASE_DIR = Path(__file__).resolve().parent
DATA_YAML = BASE_DIR / "pothole_data.yaml"

print("Downloading or locating pretrained pothole weights...")
weights_path = hf_hub_download(
    repo_id="Samdutse/pothole-yolov8",
    filename="best.pt",
)

print("Loading model...")
model = YOLO(weights_path)

print("Starting fine-tuning...")
model.train(
    data=str(DATA_YAML),
    epochs=30,
    imgsz=640,
    batch=4,
    device="cpu",
    workers=0,
    patience=8,
    project=str(BASE_DIR / "runs"),
    name="pothole_finetune",
    exist_ok=False,
    seed=42,
)

print("Training completed.")
print("Check backend/runs/pothole_finetune/weights/best.pt")