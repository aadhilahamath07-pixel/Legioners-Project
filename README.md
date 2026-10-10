
# Legioners Road Intelligence

**AI-powered road inspection and pothole detection platform**

Legioners Road Intelligence is a prototype that uses computer vision to detect potholes in road images and supports inspection management and maintenance prioritization. It combines a YOLO object-detection model, a FastAPI backend, and a React dashboard to help organize road-condition inspections.

> **Project status:** Working local prototype. Model performance, severity estimates, and prioritization logic require further validation before operational use.

## Overview

Road-condition inspections can involve reviewing large numbers of images and identifying defects that require attention. Legioners aims to streamline this workflow by combining automated pothole detection with inspection records and decision-support functionality.

Users can upload a road image through the web interface. The backend processes the image using a trained YOLO model and returns detected potholes, confidence scores, bounding-box coordinates, and an annotated image.

## Key Features

- **AI-powered pothole detection:** Uses a trained YOLO object-detection model.
- **Image upload:** Supports JPG, PNG, and WEBP images up to 10 MB.
- **Detection visualization:** Displays detected potholes, confidence scores, and bounding boxes.
- **Annotated output:** Returns an image highlighting detected objects.
- **Inspection dashboard:** Provides a frontend for reviewing inspection information.
- **Inspection records:** Includes backend database functionality for inspection-history management.
- **Maintenance prioritization:** Includes a prioritization module intended to support maintenance decisions.
- **Severity assessment:** Includes a severity-related module that requires validation against real-world examples.
- **CSV export:** Supports exporting available inspection records where exposed by the application.
- **Configurable API URL:** Allows the frontend to connect to a configured backend endpoint.

Feature availability may depend on the current application configuration. Severity estimates and prioritization should be treated as decision-support outputs, not definitive engineering assessments.

## System Architecture

The application follows a frontend–backend architecture.

```text
                User
                 |
                 v
        React + Vite Frontend
                 |
          HTTP image upload
                 |
                 v
          FastAPI Backend
                 |
                 v
        YOLO Object Detection
                 |
        +--------+---------+
        |                  |
        v                  v
 Detection Results    Annotated Image
        |
        v
 Inspection and
 Prioritization Modules
        |
        v
     SQLite Database
```

The diagram represents the intended component flow. The exact data flow depends on the routes and integrations enabled in the current implementation.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite, JavaScript, CSS |
| Backend API | Python, FastAPI, Uvicorn |
| Object detection | Ultralytics YOLO |
| Image processing | OpenCV, NumPy |
| Data storage | SQLite |
| API communication | HTTP, multipart/form-data, JSON |
| Version control | Git, GitHub |

## Repository Structure

```text
Legioners-Project/
├── backend/
│   ├── main.py
│   ├── detector.py
│   ├── database.py
│   ├── prioritization.py
│   ├── severity.py
│   ├── audit_pothole_dataset.py
│   ├── label_severity.py
│   ├── prepare_severity_crops.py
│   ├── prepare_severity_dataset.py
│   ├── pothole_data_with_negatives.yaml
│   └── requirements.txt
├── docs/
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
├── .gitignore
├── README.md
└── readme.txt
```

*This is a high-level overview; additional configuration and generated files may exist locally.*

## Prerequisites

Install the following before running the application:

- Git
- Python 3.10 or a compatible version supported by the project's dependencies
- Node.js and npm
- A compatible PyTorch and Ultralytics installation
- The trained YOLO checkpoint used by the detector

The trained model weights and datasets are supplied separately and may not be included in the repository.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/aadhilahamath07-pixel/Legioners-Project.git
cd Legioners-Project
```

### 2. Set up the backend

From the project root, create and activate a virtual environment:

```powershell
py -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
```

Install the backend dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

If PowerShell prevents environment activation, use Command Prompt instead:

```cmd
backend\.venv\Scripts\activate.bat
```

Make sure the trained model checkpoint is available at the path expected by `backend/detector.py`. For the current local setup, this may be:

```text
backend/runs/pothole_finetune/weights/best.pt
```

If the checkpoint is stored elsewhere, update the model path in the backend configuration as appropriate.

Start the backend from the project root:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000 --app-dir backend
```

The local backend address is:

`http://127.0.0.1:8000`

If enabled, interactive API documentation is available at:

`http://127.0.0.1:8000/docs`

### 3. Set up the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, typically:

`http://localhost:5173`

The frontend uses the configured backend URL. To override it, create a `frontend/.env` file:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Restart the Vite development server after changing environment variables. Never place secrets in frontend environment variables.

## API Overview

The current local integration uses the following detection endpoint:

### `POST /predict`

Uploads an image to the detection backend.

**Request format:** `multipart/form-data`

| Parameter | Description |
|---|---|
| `file` | Image to process |

Supported formats are JPG, PNG, and WEBP, with a maximum upload size of 10 MB in the frontend.

The response contains detection results and annotated image data according to the backend implementation. Detection information includes object labels, confidence scores, and bounding-box coordinates.

The frontend and backend must agree on the endpoint, request field name, and response structure. Consult the running API documentation and `backend/main.py` for the authoritative contract.

## Model Configuration

The detector uses confidence and Intersection over Union (IoU) thresholds to control detection filtering and non-maximum suppression.

The current configured values are:

| Parameter | Value |
|---|---:|
| Confidence threshold | 0.45 |
| IoU threshold | 0.45 |

These are inference settings, not model-accuracy measurements.

The model's reliability should be evaluated using a held-out dataset containing varied road conditions, lighting, camera angles, and examples without potholes. Precision, recall, and mean Average Precision (mAP) should be reported only after they have been measured on an appropriate evaluation set.

## Testing

Use the following workflow to test the local application:

1. Start the backend and verify that it starts without errors.
2. Open the API documentation, if enabled.
3. Submit a supported road image to `POST /predict`.
4. Start the frontend and upload the same image.
5. Verify the detection count, labels, confidence scores, bounding boxes, and annotated image.
6. Test representative images containing potholes and images without potholes.
7. Verify inspection-record and prioritization workflows that are enabled in the current application.

Frontend checks can be run from the `frontend` directory:

```bash
npm run lint
npm run build
```

These commands depend on the corresponding scripts being defined in `frontend/package.json`.

## Limitations

- The trained model weights and datasets may need to be obtained separately.
- Detection performance depends on the model, image quality, and road conditions.
- False positives and missed potholes are possible.
- Severity assessment and maintenance prioritization require validation against real-world inspection data.
- Local database contents are environment-specific and should not be assumed to be shared with another installation.
- The prototype has not been established as a replacement for professional road inspection or engineering assessment.
- Production deployment requires appropriate security, storage, monitoring, and performance testing.

## Future Scope

- Evaluate detection precision, recall, and mAP on a representative test dataset.
- Improve robustness under different lighting, weather, and road-surface conditions.
- Validate severity classification using expert-labelled data.
- Refine maintenance prioritization using road importance, traffic exposure, and validated severity information.
- Improve inspection location capture and map-based visualization where required.
- Strengthen duplicate-report handling and inspection-history management.
- Prepare secure deployment with suitable persistent storage and operational monitoring.

## Contributing

Contributions and suggestions are welcome.

1. Create a feature branch.
2. Keep secrets, local databases, virtual environments, datasets, and generated model outputs out of Git unless explicitly required and appropriately licensed.
3. Run relevant backend and frontend checks.
4. Submit a pull request describing the changes and tests performed.

## Disclaimer

Legioners Road Intelligence is a prototype intended to assist road-condition inspection. Its outputs are estimates and should be verified by qualified personnel. The platform should not replace on-site inspection, professional engineering judgement, or established road-safety procedures.

## Repository

[View Legioners Road Intelligence on GitHub](https://github.com/aadhilahamath07-pixel/Legioners-Project)

