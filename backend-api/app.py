from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import cv2
import numpy as np
import base64
import json
import os

SECRET_KEY = "diwaanka-ajaanibka-secret-key-2026-very-secure"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

USERS_DB = {
    "Ridwan": {
        "username": "Ridwan",
        "full_name": "Ridwan Farah",
        "email": "ridwan@diwaanka.so",
        "hashed_password": pwd_context.hash("AKIID12345"),
        "role": "Ridwan",
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
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
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

app = FastAPI(title="Diwaanka Ajaanibka API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

@app.post("/scan-face/")
async def scan_face(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    return {
        "status": "success",
        "detected_faces": len(faces),
        "message": f"Waxaa la helay {len(faces)} weji"
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

