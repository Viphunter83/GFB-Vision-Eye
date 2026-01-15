import os
import shutil
import random
import argparse
from pathlib import Path

# Mapping from source names (Russian) to target YOLO classes (English)
CLASS_MAPPING = {
    "Целая упаковка": "ok",
    "Рваная упаковка": "tear",
    "Плохая этикетка": "label_error",
    "Предмет внутри": "foreign_object",
    # English aliases just in case
    "ok": "ok",
    "tear": "tear",
    "label_error": "label_error",
    "foreign_object": "foreign_object"
}

def prepare_data(source_dir: str, output_dir: str, split_ratio: float = 0.8):
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    
    if not source_path.exists():
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return

    # Create output structure
    train_dir = output_path / "train"
    val_dir = output_path / "val"
    
    # Clean output if exists? Better to be safe and just warn or overwrite
    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(val_dir, exist_ok=True)

    print(f"Processing data from {source_path} to {output_path}...")

    # Iterate over folders in source
    for class_folder in source_path.iterdir():
        if not class_folder.is_dir():
            continue
            
        class_name = class_folder.name
        
        # Check mapping
        target_class = CLASS_MAPPING.get(class_name)
        
        if not target_class:
            print(f"Skipping unknown class folder: {class_name}")
            continue
            
        print(f"Processing class: {class_name} -> {target_class}")
        
        # Create target class folders
        (train_dir / target_class).mkdir(exist_ok=True)
        (val_dir / target_class).mkdir(exist_ok=True)
        
        # Get all images
        images = [f for f in class_folder.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']]
        random.shuffle(images)
        
        split_idx = int(len(images) * split_ratio)
        train_images = images[:split_idx]
        val_images = images[split_idx:]
        
        # Copy files
        for img in train_images:
            shutil.copy2(img, train_dir / target_class / img.name)
            
        for img in val_images:
            shutil.copy2(img, val_dir / target_class / img.name)
            
        print(f"  - Copied {len(train_images)} to train, {len(val_images)} to val")

    print("Data preparation complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare dataset for YOLO classification")
    parser.add_argument("--source", type=str, required=True, help="Path to raw dataset with class folders")
    parser.add_argument("--output", type=str, default="datasets/gfb-food-cls", help="Output path for YOLO dataset")
    parser.add_argument("--split", type=float, default=0.8, help="Train split ratio (default: 0.8)")
    
    args = parser.parse_args()
    prepare_data(args.source, args.output, args.split)
