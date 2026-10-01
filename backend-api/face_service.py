"""
Diwaanka Ajaanibka - Face Recognition Service
"""
import face_recognition
import numpy as np
import cv2
import json
import base64
from typing import List, Dict, Optional

class FaceService:
    def __init__(self):
        self.tolerance = 0.6
    
    def detect_faces(self, image: np.ndarray) -> List[tuple]:
        """Soo saar wejiyada sawirka"""
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return face_recognition.face_locations(rgb)
    
    def get_encoding(self, image: np.ndarray) -> Optional[List[float]]:
        """Hel encoding-ka wejiga (128-d vector)"""
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
        if len(encodings) == 0:
            return None
        return encodings[0].tolist()
    
    def compare_faces(self, known_encoding: List[float], unknown_encoding: List[float]) -> Dict:
        """Barbardhig laba weji"""
        known = np.array(known_encoding)
        unknown = np.array(unknown_encoding)
        
        matches = face_recognition.compare_faces([known], unknown, tolerance=self.tolerance)
        distance = face_recognition.face_distance([known], unknown)[0]
        
        return {
            "match": bool(matches[0]),
            "confidence": round((1 - distance) * 100, 2),
            "distance": round(float(distance), 4)
        }
    
    def identify_face(self, unknown_encoding: List[float], known_encodings: List[Dict]) -> Optional[Dict]:
        """Aqoonso qofka"""
        if not known_encodings:
            return None
        
        unknown = np.array(unknown_encoding)
        encodings = [np.array(k["encoding"]) for k in known_encodings]
        
        matches = face_recognition.compare_faces(encodings, unknown, tolerance=self.tolerance)
        distances = face_recognition.face_distance(encodings, unknown)
        
        best_idx = np.argmin(distances)
        
        if matches[best_idx]:
            return {
                "match": True,
                "name": known_encodings[best_idx]["name"],
                "confidence": round((1 - distances[best_idx]) * 100, 2),
                "index": int(best_idx)
            }
        return {"match": False, "message": "Qofkan lama aqoonsan"}

face_service = FaceService()
