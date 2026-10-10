# Legioners Road Intelligence

AI-powered road inspection prototype for detecting potholes in road images using a YOLO object-detection model, a FastAPI backend, and a React + Vite frontend.

## Overview

Legioners Road Intelligence lets users upload road images and run pothole detection through a web interface. The backend processes each image using a trained YOLO model and returns detection labels, confidence scores, bounding-box coordinates, and an annotated image highlighting the detected potholes.

## Features

- Upload JPG, PNG, or WEBP images (maximum 10 MB).
- Detect potholes using a YOLO model.
- Display detection labels, confidence scores, and bounding boxes.
- View annotated images returned by the detection API.
- Explore a React dashboard with report and inspection-record views.
- Export available inspection records to CSV.
- Configure the backend URL using an environment variable.

**Note:** Dashboard metrics and initial records are sample data. Inspection records are not currently stored in a persistent database. Model weights and datasets must be supplied separately.

## Tech Stack

| Component | Technology |
|---|---|
| Object detection | Ultralytics YOLO |
| Backend | Python, FastAPI, Uvicorn |
| Image processing | OpenCV, NumPy |
| Frontend | React, Vite, JavaScript |
| API communication | HTTP multipart uploads and JSON |

## Project Structure

```text
Legioners-Project/
├── backend/
│   ├── main.py
│   ├── detector.py
│   ├── requirements.txt
│   └── pothole_data.yaml
├── data/                 # Local datasets; not committed
├── docs/                 # Project documentation
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.10+ with compatible PyTorch and Ultralytics dependencies.
- Node.js and npm.
- Git.
- The trained model checkpoint at:

```text
backend/runs/pothole_finetune/weights/best.pt
```

The model checkpoint is not included in the repository and must be obtained separately.

## Installation and Setup

### 1. Start the backend

From the project root, open a terminal and run:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Make sure the trained model exists at the checkpoint path listed above.

Start the API from the `backend` directory:

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Backend URL: `http://127.0.0.1:8000`

Interactive API documentation: `http://127.0.0.1:8000/docs`

### 2. Start the frontend

Open a second terminal from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

The frontend uses `http://127.0.0.1:8000` by default. To configure another API URL, create `frontend/.env`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Restart Vite after changing this setting. Never place secrets in frontend environment variables.

## API Documentation

### `GET /`

Returns a message indicating that the API is running.

### `GET /health`

Returns the service health status.

### `POST /api/v1/detect`

Accepts an image using `multipart/form-data`.

**Request requirements**

- File field: `file`
- Supported formats: JPG, PNG, WEBP
- Maximum file size: 10 MB

**Response fields**

| Field | Description |
|---|---|
| `filename` | Uploaded filename |
| `image_width` | Original image width |
| `image_height` | Original image height |
| `count` | Number of detected objects |
| `detections` | Detection labels, confidence scores, and bounding boxes |
| `annotated_image` | Annotated JPEG encoded as a Base64 data URI |

Each detection includes `class_id`, `class_name`, `confidence`, and `bbox` coordinates (`x1`, `y1`, `x2`, `y2`).

## Model and Dataset

The current inference implementation uses a confidence threshold of `0.45` and an IoU threshold of `0.45`.

The dataset configuration expects data under `data/potholes/dataset`, with training, validation, and test image directories. Dataset files and generated model outputs are excluded from Git and must be supplied separately when reproducing training.

## Testing

1. Start the backend and check `GET /health`.
2. Open `http://127.0.0.1:8000/docs`.
3. Test `POST /api/v1/detect` with a supported image.
4. Start the frontend and upload the same image.
5. Verify the annotated image, detection count, confidence scores, and bounding boxes.
6. Evaluate false positives and missed detections using a representative validation dataset.

Frontend checks:

```bash
npm run lint
npm run build
```

Run these commands from the `frontend` directory.

## Current Limitations

- Model weights and datasets are not included in the repository.
- Detection accuracy depends on the trained model and input conditions.
- Dashboard metrics and initial records are illustrative sample data.
- Inspection records are not persisted to a database.
- GPS-based mapping and pothole severity assessment are planned enhancements, not completed features.
- Further validation is required before real-world operational use.

## Roadmap

- [ ] Evaluate model precision, recall, and detection reliability.
- [ ] Improve robustness across lighting, weather, and road conditions.
- [ ] Investigate pothole severity classification.
- [ ] Add GPS-based location capture and map visualization.
- [ ] Introduce persistent inspection records and reporting.
- [ ] Prepare secure deployment and operational monitoring.

## Contributing

1. Create a feature branch.
2. Keep datasets, model checkpoints, virtual environments, generated outputs, and secrets out of Git.
3. Run relevant backend checks and frontend lint/build commands.
4. Submit a pull request describing the changes and tests performed.

## Disclaimer

Legioners Road Intelligence is a prototype intended to assist road-condition inspection. Its predictions should be verified and should not replace on-site assessment or professional road-safety decisions.
