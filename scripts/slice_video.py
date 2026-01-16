
import cv2
import sys
from pathlib import Path
from rich.console import Console

console = Console()

def slice_video(video_path: str, output_dir: str, interval: int = 1):
    """
    Slices a video into frames at a specified interval.

    Args:
        video_path (str): Path to the source video file.
        output_dir (str): Directory where frames will be saved.
        interval (int): Capture every Nth frame.
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    
    if not video_path.exists():
        console.print(f"[bold red]Error: Video file {video_path} not found![/bold red]")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        console.print("[bold red]Error: Could not open video.[/bold red]")
        return
    
    count = 0
    saved_count = 0
    
    console.print(f"[green]Starting processing {video_path.name}...[/green]")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if count % interval == 0:
            frame_name = f"{video_path.stem}_frame_{count}.jpg"
            save_path = output_dir / frame_name
            cv2.imwrite(str(save_path), frame)
            saved_count += 1
            if saved_count % 50 == 0:
                 console.print(f"Saved {saved_count} frames...", end="\r")
        
        count += 1
        
    cap.release()
    console.print(f"\n[bold green]Done! Saved {saved_count} frames to {output_dir}[/bold green]")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Slice video into frames")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--output", "-o", default="dataset_raw/new_batch", help="Output directory")
    parser.add_argument("--interval", "-i", type=int, default=10, help="Save every Nth frame")
    
    args = parser.parse_args()
    slice_video(args.video, args.output, args.interval)
