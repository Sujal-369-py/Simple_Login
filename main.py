from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from passlib.context import CryptContext
import asyncio

app = FastAPI()
BASE_DIR = Path(__file__).parent

# MongoDB
client = AsyncIOMotorClient("mongodb+srv://UserXts_db_user:6UOSD2hon4O9dnz5@cluster0.znfwoni.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["test_subject_1"]["test_subject_users"]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/image", StaticFiles(directory=BASE_DIR / "image"), name="image")

# Index
@app.get("/")
def home():
    return FileResponse(BASE_DIR / "index.html")

# Register
@app.post("/register")
async def register_user(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if await db.find_one({"username": username}):
        return JSONResponse(content={"message": "❌ Username already exists! Waiting..."}, status_code=400)
    
    hashed_password = pwd_context.hash(password)
    await db.insert_one({"username": username, "email": email, "password": hashed_password})
    
    # Wait 2 seconds before returning success
    await asyncio.sleep(2)
    
    return JSONResponse(content={"message": "✅ Registration successful! Waiting..."})

# Login
@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = await db.find_one({"username": username})
    if not user:
        return JSONResponse(content={"message": "❌ User does not exist! Waiting..."}, status_code=400)
    
    if not pwd_context.verify(password, user["password"]):
        return JSONResponse(content={"message": "❌ Wrong password! Waiting..."}, status_code=400)
    
    # Wait 2 seconds before returning success
    await asyncio.sleep(2)
    
    return JSONResponse(content={"message": "✅ Login successful! Waiting..."})
