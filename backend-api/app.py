from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from database import init_db, get_db, ImmigrantDB, OfficerDB, AdminDB, UserDB, ScanHistoryDB
from face_service import face_service
from liveness import liveness_detector
from websocket_manager import manager
from sqlalchemy.orm import Session
from fastapi import WebSocket, WebSocketDisconnect
from typing import Optional
import cv2
import numpy as np
import base64
import json
import os

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if APP_ENV == "production":
        raise RuntimeError("SECRET_KEY must be configured in production")
    SECRET_KEY = "local-development-only-change-before-deploy"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def make_user(username: str, full_name: str, email: str, password: str, role: str):
    return {
        "username": username,
        "full_name": full_name,
        "email": email,
        "hashed_password": pwd_context.hash(password),
        "role": role,
        "disabled": False,
    }


if APP_ENV == "production":
    user_settings = {
        "ADMIN_USERNAME": os.getenv("ADMIN_USERNAME"),
        "ADMIN_PASSWORD": os.getenv("ADMIN_PASSWORD"),
        "OFFICER_USERNAME": os.getenv("OFFICER_USERNAME"),
        "OFFICER_PASSWORD": os.getenv("OFFICER_PASSWORD"),
    }
    missing_user_settings = [key for key, value in user_settings.items() if not value]
    if missing_user_settings:
        raise RuntimeError(
            "Missing production login settings: " + ", ".join(missing_user_settings)
        )
    USERS_DB = {
        user_settings["ADMIN_USERNAME"]: make_user(
            user_settings["ADMIN_USERNAME"],
            "Administrator",
            "admin@diwaanka.so",
            user_settings["ADMIN_PASSWORD"],
            "admin",
        ),
        user_settings["OFFICER_USERNAME"]: make_user(
            user_settings["OFFICER_USERNAME"],
            "Officer",
            "officer@diwaanka.so",
            user_settings["OFFICER_PASSWORD"],
            "officer",
        ),
    }
else:
    USERS_DB = {
        "admin": make_user("admin", "Administrator", "admin@diwaanka.so", "admin123", "admin"),
        "Ridwan": make_user("Ridwan", "Ridwan Farah", "ridwan@diwaanka.so", "AKIID12345", "admin"),
        "officer": make_user("officer", "Xasan Cali", "officer@diwaanka.so", "officer123", "officer"),
    }

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
    if user is None or user.get("disabled", False):
        raise credentials_exception
    return user

app = FastAPI(title="Diwaanka Ajaanibka API")

# Init database
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = os.path.join(os.path.dirname(__file__), "database.json")

def load_database():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"immigrants": [], "officers": [], "admins": [], "scan_history": []}

@app.get("/")
def home():
    return {"status": "success", "message": "Ku soo dhawaada API-ga Diwaanka Ajaanibka!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username ama password waa khaldan",
        )
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
        "role": current_user["role"]
    }

async def decode_uploaded_image(file: UploadFile):
    contents = await file.read(10 * 1024 * 1024 + 1)
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Sawirku waa inuu ka yaraadaa 10MB")
    image = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Faylka la soo diray ma aha sawir sax ah")
    return image


@app.post("/scan-face/")
async def scan_face(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    image = await decode_uploaded_image(file)
    faces = face_service.detect_faces(image)
    return {
        "status": "success",
        "detected_faces": len(faces),
        "faces": faces,
        "message": f"Waxaa la helay {len(faces)} weji",
    }


@app.post("/detect-faces/")
async def detect_faces(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    image = await decode_uploaded_image(file)
    faces = face_service.detect_faces(image)
    for face in faces:
        position = face["position"]
        x, y = position["x"], position["y"]
        width, height = position["width"], position["height"]
        cv2.rectangle(image, (x, y), (x + width, y + height), (0, 255, 0), 3)
    encoded, buffer = cv2.imencode(".jpg", image)
    if not encoded:
        raise HTTPException(status_code=500, detail="Sawirka lama diyaarin karo")
    image_base64 = base64.b64encode(buffer).decode("ascii")
    return {
        "status": "success",
        "detected_faces": len(faces),
        "faces": faces,
        "image": f"data:image/jpeg;base64,{image_base64}",
        "message": f"Waxaa la helay {len(faces)} weji",
    }

@app.get("/immigrants/")
def get_immigrants(current_user: dict = Depends(get_current_user)):
    db = load_database()
    return {"status": "success", "total": len(db["immigrants"]), "immigrants": db["immigrants"]}

@app.get("/stats/")
def get_stats(current_user: dict = Depends(get_current_user)):
    db = load_database()
    return {
        "status": "success",
        "stats": {
            "total_immigrants": len(db["immigrants"]),
            "total_officers": len(db["officers"]),
            "total_admins": len(db["admins"]),
            "total_countries": 197,
            "total_offices": 45
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


