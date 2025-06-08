from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .services import ai_service, camera_service

app = FastAPI()

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