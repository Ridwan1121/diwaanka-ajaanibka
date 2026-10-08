"""
Diwaanka Ajaanibka - Backend API (DHAMAYSTIRAN)
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
import cv2
import numpy as np
import base64
import json
import os

from database import init_db, get_db, ImmigrantDB, OfficerDB, AdminDB, UserDB, ScanHistoryDB

try:
    from face_service import face_service
except ImportError:
    face_service = None

try:
    from liveness import liveness_detector
except ImportError:
    liveness_detector = None

try:
    from websocket_manager import manager
except ImportError:
    manager = None


# ============================================================
# CONFIGURATION
# ============================================================
SECRET_KEY = os.getenv("SECRET_KEY", "diwaanka-ajaanibka-secret-key-2026-very-secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

APP_ENV = os.getenv("APP_ENV", "development")


# ============================================================
# USERS_DB
# ============================================================
USERS_DB = {
    "Ridwan": {
        "username": "Ridwan",
        "full_name": "Ridwan Farah",
        "email": "ridwan@diwaanka.so",
        "hashed_password": pwd_context.hash("AKIID12345"),
        "role": "admin",
        "disabled": False
    },
    "officer": {
        "username": "officer",
        "full_name": "Xasan Cali",
        "email": "officer@diwaanka.so",
        "hashed_password": pwd_context.hash("officer123"),
        "role": "officer",
        "disabled": False
    }
}


# ============================================================
# JWT FUNCTIONS
# ============================================================
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str):
    user = USERS_DB.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token-ka waa khaldan ama wuu dhamaaday",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = USERS_DB.get(username)
    if user is None:
        raise credentials_exception
    return user


# ============================================================
# APP
# ============================================================
app = FastAPI(
    title="Diwaanka Ajaanibka API",
    description="API-ga weji-aqoonsiga ee hay'adda socdaalka",
    version="2.0.0"
)

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MODELS
# ============================================================
class Immigrant(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    country: str = Field(..., min_length=2, max_length=100)
    region: str = Field(..., min_length=2, max_length=100)
    entry_point: str = Field(..., min_length=2, max_length=100)
    district: str = Field(..., min_length=2, max_length=100)
    passport: Optional[str] = None
    status: str = Field("registered", pattern="^(registered|pending|approved|rejected)$")


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


# ============================================================
# ENDPOINTS
# ============================================================
@app.get("/")
def home():
    return {
        "status": "success",
        "message": "Ku soo dhawaada API-ga Diwaanka Ajaanibka!",
        "version": "2.0.0",
        "endpoints": {
            "/health": "Hubi haddii API-gu shaqeynayo",
            "/token": "Login - hel JWT token",
            "/users/me": "Macluumaadka isticmaalaha",
            "/scan-face/": "Aqoonso wejiyada sawirka",
            "/detect-faces/": "Soo bandhig wejiyada sawirka",
            "/register-face/{immigrant_id}": "Diiwaangeli wejiga ajaanib",
            "/check-liveness/": "Hubi haddii sawirku yahay qof nool",
            "/immigrants/": "Liiska ajaanibta",
            "/stats/": "Tirakoobka nidaamka"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API-ga waa shaqeynayaa si fiican"}


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username ama password waa khaldan",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
    }


@app.get("/users/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "full_name": current_user["full_name"],
        "email": current_user["email"],
        "role": current_user["role"]
    }


# ============================================================
# FACE RECOGNITION
# ============================================================
@app.post("/scan-face/")
async def scan_face(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Fadlan soo gudbi sawir sax ah")
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Sawirka lama akhrin karo")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) == 0:
            return {"status": "warning", "detected_faces": 0, "faces": [], "message": "Wax weji ah lagama helin"}
        faces_data = []
        for i, (x, y, w, h) in enumerate(faces):
            faces_data.append({
                "face_number": i + 1,
                "position": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}
            })
        return {
            "status": "success",
            "detected_faces": len(faces),
            "faces": faces_data,
            "message": f"Waxaa la helay {len(faces)} weji"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Qalad dhacay: {str(e)}")


@app.post("/detect-faces/")
async def detect_faces(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Sawirka lama akhrin karo")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 3)
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


@app.post("/register-face/{immigrant_id}")
async def register_face(immigrant_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Sawirka lama akhrin karo")
        immigrant = db.query(ImmigrantDB).filter(ImmigrantDB.id == immigrant_id).first()
        if not immigrant:
            raise HTTPException(status_code=404, detail="Ajaanib lama helin")
        if face_service:
            encoding = face_service.get_encoding(img)
            if encoding:
                immigrant.face_encoding = json.dumps(encoding)
                db.commit()
                return {"status": "success", "message": f"Wejiga {immigrant.name} waa la diiwaangeliyay", "encoding_size": len(encoding)}
        return {"status": "warning", "message": "DeepFace lama rakibin - Haar Cascade ayaa la isticmaalayaa"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Qalad dhacay: {str(e)}")


@app.post("/check-liveness/")
async def check_liveness(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Sawirka lama akhrin karo")
        if liveness_detector:
            result = liveness_detector.check_liveness(img)
            return {"status": "success", "result": result}
        return {"status": "warning", "message": "Liveness detector lama helin"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Qalad dhacay: {str(e)}")


# ============================================================
# IMMIGRANTS
# ============================================================
@app.get("/immigrants/")
def get_immigrants(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    immigrants = db.query(ImmigrantDB).all()
    return {"status": "success", "total": len(immigrants), "immigrants": immigrants}


@app.post("/immigrants/")
def add_immigrant(immigrant: Immigrant, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    new_immigrant = ImmigrantDB(**immigrant.dict())
    db.add(new_immigrant)
    db.commit()
    db.refresh(new_immigrant)
    return {"status": "success", "message": "Ajaanib cusub waa la diiwaangeliyay", "immigrant": new_immigrant}


@app.put("/immigrants/{immigrant_id}")
def update_immigrant(immigrant_id: int, immigrant: Immigrant, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_immigrant = db.query(ImmigrantDB).filter(ImmigrantDB.id == immigrant_id).first()
    if not db_immigrant:
        raise HTTPException(status_code=404, detail="Ajaanib lama helin")
    for key, value in immigrant.dict().items():
        setattr(db_immigrant, key, value)
    db.commit()
    db.refresh(db_immigrant)
    return {"status": "success", "message": "Ajaanib waa la cusbooneysiiyay", "immigrant": db_immigrant}


@app.delete("/immigrants/{immigrant_id}")
def delete_immigrant(immigrant_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_immigrant = db.query(ImmigrantDB).filter(ImmigrantDB.id == immigrant_id).first()
    if not db_immigrant:
        raise HTTPException(status_code=404, detail="Ajaanib lama helin")
    db.delete(db_immigrant)
    db.commit()
    return {"status": "success", "message": "Ajaanib waa la tirtiray"}


# ============================================================
# STATS
# ============================================================
@app.get("/stats/")
def get_stats(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    total_immigrants = db.query(ImmigrantDB).count()
    total_officers = db.query(OfficerDB).count()
    total_admins = db.query(AdminDB).count()
    total_scans = db.query(ScanHistoryDB).count()
    return {
        "status": "success",
        "stats": {
            "total_immigrants": total_immigrants,
            "total_officers": total_officers,
            "total_admins": total_admins,
            "total_scans": total_scans,
            "total_countries": 197,
            "total_offices": 45
        }
    }


# ============================================================
# WEBSOCKET
# ============================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if manager:
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await manager.broadcast(f"Message: {data}")
        except WebSocketDisconnect:
            manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
