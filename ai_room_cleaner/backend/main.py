from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, JSONResponse
from .services import ai_service, camera_service
import logging
import base64

app = FastAPI()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, e: Exception):
    logging.error(f"Unhandled Exception: {str(e)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred. Please check the logs."},
    )

@app.get("/api/tasks")
async def get_tasks():
    return []

@app.post("/api/analyze")
async def analyze_room():
    image_base64 = camera_service.get_camera_image()
    if not image_base64:
        return JSONResponse(status_code=500, content={"error": "Could not retrieve image from camera."})
    messes = ai_service.analyze_room_for_mess(image_base64)
    return messes

@app.get("/api/camera/image")
async def get_camera_image():
    image_base64 = camera_service.get_camera_image()
    if image_base64:
        image_bytes = base64.b64decode(image_base64)
        return Response(content=image_bytes, media_type="image/jpeg")
    return JSONResponse(status_code=404, content={"error": "Image not found"})

app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")