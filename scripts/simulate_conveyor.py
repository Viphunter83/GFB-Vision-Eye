
import asyncio
import random
import time
import uuid
import sys
from pathlib import Path
from typing import List, Optional

try:
    import httpx
    from rich.console import Console
    from rich.table import Table
    from rich import print as rprint
except ImportError:
    print("Please install required packages: pip install rich httpx")
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
            
            verdict = result.get("verdict", "UNKNOWN")
            confidence = result.get("confidence", 0.0)
            defect_class = result.get("predicted_class", "N/A")
            
            if verdict == "PASS":
                stats["pass"] += 1
                rprint(f"✅ Batch {batch_id[:8]}...: [green]OK[/green] | Time: {latency:.0f}ms | Conf: {confidence:.2f}")
            else:
                stats["reject"] += 1
                rprint(f"⛔ Batch {batch_id[:8]}...: [red]REJECTED[/red] | Defect: {defect_class} | Time: {latency:.0f}ms")
            
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
    rprint("=" * 30)

if __name__ == "__main__":
    asyncio.run(simulate_conveyor())
