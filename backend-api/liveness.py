"""
Diwaanka Ajaanibka - Liveness Detection
"""
import cv2
import numpy as np
from typing import Dict

class LivenessDetector:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
    
    def check_liveness(self, image: np.ndarray) -> Dict:
        """
        Hubi haddii sawirku yahay qof nool
        (Fudud - wuxuu baarayaa indhaha iyo wejiga)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return {"is_live": False, "message": "Wax weji ah lama helin"}
        
        total_eyes = 0
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            eyes = self.eye_cascade.detectMultiScale(roi_gray)
            total_eyes += len(eyes)
        
        if total_eyes >= 2:
            return {
                "is_live": True,
                "confidence": 95,
                "message": "Qof nool ayaa la helay"
            }
        else:
            return {
                "is_live": False,
                "confidence": 50,
                "message": "Waxaa laga yaabaa inaanu qof nool ahayn"
            }

liveness_detector = LivenessDetector()
