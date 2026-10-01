"""Root entry point that re-exports the backend API app."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_APP = ROOT / "backend-api" / "app.py"

_spec = importlib.util.spec_from_file_location("backend_api_app", BACKEND_APP)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Unable to load backend app from {BACKEND_APP}")

_backend_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_backend_module)

app = _backend_module.app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
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
