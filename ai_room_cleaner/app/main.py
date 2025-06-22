import asyncio
import json
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from app.core.config import settings
from app.core.logging import log
from app.services.ai_service import AIService
from app.services.camera_service import CameraService
from app.services.ha_service import HomeAssistantService
from app.services.history_service import HistoryService
from app.core.exceptions import AIError as AIProviderError, CameraError, HomeAssistantError as HomeAssistantAPIError

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting up AI Room Cleaner...")
    app.state.ai_service = AIService()
    app.state.camera_service = CameraService()
    app.state.ha_service = HomeAssistantService()
    app.state.history_service = HistoryService()
    
    loop = asyncio.get_event_loop()
    app.state.background_task = loop.create_task(run_analysis_periodically())
    
    yield
    
    log.info("Shutting down AI Room Cleaner...")
    app.state.background_task.cancel()
    try:
        await app.state.background_task
    except asyncio.CancelledError:
        log.info("Background task cancelled successfully.")

app = FastAPI(lifespan=lifespan)

async def run_single_analysis():
    """
    This function orchestrates a single run of the room analysis process.
    """
    log.info("Starting new analysis cycle.")
    
    ai_service: AIService = app.state.ai_service
    camera_service: CameraService = app.state.camera_service
    ha_service: HomeAssistantService = app.state.ha_service
    history_service: HistoryService = app.state.history_service

    try:
        # 1. Get camera image
        image_bytes = await camera_service.get_camera_image()
        log.info(f"Successfully retrieved image, size: {len(image_bytes)} bytes.")

        # 2. Analyze image with AI
        analysis_result = await ai_service.analyze_image(image_bytes)
        log.info(f"Successfully received AI analysis.")

        # 3. Process the result
        if ai_service.provider == 'openai':
            content = analysis_result['choices'][0]['message']['content']
        else: # google
            content = analysis_result['candidates'][0]['content']['parts'][0]['text']
        
        # Clean the content
        cleaned_content = content.strip().replace("```json", "").replace("```", "")
        data = json.loads(cleaned_content)
        
        score = data.get("cleanliness_score")
        tasks = data.get("cleaning_tasks", [])

        # 4. Update Home Assistant entities
        log.info(f"Updating sensor {settings.CLEANLINESS_SENSOR_ENTITY} with score: {score}")
        await ha_service.set_entity_state(
            settings.CLEANLINESS_SENSOR_ENTITY,
            str(score),
            {"last_analysis": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "recommended_tasks": tasks}
        )
        
        log.info(f"Updating todo list {settings.TODO_LIST_ENTITY_ID}")
        await ha_service.clear_todo_list(settings.TODO_LIST_ENTITY_ID)
        for task in tasks:
            await ha_service.create_todo_list_item(settings.TODO_LIST_ENTITY_ID, task)
        
        # 5. Record history
        await history_service.add_record({
            "timestamp": time.time(),
            "score": score,
            "tasks": tasks,
        })
        
        log.info("Analysis cycle completed successfully.")

    except (CameraError, AIProviderError, HomeAssistantAPIError, json.JSONDecodeError) as e:
        log.error(f"An error occurred during the analysis cycle: {e}")
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}", exc_info=True)


async def run_analysis_periodically():
    """
    Runs the analysis function at the interval specified in the configuration.
    """
    while True:
        await run_single_analysis()
        interval_seconds = settings.RECHECK_INTERVAL_MINUTES * 60
        log.info(f"Waiting for {interval_seconds} seconds before next run.")
        await asyncio.sleep(interval_seconds)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/history")
async def get_history():
    history_service: HistoryService = app.state.history_service
    try:
        return await history_service.get_history()
    except Exception as e:
        log.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve history.")

@app.post("/run-now", status_code=202)
async def trigger_run_now():
    """
    Manually triggers a single analysis run.
    """
    loop = asyncio.get_event_loop()
    loop.create_task(run_single_analysis())
    return {"message": "Analysis task triggered."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
