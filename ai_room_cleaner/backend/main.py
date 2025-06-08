from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from .services import ai_service, camera_service
import logging

app = FastAPI()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, e: Exception):
    logging.error(f"Unhandled Exception: {str(e)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred. Please check the logs."},
    )

@app.post("/api/tasks")
async def create_task():
    return {"message": "Task created successfully"}

@app.get("/api/tasks")
async def get_tasks():
    return []

@app.put("/api/tasks/{task_id}")
async def update_task(task_id: int):
    return {"message": f"Task {task_id} updated successfully"}

@app.post("/api/analyze")
async def analyze_room():
    image_path = camera_service.get_image_path()
    analysis = ai_service.analyze_room_for_mess(image_path)
    return analysis

@app.get("/api/camera/image")
async def get_camera_image():
    image_path = camera_service.get_image_path()
    return FileResponse(image_path, media_type="image/jpeg")

app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")