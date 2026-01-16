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
        # YOLO26/v10+ are End-to-End (NMS-free), so we rely on model output directly.
        # No additional NMS post-processing needed here beyond what Ultralytics handles.
        results = self.model.predict(
            source=image, 
            conf=settings.CONFIDENCE_THRESHOLD,
            iou=settings.IOU_THRESHOLD,
            verbose=False
        )
        
        result = results[0]
        inference_time = time.time() - start_time
        
        defects = []
        verdict = "FAIL" # Default fallback
        model_name = str(self.model.model.names) if self.model.model else "unknown"
        
        predicted_class = None
        confidence = None

        # Check task type
        task = result.orig_shape # simplistic check, or check model.task
        # Ultralytics result object has .probs for classification and .boxes for detection
        
        if result.probs is not None:
            # CLASSIFICATION MODE
            top1_index = result.probs.top1
            top1_conf = result.probs.top1conf.item()
            class_name = result.names[top1_index]
            
            predicted_class = class_name
            confidence = top1_conf
            
            # Logic: If class == 'ok' and confidence > 0.8 -> PASS
            # Note: User request says "class == 'ok' and confidence > 0.8". 
            # We assume threshold 0.8 is hardcoded or should be settings.CONFIDENCE_THRESHOLD? 
            # User said "confidence > 0.8", I will use 0.8 explicitly or settings if specifically configured for cls.
            # Using 0.8 as requested.
            
            if class_name == 'ok' and top1_conf > 0.8:
                verdict = "PASS"
            else:
                verdict = "FAIL"
                
            # For classification, we don't have bounding boxes, but we can return the top result in defects for info?
            # Or just leave defects empty. Creating a dummy box might be confusing.
            # We will leave defects empty for now as per schema.
            
        else:
            # DETECTION MODE (original logic)
            if result.boxes:
                for box in result.boxes:
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

            # Verdict logic for detection
            verdict = "FAIL" if len(defects) > 0 else "PASS"

        return PredictionResult(
            verdict=verdict,
            defects=defects,
            inference_time=inference_time,
            model_name=model_name,
            predicted_class=predicted_class,
            confidence=confidence
        )

# Global instance
inference_service = None

def get_inference_service():
    global inference_service
    if inference_service is None:
        inference_service = ModelInference()
    return inference_service
