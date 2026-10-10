
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import (
    get_inspections,
    save_inspection,
    update_inspection_priority,
    update_inspection_status,
)
from detector import detect_potholes
from prioritization import calculate_priority

app = FastAPI(
    title="Legioners Pothole Detection API",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)


class StatusUpdate(BaseModel):
    status: str


class PriorityFactors(BaseModel):
    severity: float = Field(ge=0, le=100)
    traffic: float = Field(ge=0, le=100)
    road_importance: float = Field(ge=0, le=100)
    location_risk: float = Field(ge=0, le=100)
    accessibility: float = Field(ge=0, le=100)
    emergency_override: bool = False


@app.get("/")
def home():
    return {"message": "Legioners Pothole Detection API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Legioners Pothole Detection API"}


@app.get("/api/v1/inspections")
def inspection_history():
    return {"inspections": get_inspections()}


@app.patch("/api/v1/inspections/{inspection_id}/status")
def change_inspection_status(inspection_id: int, payload: StatusUpdate):
    if payload.status not in {"Pending", "In Progress", "Resolved"}:
        raise HTTPException(
            status_code=422,
            detail="Status must be Pending, In Progress, or Resolved.",
        )

    try:
        inspection = update_inspection_status(inspection_id, payload.status)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not update inspection status.",
        ) from exc

    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    return {"inspection": inspection}


@app.patch("/api/v1/inspections/{inspection_id}/priority")
def set_inspection_priority(inspection_id: int, payload: PriorityFactors):
    factors = {
        "severity": payload.severity,
        "traffic": payload.traffic,
        "road_importance": payload.road_importance,
        "location_risk": payload.location_risk,
        "accessibility": payload.accessibility,
    }

    try:
        priority_result = calculate_priority(
            factors,
            emergency_override=payload.emergency_override,
        )
        inspection = update_inspection_priority(
            inspection_id,
            priority_result,
            factors,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not calculate or save inspection priority.",
        ) from exc

    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    return {"inspection": inspection}


@app.post("/api/v1/detect")
async def detect_image(
    file: UploadFile = File(...),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
):
    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    max_size = 10 * 1024 * 1024

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail="Upload a JPG, PNG, or WEBP image.",
        )

    temp_path = None

    try:
        contents = await file.read(max_size + 1)

        if not contents:
            raise HTTPException(status_code=400, detail="Empty image.")

        if len(contents) > max_size:
            raise HTTPException(
                status_code=413,
                detail="Image must be 10 MB or smaller.",
            )

        with NamedTemporaryFile(
            suffix=allowed_types[file.content_type],
            delete=False,
        ) as temp_file:
            temp_file.write(contents)
            temp_path = Path(temp_file.name)

        try:
            result = detect_potholes(str(temp_path))
        except Exception as exc:
            import logging
            logging.exception("Pothole detection failed")
            raise HTTPException(
                status_code=422,
                detail="Could not process the uploaded image.",
            ) from exc

        if (latitude is None) != (longitude is None):
            raise HTTPException(
                status_code=422,
                detail="Latitude and longitude must be provided together.",
            )

        if latitude is not None and not (-90 <= latitude <= 90):
            raise HTTPException(
                status_code=422,
                detail="Latitude must be between -90 and 90.",
            )

        if longitude is not None and not (-180 <= longitude <= 180):
            raise HTTPException(
                status_code=422,
                detail="Longitude must be between -180 and 180.",
            )

        result["filename"] = file.filename or "uploaded-image"
        result["latitude"] = latitude
        result["longitude"] = longitude

        # Save the inspection first, preserving the existing workflow.
        try:
            saved_inspection = save_inspection(result)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Detection succeeded, but saving the inspection failed.",
            ) from exc

        result["inspection_id"] = saved_inspection["id"]
        result["status"] = saved_inspection["status"]
        result["created_at"] = saved_inspection["created_at"]
        result["latitude"] = saved_inspection.get("latitude")
        result["longitude"] = saved_inspection.get("longitude")

        # Prototype mappings only; not calibrated severity measurements.
        severity_values = {
            "Low": 25.0,
            "Medium": 55.0,
            "High": 85.0,
        }

        detected_severities = [
            detection.get("severity")
            for detection in result["detections"]
            if detection.get("severity") in severity_values
        ]

        # Use the highest estimated severity for this inspection.
        factors = {
            "severity": (
                max(severity_values[level] for level in detected_severities)
                if detected_severities
                else None
            ),
            "traffic": None,
            "road_importance": None,
            "location_risk": None,
            "accessibility": None,
        }

        priority_result = None

        if factors["severity"] is not None:
            try:
                priority_result = calculate_priority(factors)

                saved_inspection = update_inspection_priority(
                    saved_inspection["id"],
                    priority_result,
                    factors,
                )
            except Exception:
                import logging
                logging.exception("Automatic priority calculation failed")
                priority_result = None

        if priority_result is not None and saved_inspection is not None:
            result["priority_score"] = saved_inspection["priority_score"]
            result["priority_level"] = saved_inspection["priority_level"]
            result["priority_explanation"] = (
                saved_inspection["priority_explanation"]
            )
            result["priority_factors"] = saved_inspection["priority_factors"]
        else:
            result["priority_score"] = None
            result["priority_level"] = None
            result["priority_explanation"] = (
                "Priority not calculated because no severity estimate was "
                "available or automatic priority saving failed."
            )
            result["priority_factors"] = factors

        return result

    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

        await file.close()
