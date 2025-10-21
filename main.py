from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
import os

app = FastAPI()
BASE_DIR = Path(__file__).parent

# ----------------------------
# MongoDB Connection
# ----------------------------
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    raise RuntimeError("❌ MONGO_URI environment variable not set!")

try:
    client = AsyncIOMotorClient(mongo_uri, tls=True, serverSelectionTimeoutMS=5000)
    db = client["test_subject_1"]["test_subject_users"]
except Exception as e:
    print("❌ MongoDB connection failed:", e)
    raise

# ----------------------------
# No-Cache StaticFiles Class
# ----------------------------
class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            # Prevent browsers from caching static assets
            response.headers["Cache-Control"] = "no-store"
        return response

# ----------------------------
# Static File Mounts
# ----------------------------

# Serve static assets (CSS, JS, etc.)
index_static_dir = BASE_DIR / "static"
if index_static_dir.exists():
    app.mount("/static", NoCacheStaticFiles(directory=index_static_dir), name="static")
else:
    print("⚠️ Missing: 'static' folder (index CSS/JS).")

# Serve CSS for other pages (home, about, php)
work_dir = BASE_DIR / "others" / "work"
if work_dir.exists():
    app.mount("/work", NoCacheStaticFiles(directory=work_dir), name="work")
else:
    print("⚠️ Missing: 'others/work' folder (CSS for subpages).")

# Serve images
image_dir = BASE_DIR / "image"
if image_dir.exists():
    app.mount("/image", NoCacheStaticFiles(directory=image_dir), name="image")
else:
    print("⚠️ Missing: 'image' folder (images).")

# Serve other HTML pages (home.html, about.html, etc.)
others_dir = BASE_DIR / "others"
if others_dir.exists():
    app.mount("/others", NoCacheStaticFiles(directory=others_dir), name="others")
else:
    print("⚠️ Missing: 'others' folder (HTML pages).")

# ----------------------------
# Routes
# ----------------------------

@app.get("/")
def get_index():
    """Serve the main index.html page"""
    index_path = BASE_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse({"message": "❌ index.html not found!"}, status_code=404)


@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """User login"""
    try:
        user = await db.find_one({"username": username})
        if not user:
            return JSONResponse({"message": "❌ User does not exist!"}, status_code=400)

        if password != user["password"]:
            return JSONResponse({"message": "❌ Wrong password!"}, status_code=400)

        # ✅ Successful login → redirect to home.html
        return RedirectResponse(url="/others/home.html", status_code=303)

    except Exception as e:
        print("❌ Login error:", e)
        return JSONResponse({"message": "Internal server error."}, status_code=500)


@app.post("/register")
async def register_user(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    """User registration"""
    try:
        if await db.find_one({"username": username}):
            return JSONResponse({"message": "❌ Username already exists!"}, status_code=400)

        await db.insert_one({"username": username, "email": email, "password": password})
        return JSONResponse({"message": "✅ Registration successful!"})

    except Exception as e:
        print("❌ Registration error:", e)
        return JSONResponse({"message": "Internal server error."}, status_code=500)

# ----------------------------
# Run Command (Development)
# ----------------------------
# uvicorn main:app --reload
