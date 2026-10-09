
from pathlib import Path

from ultralytics import YOLO
from huggingface_hub import hf_hub_download

BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "test_road.jpg"
OUTPUT_DIR = BASE_DIR / "runs" / "improved_test"

CONFIDENCE = 0.50
IMAGE_SIZE = 640

if not IMAGE_PATH.exists():
    raise FileNotFoundError(
        f"Add test_road.jpg to: {BASE_DIR}"
    )

print("Downloading or loading the pothole model...")

weights_path = hf_hub_download(
    repo_id="Samdutse/pothole-yolov8",
    filename="best.pt",
)

model = YOLO(weights_path)

print("Running pothole detection...")

results = model.predict(
    source=str(IMAGE_PATH),
    conf=CONFIDENCE,
    imgsz=IMAGE_SIZE,
    iou=0.45,
    save=True,
    project=str(OUTPUT_DIR.parent),
    name=OUTPUT_DIR.name,
    exist_ok=True,
    verbose=False,
)

for result in results:
    boxes = result.boxes

    print(f"\nImage: {IMAGE_PATH.name}")
    print(f"Confidence threshold: {CONFIDENCE}")
    print(f"Detections: {len(boxes) if boxes is not None else 0}")

    if boxes is not None:
        for index, box in enumerate(boxes, start=1):
            class_id = int(box.cls.item())
            confidence = float(box.conf.item())
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            class_name = result.names[class_id]

            print(
                f"{index}. Class: {class_name} | "
                f"Confidence: {confidence:.3f} | "
                f"Box: ({x1:.1f}, {y1:.1f}, "
                f"{x2:.1f}, {y2:.1f})"
            )

    print(f"Annotated image saved to: {result.save_dir}")

print("\nTest completed!")