
from fastapi import APIRouter
from app.api.v1.endpoints import prediction
from app.api.v1.endpoints import trigger

router = APIRouter()

# Include prediction router (e.g. /api/v1/predict)
# Note: In original code, prefix was included in main.py: app.include_router(api_router, prefix=settings.API_V1_STR)
# And inside routers.py: @router.post("/predict")
# So effective URL was /api/v1/predict.
# Here we include prediction.router. 
# If prediction.router has @router.post("/predict"), we just include it directly.
router.include_router(prediction.router, tags=["prediction"])

# Include trigger router
# trigger router has @router.post("/simulate")
# We want /api/v1/trigger/simulate
router.include_router(trigger.router, prefix="/trigger", tags=["hardware-trigger"])
