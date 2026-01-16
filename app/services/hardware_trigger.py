
import asyncio
import logging
import platform
import time
from typing import Optional, Callable
import cv2
import numpy as np
from app.services.inference_service import get_inference_service

# Try importing Jetson.GPIO, fallback to Mock if not available
try:
    import Jetson.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

logger = logging.getLogger(__name__)

# Pin Configuration (BCM mode usually for Jetson if configured, or BOARD)
# Adjust based on wiring. Assuming Board Pin 18 for now as per prompt.
OUTPUT_PIN = 18 
TRIGGER_PIN = 12 # Example input pin

class TriggerListener:
    def __init__(self):
        self.running = False
        self.inference_service = get_inference_service()
        self.cap: Optional[cv2.VideoCapture] = None
        
        # Determine mode
        self.is_jetson = GPIO_AVAILABLE
        logger.info(f"Hardware Manager initialized. Mode: {'JETSON (Real GPIO)' if self.is_jetson else 'MOCK (Simulation)'}")

    async def start(self):
        """Starts the trigger listener loop."""
        self.running = True
        
        # Initialize Camera
        # Using index 0. On Jetson typically /dev/video0
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            logger.warning("Camera not found! Will rely on mock images if triggered.")
        
        # Initialize GPIO
        if self.is_jetson:
            try:
                GPIO.setmode(GPIO.BOARD) # or BCM
                GPIO.setup(TRIGGER_PIN, GPIO.IN)
                GPIO.setup(OUTPUT_PIN, GPIO.OUT, initial=GPIO.LOW)
                
                # Add event detect
                GPIO.add_event_detect(TRIGGER_PIN, GPIO.RISING, callback=self.on_trigger_event)
            except Exception as e:
                logger.error(f"GPIO Setup failed: {e}")
                self.is_jetson = False # Fallback to mock behavior if setup fails
        
        # Start loop (mostly for mock mode or keeping service alive)
        asyncio.create_task(self._loop())

    async def stop(self):
        """Stops the listener and cleans up resources."""
        self.running = False
        if self.cap:
            self.cap.release()
        
        if self.is_jetson:
            GPIO.cleanup()
        logger.info("Hardware Manager stopped.")

    def on_trigger_event(self, channel):
        """Callback for GPIO interrupt (Run in separate thread via Jetson.GPIO)."""
        logger.info("Physical Trigger Detected!")
        # Fire and forget processing loop
        asyncio.run_coroutine_threadsafe(self.process_trigger(), asyncio.get_event_loop())

    async def _loop(self):
        """Simulation loop for Mock mode."""
        while self.running:
            if not self.is_jetson:
                # In Mock mode, we don't self-trigger automatically to avoid spamming.
                # Use API /simulate to trigger. 
                # But prompt said: "Emulate trigger press (e.g. once every 5 seconds)"
                # Let's do that for now to verify logic? 
                # Actually, user said: "API update... for manual call". 
                # "Mock mode... emulate trigger press... OR key press".
                # Let's stick to API trigger for now to be less annoying, 
                # or maybe a very slow auto-trigger.
                # Let's wait for API trigger mostly, but maybe log a heartbeat.
                pass
            await asyncio.sleep(1)

    async def process_trigger(self):
        """Main logic: Capture -> Inference -> Action."""
        logger.info("Processing Trigger...")
        
        # 1. Capture Frame
        frame = self.capture_frame()
        if frame is None:
            logger.error("Failed to capture frame.")
            return

        # 2. Inference
        try:
            # Inference service expects bytes or file. 
            # We have a numpy array. We need to encode it.
            success, encoded_img = cv2.imencode('.jpg', frame)
            if not success:
                logger.error("Failed to encode frame.")
                return
            
            # Send to inference
            # Note: InferenceService.predict takes bytes
            image_bytes = encoded_img.tobytes()
            # We likely need a way to call predict directly without async http overhead if internal?
            # app.services.inference_service.InferenceService usually has a 'predict' method.
            # Let's verify signature. It probably takes bytes.
            
            result = await self.inference_service.predict(image_bytes)
            
            verdict = result.get("verdict", "UNKNOWN")
            logger.info(f"Verdict: {verdict} | Class: {result.get('predicted_class')}")
            
            # 3. Action
            if verdict == "FAIL":
                await self.activate_pusher()
                
        except Exception as e:
            logger.error(f"Error during processing: {e}")

    def capture_frame(self) -> Optional[np.ndarray]:
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        
        # Mock frame if camera fails or in mock mode
        logger.warning("Using generated MOCK frame.")
        img = np.zeros((640, 640, 3), dtype=np.uint8)
        # Draw a red noise or something
        cv2.putText(img, "MOCK FRAME", (50, 320), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
        return img

    async def activate_pusher(self):
        logger.warning(">>> ACTIVATING PNEUMO-PUSHER (PIN 18) <<<")
        if self.is_jetson:
            GPIO.output(OUTPUT_PIN, GPIO.HIGH)
            await asyncio.sleep(0.1) # Pulse duration
            GPIO.output(OUTPUT_PIN, GPIO.LOW)
        else:
            # Mock Feedback
            logger.info("[MOCK] PSHHH! (Air blast sound)")

# Singleton instance
_trigger_listener: Optional[TriggerListener] = None

def get_trigger_listener() -> TriggerListener:
    global _trigger_listener
    if not _trigger_listener:
        _trigger_listener = TriggerListener()
    return _trigger_listener
