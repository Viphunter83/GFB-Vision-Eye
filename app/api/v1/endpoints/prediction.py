
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from app.schemas.prediction import PredictionResult, ErrorResponse
from app.services.inference_service import get_inference_service, ModelInference
from app.utils.image_processing import preprocess_image
from app.services.notifier import notifier_service
from app.utils.s3_client import s3_client
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

async def handle_notification(result: PredictionResult, image_bytes: bytes):
    """
    Background task to upload evidence and send notification.
    """
    try:
        # Upload evidence to S3
        # Ensure we are passing bytes. 
        # Note: image_processing.preprocess_image returns numpy array, 
        # but we should upload the ORIGINAL bytes for evidence, or encoded JPEG.
        # Here we pass the original file contents.
        image_url = await s3_client.upload(image_bytes)
        
        # Send webhook
        await notifier_service.send_inspection_result(result, image_url)
    except Exception as e:
        logger.error(f"Background notification failed: {e}")

@router.post("/predict", response_model=PredictionResult, responses={500: {"model": ErrorResponse}})
async def predict_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    service: ModelInference = Depends(get_inference_service)
):
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
            
        contents = await file.read()
        image = preprocess_image(contents)
        
        if image is None or image.size == 0:
             raise HTTPException(status_code=400, detail="Invalid image file")

        # Run inference
        result = service.predict(image)
        
        # Schedule notification task (Fire-and-Forget)
        # We pass 'contents' (original bytes) to avoid re-encoding numpy array
        background_tasks.add_task(handle_notification, result, contents)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
