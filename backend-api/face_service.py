"""
Diwaanka Ajaanibka - Face Recognition Service
"""
import os
import json
import numpy as np
from typing import List, Dict, Optional
import cv2

# DeepFace (ikhtiyaari)
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("⚠️  DeepFace lama rakibin - Haar Cascade ayaa la isticmaalayaa")


class FaceService:
    def __init__(self):
        self.tolerance = 0.6
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def detect_faces(self, image: np.ndarray) -> List[tuple]:
        """Soo saar wejiyada sawirka (Haar Cascade)"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]

    def get_encoding(self, image: np.ndarray) -> Optional[List[float]]:
        """Hel encoding-ka wejiga (DeepFace)"""
        if not DEEPFACE_AVAILABLE:
            return None
        try:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            embedding = DeepFace.represent(
                img_path=rgb,
                model_name="Facenet",
                enforce_detection=False
            )
            if embedding and len(embedding) > 0:
                return embedding[0]["embedding"]
            return None
        except Exception as e:
            print(f"Qalad encoding: {e}")
            return None

    def compare_faces(self, known_encoding: List[float], unknown_encoding: List[float]) -> Dict:
        """Barbardhig laba weji"""
        known = np.array(known_encoding)
        unknown = np.array(unknown_encoding)
        similarity = np.dot(known, unknown) / (np.linalg.norm(known) * np.linalg.norm(unknown))
        distance = 1 - similarity
        return {
            "match": bool(distance < 0.4),
            "confidence": round(float(similarity) * 100, 2),
            "distance": round(float(distance), 4)
        }

    def identify_face(self, unknown_encoding: List[float], known_encodings: List[Dict]) -> Optional[Dict]:
        """Aqoonso qofka"""
        if not known_encodings:
            return None
        unknown = np.array(unknown_encoding)
        best_match = None
        best_confidence = 0
        for k in known_encodings:
            if not k.get("encoding"):
                continue
            known = np.array(k["encoding"])
            similarity = np.dot(known, unknown) / (np.linalg.norm(known) * np.linalg.norm(unknown))
            if similarity > best_confidence:
                best_confidence = similarity
                best_match = k
        if best_match and best_confidence > 0.6:
            return {
                "match": True,
                "name": best_match["name"],
                "confidence": round(float(best_confidence) * 100, 2),
                "immigrant_id": best_match.get("id")
            }
        return {"match": False, "message": "Qofkan lama aqoonsan"}


face_service = FaceService()
