from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, Form, Header  # type: ignore[import-not-found]
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt  # type: ignore[import-not-found]
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import cv2
import numpy as np
import base64
import json
import os


class OAuth2PasswordBearer:
    def __init__(self, tokenUrl: str):
        self.tokenUrl = tokenUrl

    async def __call__(self, authorization: Optional[str] = Header(default=None)):
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return authorization[7:].strip()


class OAuth2PasswordRequestForm:
    def __init__(
        self,
        username: str = Form(...),
        password: str = Form(...),
    ):
        self.username = username
        self.password = password

# ============================================================
# JWT CONFIGURATION
# ============================================================
SECRET_KEY = "diwaanka-ajaanibka-secret-key-2026-very-secure"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

USERS_DB = {
    "admin": {
        "username": "admin",
        "full_name": "Dr. Axmed Cali",
        "email": "admin@diwaanka.so",
        "hashed_password": pwd_context.hash("admin123"),
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

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

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
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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

async def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kaliya maamulayaasha ayaa geli kara"
        )
    return current_user

# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(title="Diwaanka Ajaanibka API")

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
    return {"immigrants": [], "officers": [], "admins": [], "scan_history": []}

def save_database(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.get("/")
def home():
    return {"status": "success", "message": "Ku soo dhawaada API-ga Diwaanka Ajaanibka!"}

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
            "total_scans": len(db["scan_history"]),
            "total_countries": 197,
            "total_offices": 45
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
