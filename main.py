from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
import asyncio
import os

app = FastAPI()
BASE_DIR = Path(__file__).parent

# MongoDB Connection
mongo_uri = os.getenv("MONGO_URI")

if not mongo_uri:
    raise RuntimeError("❌ MONGO_URI environment variable not set!")

try:
    client = AsyncIOMotorClient(mongo_uri, tls=True, serverSelectionTimeoutMS=5000)
    db = client["test_subject_1"]["test_subject_users"]
except Exception as e:
    print("❌ MongoDB connection failed:", e)
    raise

# Static files
if (BASE_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

if (BASE_DIR / "image").exists():
    app.mount("/image", StaticFiles(directory=BASE_DIR / "image"), name="image")

# Index route
@app.get("/")
def home():
    return FileResponse(BASE_DIR / "index.html")

# Register route
@app.post("/register")
async def register_user(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    try:
        # Check existing user
        if await db.find_one({"username": username}):
            return JSONResponse(content={"message": "❌ Username already exists!"}, status_code=400)

        # Store password as plain text
        await db.insert_one({"username": username, "email": email, "password": password})

        await asyncio.sleep(2)
        return JSONResponse(content={"message": "✅ Registration successful!"})
    
    except Exception as e:
        print("❌ Error during registration:", e)
        return JSONResponse(content={"message": "Internal server error. Please try again later."}, status_code=500)

# Login route
@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    try:
        user = await db.find_one({"username": username})
        if not user:
            return JSONResponse(content={"message": "❌ User does not exist!"}, status_code=400)

        if password != user["password"]:
            return JSONResponse(content={"message": "❌ Wrong password!"}, status_code=400)

        await asyncio.sleep(2)
        return JSONResponse(content={"message": "✅ Login successful!"})

    except Exception as e:
        print("❌ Error during login:", e)
        return JSONResponse(content={"message": "Internal server error. Please try again later."}, status_code=500)
