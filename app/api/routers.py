from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.schemas.prediction import PredictionResult, ErrorResponse
from app.services.inference_service import get_inference_service, ModelInference
from app.utils.image_processing import preprocess_image
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/predict", response_model=PredictionResult, responses={500: {"model": ErrorResponse}})
async def predict_image(
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

        result = service.predict(image)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
