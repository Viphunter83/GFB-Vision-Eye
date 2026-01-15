from ultralytics import YOLO
import numpy as np
import time
from app.core.config import settings
from app.schemas.prediction import BoundingBox, PredictionResult

class ModelInference:
    def __init__(self):
        self.model = YOLO(settings.MODEL_PATH)
        # Warmup or check if loaded? Ultralytics usually loads on init.

    def predict(self, image: np.ndarray) -> PredictionResult:
        start_time = time.time()
        
        # Run inference
        results = self.model.predict(
            source=image, 
            conf=settings.CONFIDENCE_THRESHOLD,
            iou=settings.IOU_THRESHOLD,
            verbose=False
        )
        
        defects = []
        result = results[0]  # We process one image at a time
        
        # Process detections
        if result.boxes:
            for box in result.boxes:
                # box.xyxy is a tensor, need to convert to list
                coords = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = result.names[cls_id]
                
                defects.append(BoundingBox(
                    x1=coords[0],
                    y1=coords[1],
                    x2=coords[2],
                    y2=coords[3],
                    confidence=conf,
                    class_id=cls_id,
                    class_name=cls_name
                ))

        inference_time = time.time() - start_time
        
        # Determine verdict
        # If any defects are found, verdict is FAIL. Or specific logic?
        # Requirement: "defects include 'tear', 'label_error', 'foreign_object'"
        # Assuming finding any of these is a FAIL.
        verdict = "FAIL" if len(defects) > 0 else "PASS"

        return PredictionResult(
            verdict=verdict,
            defects=defects,
            inference_time=inference_time,
            model_name=str(self.model.model.names) if self.model.model else "unknown"  # simplified name retrieval
        )

# Global instance
inference_service = None

def get_inference_service():
    global inference_service
    if inference_service is None:
        inference_service = ModelInference()
    return inference_service
