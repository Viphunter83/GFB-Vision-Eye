from pydantic import BaseModel, Field
from typing import List, Optional

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str

class PredictionResult(BaseModel):
    verdict: str = Field(..., description="PASS or FAIL")
    defects: List[BoundingBox] = []
    inference_time: float = Field(..., description="Inference time in seconds")
    model_name: str
    
class ErrorResponse(BaseModel):
    detail: str
