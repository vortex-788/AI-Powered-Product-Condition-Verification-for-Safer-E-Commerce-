"""
VeriShield AI Service - Product Condition Verification Engine
FastAPI server providing damage detection, video analysis, and fraud comparison.
"""
import os
import io
import uuid
import tempfile
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import numpy as np
from PIL import Image
import cv2
import re

from services.damage_detector import DamageDetector
from services.video_processor import VideoProcessor
from services.fraud_comparator import FraudComparator

app = FastAPI(
    title="VeriShield AI Service",
    description="AI-Powered Product Condition Verification Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
damage_detector = DamageDetector()
video_processor = VideoProcessor(damage_detector)
fraud_comparator = FraudComparator()


@app.get("/")
async def root():
    return {"service": "VeriShield AI Engine", "version": "1.0.0", "status": "active"}


@app.get("/health")
async def health():
    return {"status": "healthy", "models_loaded": True}


def validate_file(file: UploadFile):
    allowed_file_types = ["jpg", "jpeg", "png", "mp4", "avi"]
    max_file_size = 1024 * 1024 * 50
    filename = file.filename
    if not re.match("^[a-zA-Z0-9._-]+$", filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if filename.split(".")[-1].lower() not in allowed_file_types:
        raise HTTPException(status_code=400, detail=f"Only {', '.join(allowed_file_types)} files are allowed")
    if file.file.size > max_file_size:
        raise HTTPException(status_code=400, detail=f"File size exceeds {max_file_size / (1024 * 1024)}MB limit")


def validate_query_param(param: str):
    if not re.match("^[a-zA-Z0-9._-]+$", param):
        raise HTTPException(status_code=400, detail="Invalid query parameter")


@app.post("/analyze/image")
async def analyze_image(file: UploadFile = File(...), query_param: str = Query(None)):
    """Analyze a product image for damage detection."""
    try:
        validate_file(file)
        if query_param:
            validate_query_param(query_param)
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        image_np = np.array(image)
        image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

        result = damage_detector.analyze(image_cv)
        return JSONResponse(content=result)
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")
    except cv2.error as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.post("/analyze/video")
async def analyze_video(file: UploadFile = File(...)):
    """Analyze a product video by extracting and processing frames."""
    try:
        validate_file(file)
        # Save video to temp file
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        result = video_processor.analyze_video(tmp_path)

        # Cleanup
        os.unlink(tmp_path)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare")
async def compare_images(
    original: UploadFile = File(...),
    returned: UploadFile = File(...)
):
    """Compare original vs returned product images for fraud detection."""
    try:
        validate_file(original)
        validate_file(returned)
        orig_contents = await original.read()
        ret_contents = await returned.read()

        orig_image = np.array(Image.open(io.BytesIO(orig_contents)).convert("RGB"))
        ret_image = np.array(Image.open(io.BytesIO(ret_contents)).convert("RGB"))

        orig_cv = cv2.cvtColor(orig_image, cv2.COLOR_RGB2BGR)
        ret_cv = cv2.cvtColor(ret_image, cv2.COLOR_RGB2BGR)

        result = fraud_comparator.compare(orig_cv, ret_cv)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/validate")
async def validate(query_param: str = Query(...)):
    try:
        validate_query_param(query_param)
        return JSONResponse(content={"message": "Query parameter is valid"}, status_code=200)
    except HTTPException as e:
        return JSONResponse(content={"message": "Query parameter is invalid"}, status_code=e.status_code)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)