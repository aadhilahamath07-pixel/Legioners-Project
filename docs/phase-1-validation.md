# Phase 1 — Pothole Detection Model Validation

## 1. Objective

Set up and test a pretrained YOLOv8 pothole-detection model on sample road images, inspect its predictions, and select a provisional confidence threshold for further development.

## 2. Model and Environment

* **Model repository:** `Samdutse/pothole-yolov8` on Hugging Face
* **Model weights:** `best.pt`
* **Inference framework:** Ultralytics YOLO
* **Programming language:** Python
* **Execution environment:** Python virtual environment in the backend
* **Hardware acceleration:** Not yet documented; record whether CPU or GPU was used.

## 3. Test Dataset

Five sample images were used:

* `normal_road_01.jpg`
* `normal_road_02.jpg`
* `road_pothole_01.jpg`
* `road_pothole_02.jpg`
* `road_pothole_03.jpg`

These images provide an initial visual test set. They are not a sufficiently large or formally labelled dataset for reliable accuracy measurement.

## 4. Confidence Threshold Comparison

| Image                | Threshold 0.25 | Threshold 0.50 | Threshold 0.65 |
| -------------------- | -------------: | -------------: | -------------: |
| normal_road_01.jpg   |              5 |              5 |              4 |
| normal_road_02.jpg   |             10 |              7 |              4 |
| road_pothole_01.jpg  |             15 |              8 |              1 |
| road_pothole_02.jpg  |             18 |              6 |              5 |
| road_pothole_03.jpg  |             14 |              5 |              3 |
| **Total detections** |         **62** |         **31** |         **17** |

Detection counts represent model output boxes, not confirmed pothole counts.

## 5. Visual Inspection

Based on the initial visual inspection at confidence threshold 0.50:

* No incorrect boxes were noticed on the normal-road test images.
* All visible potholes appeared to be detected in the pothole test images.
* No obvious duplicate or overlapping boxes were noticed.

These observations are preliminary and have not been verified against ground-truth annotations.

## 6. Provisional Threshold Selection

The confidence threshold of **0.50** was selected as the provisional setting for subsequent testing.

The 0.25 threshold generated more detections overall, while 0.65 generated fewer detections and retained only one detection for `road_pothole_01.jpg`.

The 0.50 setting provides a practical starting point, but it has not been established as the optimal threshold.

## 7. Current Results

* The pretrained model loaded and ran on the sample images.
* Predictions were generated and saved for visual inspection.
* A CSV comparison of confidence thresholds was generated.
* Annotated predictions were saved under `backend/runs/threshold_comparison/`.

## 8. Limitations

* Only five sample images were tested.
* Ground-truth bounding-box annotations and formal evaluation metrics have not been established.
* Detection counts alone do not measure precision, recall, or model accuracy.
* Performance in different lighting, weather, road conditions, and camera angles remains untested.
* The model's licence and usage terms must be checked before commercial deployment.
* The provisional threshold may need adjustment after testing on a larger, labelled dataset.

## 9. Next Steps

1. Confirm that the normal-road images are genuinely free of potholes and investigate any model detections on them.
2. Expand the dataset with diverse road images.
3. Create or obtain ground-truth annotations.
4. Evaluate precision, recall, and other suitable metrics.
5. Integrate the validated model into the application after the initial validation stage.

**Phase 1 status:** Initial setup, five-image testing, visual inspection, and threshold comparison completed. Documentation is in progress. Further validation is required before claiming production readiness.
