from ultralytics import YOLO
import argparse
import os

def train_model(dataset_path: str, epochs: int = 10, imgsz: int = 224, model_name: str = "yolo11n-cls.pt"):
    print(f"Starting training with model {model_name} on {dataset_path}...")
    
    # Load model
    model = YOLO(model_name)
    
    # Train
    results = model.train(
        data=dataset_path, 
        epochs=epochs, 
        imgsz=imgsz,
        project="models/train_runs",
        name="gfb_cls_run"
    )
    
    # Save best model
    # Ultralytics saves best.pt in runs/.../weights/best.pt
    # We will copy it to the requested location
    best_model_path = os.path.join(results.save_dir, "weights", "best.pt")
    target_path = "models/gfb_classifier_v1.pt"
    
    if os.path.exists(best_model_path):
        import shutil
        shutil.copy(best_model_path, target_path)
        print(f"Training complete. Best model saved to {target_path}")
    else:
        print("Training complete, but could not find best.pt to copy.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="datasets/gfb-food-cls", help="Path to dataset root")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--imgsz", type=int, default=224, help="Image size")
    
    args = parser.parse_args()
    train_model(args.data, args.epochs, args.imgsz)
