"""Minimal face service used by the API."""

from __future__ import annotations

from typing import Dict, List, Tuple

import cv2
import numpy as np


class FaceService:
    """Simple wrapper around OpenCV face detection for the app."""

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def detect_faces(self, image: np.ndarray) -> List[Dict[str, object]]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        results: List[Dict[str, object]] = []
        for index, (x, y, width, height) in enumerate(faces, start=1):
            results.append(
                {
                    "face_number": index,
                    "position": {
                        "x": int(x),
                        "y": int(y),
                        "width": int(width),
                        "height": int(height),
                    },
                }
            )
        return results


face_service = FaceService()
