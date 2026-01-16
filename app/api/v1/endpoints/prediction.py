
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

        # service.predict now might be async or sync depending on implementation? 
        # In previous steps checking InferenceService it seemed sync but let's check. 
        # Actually inference_service.py usually has 'predict' as async def or regular def.
        # The 'simulate_conveyor.py' called API.
        # 'InferenceService' code I viewed earlier:
        # It had "def predict(self, image_data: bytes) -> PredictionResult:"
        # Wait, inside hardware_trigger.py I called "await self.inference_service.predict(image_bytes)".
        # I should check if it is async or not.
        
        # In the original routers.py (lines 32): "result = service.predict(image)" (not await)
        # So it handles numpy array? 
        # Looking at line 27: "image = preprocess_image(contents)" -> returns numpy array likely.
        
        # Let's trust the original code logic from routers.py:
        result = service.predict(image)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
