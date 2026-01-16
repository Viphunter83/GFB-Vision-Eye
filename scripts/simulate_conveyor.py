
import asyncio
import random
import time
import uuid
import sys
from pathlib import Path
from typing import List, Optional

try:
    import httpx
    import cv2
    import numpy as np
    from rich.console import Console
    from rich.table import Table
    from rich import print as rprint
except ImportError:
    print("Please install required packages: pip install rich httpx opencv-python-headless")
    sys.exit(1)

# Configuration
import os
API_URL = os.getenv("API_URL", "http://localhost:8080/api/v1/predict")
SEARCH_DIRS = [
    "dataset_raw",
    "Плохая этикетка",
    "Предмет внутри",
    "Рваная упаковка",
    "Целая упаковка"
]
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

console = Console()

def find_images(base_path: Path) -> List[Path]:
    """Find all images in specific directories."""
    images = []
    
    # Check explicitly defined search directories
    for dir_name in SEARCH_DIRS:
        target_dir = base_path / dir_name
        if target_dir.exists() and target_dir.is_dir():
            for ext in EXTENSIONS:
                images.extend(list(target_dir.glob(f"*{ext}")))
                # Also check uppercase extensions
                images.extend(list(target_dir.glob(f"*{ext.upper()}")))

    return list(set(images)) # Remove duplicates if any

async def simulate_conveyor(num_items: int = 10):
    """Simulate conveyor belt processing."""
    
    base_path = Path.cwd()
    images = find_images(base_path)
    
    if not images:
        rprint("[bold red]ERROR:[/bold red] No images found in search directories!")
        rprint(f"Searched in: {', '.join(SEARCH_DIRS)}")
        return

    # Select random images
    selected_images = random.sample(images, min(num_items, len(images)))
    
    rprint(f"[bold blue]Starting simulation with {len(selected_images)} items...[/bold blue]")
    rprint("-" * 50)

    # Setup Results Directory
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_dir = Path(f"simulation_results/{timestamp}")
    results_dir.mkdir(parents=True, exist_ok=True)
    rprint(f"Saving evidence to: [blue]{results_dir}[/blue]")

    stats = {
        "total": 0,
        "pass": 0,
        "reject": 0,
        "total_latency": 0
    }

    async with httpx.AsyncClient() as client:
        for img_path in selected_images:
            batch_id = str(uuid.uuid4())
            stats["total"] += 1
            
            # Prepare request
            start_time = time.time()
            try:
                with open(img_path, "rb") as f:
                    files = {"file": (img_path.name, f, "image/png")}
                    response = await client.post(API_URL, files=files)
                    response.raise_for_status()
                    result = response.json()
            except Exception as e:
                rprint(f"[bold red]REQ ERROR[/bold red]: {e}")
                continue
            
            latency = (time.time() - start_time) * 1000
            stats["total_latency"] += latency

            # Verdict logic (assuming response structure from previous context or standard)
            # Adjusting based on potential response format. 
            # Usually: {"verdict": "PASS" | "FAIL", "confidence": float, "class": str}
            
            # Verdict logic with local override
            server_verdict = result.get("verdict", "UNKNOWN")
            confidence = result.get("confidence", 0.0) or 0.0
            defect_class = result.get("predicted_class", "N/A")
            
            # Local override logic (User requirement: PASS if conf > 0.5 for 'ok')
            final_verdict = server_verdict
            color = (0, 0, 255) # Red for FAIL
            status_text = f"FAIL | {defect_class} | {confidence:.2f}"
            
            if defect_class == "ok":
                if confidence > 0.8:
                    final_verdict = "PASS"
                    color = (0, 255, 0) # Green
                    status_text = f"PASS | {defect_class} | {confidence:.2f}"
                elif confidence > 0.5:
                    final_verdict = "WARNING" # Treated as PASS locally but visual warning or just lower threshold PASS
                    # User asked to lower threshold to 0.5 for PASS OR use yellow.
                    # Let's treat it as PASS with Yellow indication if between 0.5 and 0.8
                    color = (0, 255, 255) # Yellow (BGR: 0, 255, 255) -> actually Yellow is (0, 255, 255) in BGR? No, Yellow is R+G = (0, 255, 255) is Cyan. Yellow is (0, 255, 255)? 
                    # RGB Yellow is (255, 255, 0). OpenCV uses BGR. So Yellow is (0, 255, 255). Wait.
                    # Blue=0, Green=255, Red=255.
                    color = (0, 255, 255) 
                    status_text = f"PASS (LOW CONF) | {defect_class} | {confidence:.2f}"
                    # Count as PASS for stats
                    final_verdict = "PASS" 
                else:
                    final_verdict = "FAIL"
                    status_text = f"FAIL (LOW CONF) | {defect_class} | {confidence:.2f}"

            # Update stats based on local final_verdict
            if final_verdict == "PASS":
                stats["pass"] += 1
                rprint(f"✅ Batch {batch_id[:8]}...: [green]{status_text}[/green] | Time: {latency:.0f}ms")
            else:
                stats["reject"] += 1
                rprint(f"⛔ Batch {batch_id[:8]}...: [red]{status_text}[/red] | Time: {latency:.0f}ms")

            # Visual Evidence Generation
            try:
                img = cv2.imread(str(img_path))
                if img is not None:
                    # Draw top banner
                    h, w, _ = img.shape
                    banner_height = int(h * 0.1) # 10% of height
                    cv2.rectangle(img, (0, 0), (w, banner_height), color, -1)
                    
                    # Add text
                    font_scale = min(w, h) / 1000 * 2.5
                    thickness = max(1, int(font_scale * 2))
                    text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
                    text_x = (w - text_size[0]) // 2
                    text_y = (banner_height + text_size[1]) // 2
                    
                    # Text color: Black if Yellow/Green, White if Red? 
                    # Yellow (0,255,255) is bright. Green (0,255,0) is bright. Red (0,0,255) is dark.
                    # Let's use Black text for Yellow/Green and White for Red.
                    text_color = (0, 0, 0) if color != (0, 0, 255) else (255, 255, 255)
                    
                    cv2.putText(img, status_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, thickness)
                    
                    # Save
                    if results_dir:
                        save_path = results_dir / f"{batch_id}_{final_verdict}.jpg"
                        cv2.imwrite(str(save_path), img)
            except Exception as e:
                rprint(f"[bold red]VISUALIZATION ERROR[/bold red]: {e}")

            # Simulate conveyor interval
            await asyncio.sleep(0.5)

    # Summary
    avg_time = stats["total_latency"] / stats["total"] if stats["total"] > 0 else 0
    
    rprint("\n[bold]Simulation Summary[/bold]")
    rprint("=" * 30)
    rprint(f"Total Processed : {stats['total']}")
    rprint(f"Accepted        : [green]{stats['pass']}[/green]")
    rprint(f"Rejected        : [red]{stats['reject']}[/red]")
    rprint(f"Avg Latency     : {avg_time:.0f} ms")
    if results_dir:
        rprint(f"Visual Evidence : [blue]{results_dir}[/blue]")
    rprint("=" * 30)

if __name__ == "__main__":
    asyncio.run(simulate_conveyor())
