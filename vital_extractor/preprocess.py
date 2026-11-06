import cv2
import numpy as np
from typing import Tuple


def load_image(image_path: str, max_dim: int = 800) -> np.ndarray:
    """
    Load an image from disk using OpenCV and downscale if too large.

    Parameters
    ----------
    image_path : str
        Path to the input image file.
    max_dim : int
        Maximum dimension (width or height) to prevent high memory usage.

    Returns
    -------
    np.ndarray
        Loaded image in BGR color format.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not read image at path: {image_path}")
    h, w = image.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        image = cv2.resize(image, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    return image


def load_image_from_bytes(image_bytes: bytes, max_dim: int = 800) -> np.ndarray:
    """
    Decode an image directly from in-memory bytes (Zero-disk consumption)
    and downscale to max_dim immediately to prevent container Out-Of-Memory (OOM).

    Parameters
    ----------
    image_bytes : bytes
        Raw image file bytes.
    max_dim : int
        Maximum width or height in pixels (defaults to 800px).

    Returns
    -------
    np.ndarray
        Decoded image in BGR format.
    """
    if not image_bytes:
        raise ValueError("Empty image bytes received.")
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image from memory bytes.")
    
    h, w = image.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return image


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Apply a set of preprocessing operations to improve OCR accuracy.

    Steps:
    - Convert to grayscale
    - Improve local contrast using CLAHE
    - Optionally invert if the background is very dark
    - Apply mild blurring to reduce noise
    - Apply adaptive thresholding to emphasize text, but keep shapes readable

    Parameters
    ----------
    image : np.ndarray
        Original BGR image in uint8 format.

    Returns
    -------
    np.ndarray
        Preprocessed image in 3-channel BGR format suitable for OCR.
    """
    # Ensure we have a proper uint8 BGR image.
    if image is None or image.size == 0:
        raise ValueError("preprocess_image received an empty image.")
    if image.dtype != np.uint8:
        image = image.astype(np.uint8)

    # Convert to grayscale to simplify the data for OCR
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # If the background is very dark (monitor screen), inverting can
    # make bright text stand out more clearly for OCR.
    mean_intensity = float(gray.mean())
    if mean_intensity < 80:
        gray = cv2.bitwise_not(gray)

    # Improve contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Light Gaussian blur helps to remove small noise while keeping edges
    blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)

    # Adaptive thresholding makes text regions stand out under varying lighting.
    # Using a slightly larger blockSize avoids over-fragmenting digits.
    thresh = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        31,
        5,
    )

    # Many OCR models expect 3-channel images.
    # Convert the binary image back to BGR so PaddleOCR receives (H, W, 3).
    thresh_bgr = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    return thresh_bgr


def load_and_preprocess(image_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convenience helper that loads and preprocesses an image in one call.

    Parameters
    ----------
    image_path : str
        Path to the input image file.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        Tuple of (original_image_bgr, preprocessed_image).
    """
    original = load_image(image_path)
    processed = preprocess_image(original)

    # Save a debug copy of the preprocessed image so you can visually
    # inspect what is being sent to OCR.
    try:
        cv2.imwrite("debug_preprocessed.png", processed)
    except Exception:
        # Failing to write the debug image should not break the pipeline.
        pass

    return original, processed

