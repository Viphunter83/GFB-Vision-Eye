import numpy as np
import cv2

def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Convert raw bytes to an OpenCV image (numpy array).
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img
