```python
from pathlib import Path
import base64
import cv2
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = (
    BASE_DIR
    / "runs"
    / "pothole_finetune"
    / "weights"
    / "best.pt"
)

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

print(f"Loading pothole model: {MODEL_PATH}")
model = YOLO(str(MODEL_PATH))


def detect_potholes(image_path: str):
    results = model.predict(
        source=image_path,
        conf=0.45,
        iou=0.45,
        verbose=False,
    )

    result = results[0]
    detections = []

    if result.boxes is not None:
        for box in result.boxes:
            coords = box.xyxy[0].tolist()
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            detections.append({
                "class_id": class_id,
                "class_name": result.names[class_id],
                "confidence": round(confidence, 4),
                "bbox": {
                    "x1": round(coords[0], 2),
                    "y1": round(coords[1], 2),
                    "x2": round(coords[2], 2),
                    "y2": round(coords[3], 2),
                },
            })
    # Draw bounding boxes and labels on the original image.
    annotated_image = result.plot()

    # Encode the annotated image as JPEG and then Base64.
    success, encoded_image = cv2.imencode(
        ".jpg",
        annotated_image,
        [cv2.IMWRITE_JPEG_QUALITY, 85],
    )

    if not success:
        raise RuntimeError("Could not encode the annotated image.")

    image_base64 = base64.b64encode(
        encoded_image.tobytes()
    ).decode("utf-8")

    return {
        "image_width": int(result.orig_shape[1]),
        "image_height": int(result.orig_shape[0]),
        "count": len(detections),
        "detections": detections,
        "annotated_image": f"data:image/jpeg;base64,{image_base64}",
    }
```
