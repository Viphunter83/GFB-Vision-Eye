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
        # We might want to exit here if model is critical, or just log
    yield
    # Clean up resources if needed

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok", "service": settings.PROJECT_NAME}

app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
