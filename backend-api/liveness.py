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
        self.smile_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_smile.xml'
        )

    def check_liveness(self, image: np.ndarray) -> Dict:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) == 0:
            return {
                "is_live": False,
                "confidence": 0,
                "message": "Wax weji ah lama helin"
            }

        total_eyes = 0
        total_smiles = 0

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 10)
            total_eyes += len(eyes)
            smiles = self.smile_cascade.detectMultiScale(roi_gray, 1.7, 20)
            total_smiles += len(smiles)

        score = 0
        if total_eyes >= 2:
            score += 50
        if total_smiles >= 1:
            score += 30
        if len(faces) == 1:
            score += 20

        is_live = score >= 50

        return {
            "is_live": bool(is_live),
            "confidence": int(score),
            "faces_detected": len(faces),
            "eyes_detected": int(total_eyes),
            "smiles_detected": int(total_smiles),
            "message": "Qof nool ahaa la helay" if is_live else "Waxaa laga yaabaa inaanu qof nool ahayn"
        }


liveness_detector = LivenessDetector()
