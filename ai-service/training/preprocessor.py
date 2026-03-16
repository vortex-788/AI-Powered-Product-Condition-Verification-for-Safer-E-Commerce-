import cv2
import numpy as np

def preprocess_image(image: np.ndarray, target_size=(224, 224)) -> np.ndarray:
    """
    Standardizes image size and applies CLAHE to normalize lighting 
    and enhance texture/edges before feeding into the neural network.
    
    Args:
        image: Raw BGR image array (uint8).
        target_size: Tuple indicating dimensions to resize to.
    
    Returns:
        Preprocessed BGR image array (uint8).
    """
    # Resize
    resized = cv2.resize(image, target_size)
    
    # Convert to LAB color space to apply equalization only to the Lightness channel
    lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    
    # Apply CLAHE to L-channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l_channel)
    
    # Merge back and convert to BGR
    merged = cv2.merge((cl, a_channel, b_channel))
    balanced_bgr = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    
    return balanced_bgr

if __name__ == '__main__':
    # Simple test to confirm imports and syntax
    dummy_img = np.zeros((500, 500, 3), dtype=np.uint8)
    processed = preprocess_image(dummy_img)
    print(f"Processed image shape: {processed.shape}")
