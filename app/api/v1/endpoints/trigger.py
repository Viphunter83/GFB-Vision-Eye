
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.services.hardware_trigger import get_trigger_listener

router = APIRouter()

@router.post("/simulate")
async def simulate_trigger(background_tasks: BackgroundTasks):
    """
    Simulates a hardware trigger event.
    Useful for testing logic without physical sensors.
    """
    listener = get_trigger_listener()
    
    # We run this in background or directly invoke? 
    # invoke directly is fine as it's async and returns void usually
    # But process_trigger is async.
    
    # Let's run it in background to not block response
    background_tasks.add_task(listener.process_trigger)
    
    return {"status": "Trigger signal received", "mode": "MOCK" if not listener.is_jetson else "JETSON"}
