
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from detector import detect_potholes

app = FastAPI(
    title="Legioners Pothole Detection API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Legioners Pothole Detection API is running"}


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Legioners Pothole Detection API",
    }


@app.post("/api/v1/detect")
async def detect_image(file: UploadFile = File(...)):
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
            raise HTTPException(
                status_code=422,
                detail="Could not process the uploaded image.",
            ) from exc

        result["filename"] = file.filename or "uploaded-image"
        return result

    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        await file.close()