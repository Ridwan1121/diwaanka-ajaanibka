"""
Diwaanka Ajaanibka - Backend API
Face Recognition System for Immigration
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import cv2
import numpy as np
import base64
import json
import os

app = FastAPI(
    title="Diwaanka Ajaanibka - Face Recognition API",
    description="API-ga weji-aqoonsiga ee hay'adda socdaalka",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

DB_FILE = "database.json"

def load_database():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "immigrants": [],
        "officers": [],
        "admins": [],
        "scan_history": []
    }

def save_database(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

class Immigrant(BaseModel):
    name: str
    country: str
    region: str
    entry_point: str
    district: str
    passport: Optional[str] = None
    status: str = "registered"

class Officer(BaseModel):
    name: str
    office: str
    border: str
    country: str
    status: str = "active"

class Admin(BaseModel):
    name: str
    role: str
    office: str
    status: str = "active"

@app.get("/")
def home():
    return {
        "status": "success",
        "message": "Ku soo dhawaada API-ga Diwaanka Ajaanibka!",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Hubi haddii API-gu shaqeynayo",
            "/scan-face/": "Aqoonso wejiyada sawirka",
            "/detect-faces/": "Soo bandhig wejiyada sawirka",
            "/immigrants/": "Liiska ajaanibta",
            "/officers/": "Liiska askarta",
            "/admins/": "Liiska maamulayaasha",
            "/stats/": "Tirakoobka nidaamka"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "API-ga waa shaqeynayaa si fiican",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/scan-face/")
async def scan_face(file: UploadFile = File(...)):
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Fadlan soo gudbi sawir sax ah")
        
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Sawirka lama akhrin karo")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "warning",
                    "detected_faces": 0,
                    "faces": [],
                    "message": "Wax weji ah lagama helin sawirkan"
                }
            )
        
        faces_data = []
        for i, (x, y, w, h) in enumerate(faces):
            faces_data.append({
                "face_number": i + 1,
                "position": {
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h)
                }
            })
        
        db = load_database()
        db["scan_history"].append({
            "timestamp": datetime.now().isoformat(),
            "faces_detected": len(faces),
            "type": "scan"
        })
        save_database(db)
        
        return {
            "status": "success",
            "detected_faces": len(faces),
            "faces": faces_data,
            "message": f"Waxaa la helay {len(faces)} weji"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Qalad dhacay: {str(e)}")

@app.post("/detect-faces/")
async def detect_faces(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Sawirka lama akhrin karo")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 3)
            cv2.putText(img, "Face", (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        _, buffer = cv2.imencode('.jpg', img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            "status": "success",
            "detected_faces": len(faces),
            "image": f"data:image/jpeg;base64,{img_base64}",
            "message": f"Waxaa la helay {len(faces)} weji"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Qalad dhacay: {str(e)}")

@app.get("/immigrants/")
def get_immigrants():
    db = load_database()
    return {"status": "success", "total": len(db["immigrants"]), "immigrants": db["immigrants"]}

@app.post("/immigrants/")
def add_immigrant(immigrant: Immigrant):
    db = load_database()
    new_immigrant = immigrant.dict()
    new_immigrant["id"] = len(db["immigrants"]) + 1
    new_immigrant["registered_at"] = datetime.now().isoformat()
    db["immigrants"].append(new_immigrant)
    save_database(db)
    return {"status": "success", "message": "Ajaanib cusub waa la diiwaangeliyay", "immigrant": new_immigrant}

@app.get("/officers/")
def get_officers():
    db = load_database()
    return {"status": "success", "total": len(db["officers"]), "officers": db["officers"]}

@app.post("/officers/")
def add_officer(officer: Officer):
    db = load_database()
    new_officer = officer.dict()
    new_officer["id"] = len(db["officers"]) + 1
    db["officers"].append(new_officer)
    save_database(db)
    return {"status": "success", "officer": new_officer}

@app.get("/admins/")
def get_admins():
    db = load_database()
    return {"status": "success", "total": len(db["admins"]), "admins": db["admins"]}

@app.post("/admins/")
def add_admin(admin: Admin):
    db = load_database()
    new_admin = admin.dict()
    new_admin["id"] = len(db["admins"]) + 1
    db["admins"].append(new_admin)
    save_database(db)
    return {"status": "success", "admin": new_admin}

@app.get("/stats/")
def get_stats():
    db = load_database()
    return {
        "status": "success",
        "stats": {
            "total_immigrants": len(db["immigrants"]),
            "total_officers": len(db["officers"]),
            "total_admins": len(db["admins"]),
            "total_scans": len(db["scan_history"]),
            "total_countries": 197,
            "total_offices": 45
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
