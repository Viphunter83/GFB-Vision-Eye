import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.schemas.prediction import PredictionResult

logger = logging.getLogger(__name__)

class NotifierService:
    def __init__(self):
        self.webhook_url = settings.MAIN_SYSTEM_WEBHOOK_URL
        self.headers = {"Content-Type": "application/json"}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.RequestError),
    )
    async def _send_payload(self, payload: Dict[str, Any]):
        if not self.webhook_url:
            logger.warning("Webhook URL not set. Skipping notification.")
            return

        async with httpx.AsyncClient() as client:
            response = await client.post(self.webhook_url, json=payload, headers=self.headers, timeout=5.0)
            response.raise_for_status()
            logger.info(f"Notification sent successfully: {response.status_code}")

    async def send_inspection_result(self, result: PredictionResult, image_url: str):
        """
        Sends inspection result to the main system via webhook.
        Fire-and-forget style (handled by BackgroundTasks in caller, but logic here is async).
        """
        if not self.webhook_url:
             # Even if checked in _send_payload, check here to avoid overhead
            return

        payload = {
            "batch_id": str(uuid.uuid4()), # Generate a batch ID if not available? Or should be passed? check usage
            "timestamp": datetime.now().isoformat(),
            "verdict": result.verdict,
            "confidence": result.confidence if result.confidence else (
                 # Derived confidence from boxes if purely detection mode?
                 # Assuming average or max confidence of detections? 
                 # Or 1.0 if PASS?
                 # The prompt example says "0.95". 
                 # I'll use max confidence from detections if available.
                 max([d.confidence for d in result.defects], default=0.0) if result.defects else 1.0 
                 if result.verdict == "PASS" else 0.0
            ),
            "evidence_url": image_url,
            "device_id": "JETSON_01" # Hardcoded or from config? Prompt example says JETSON_01
        }
        
        try:
            await self._send_payload(payload)
        except Exception as e:
            logger.error(f"Failed to send webhook notification after retries: {e}")

notifier_service = NotifierService()
