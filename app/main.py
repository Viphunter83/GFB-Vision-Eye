from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.routers import router as api_router
from app.services.inference_service import get_inference_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model on startup
    logger.info("Loading YOLO model...")
    try:
        get_inference_service()
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")

    # Start Hardware Trigger Listener
    from app.services.hardware_trigger import get_trigger_listener
    trigger_service = get_trigger_listener()
    await trigger_service.start()
    
    yield
    
    # Clean up resources
    await trigger_service.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok", "service": settings.PROJECT_NAME}

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
