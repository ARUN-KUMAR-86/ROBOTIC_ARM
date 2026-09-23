"""
Computer Vision Object Detectors for Auron Robotics.
Provides modular detector pipeline:
- BaseDetector: Abstract interface
- ColorBlobDetector: Robust OpenCV HSV-based detector for simulation and real objects (Red, Blue, Green)
- AIDetector: Template architecture ready for YOLO / ONNX model integration
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple
import cv2
import numpy as np

@dataclass
class DetectionResult:
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int] # x, y, width, height
    center_pixel: Tuple[float, float] # cx, cy
    area: float

class BaseDetector(ABC):
    @abstractmethod
    def detect(self, img_bgr: np.ndarray) -> List[DetectionResult]:
        """Detect objects in a BGR image and return list of DetectionResult."""
        pass

class ColorBlobDetector(BaseDetector):
    """
    OpenCV HSV Color Segmentation Detector.
    Detects Red, Blue, and Green colored objects (matching Gazebo demo cubes and cylinders).
    """
    def __init__(self, min_area=300):
        self.min_area = min_area
        # HSV Color ranges
        self.color_ranges = {
            'red_cube': [
                # Red wraps around HSV 0/180
                (np.array([0, 100, 50]), np.array([10, 255, 255])),
                (np.array([170, 100, 50]), np.array([180, 255, 255])),
            ],
            'blue_cube': [
                (np.array([100, 120, 50]), np.array([135, 255, 255])),
            ],
            'green_cylinder': [
                (np.array([35, 80, 50]), np.array([85, 255, 255])),
            ],
        }

    def detect(self, img_bgr: np.ndarray) -> List[DetectionResult]:
        results = []
        if img_bgr is None or img_bgr.size == 0:
            return results

        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        # Apply slight blur to reduce sensor noise
        blurred = cv2.GaussianBlur(hsv, (5, 5), 0)

        for name, ranges in self.color_ranges.items():
            mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lower, upper in ranges:
                m = cv2.inRange(blurred, lower, upper)
                mask = cv2.bitwise_or(mask, m)

            # Morphological cleanup
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area >= self.min_area:
                    x, y, w, h = cv2.boundingRect(cnt)
                    M = cv2.moments(cnt)
                    if M["m00"] != 0:
                        cx = float(M["m10"] / M["m00"])
                        cy = float(M["m01"] / M["m00"])
                    else:
                        cx = float(x + w / 2.0)
                        cy = float(y + h / 2.0)

                    confidence = min(1.0, float(area / 5000.0) * 0.5 + 0.5)
                    results.append(DetectionResult(
                        class_name=name,
                        confidence=confidence,
                        bbox=(x, y, w, h),
                        center_pixel=(cx, cy),
                        area=area
                    ))
        return results

class AIDetector(BaseDetector):
    """
    Architecture placeholder for future Deep Learning / YOLO object detector.
    Allows easy drop-in of ultralytics YOLO or OpenCV DNN model without changing
    the rest of the ROS 2 vision pipeline.
    """
    def __init__(self, model_path=None, conf_threshold=0.5):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.model_loaded = False
        if model_path:
            self._load_model()

    def _load_model(self):
        # Implementation hook: e.g. self.net = cv2.dnn.readNetFromONNX(self.model_path)
        self.model_loaded = True

    def detect(self, img_bgr: np.ndarray) -> List[DetectionResult]:
        if not self.model_loaded:
            # Fallback to color segmentation if no neural network weights loaded
            return []
        # Inference pipeline here
        return []
