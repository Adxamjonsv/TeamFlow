import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Telegram Vazifa Bot Mini App")


@app.get("/health")
async def health_check():
    """Railway health check for the combined bot and Mini App service."""
    return JSONResponse({"status": "ok"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Statik fayllar
static_dir = os.path.join(BASE_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# API marshrutlari
app.include_router(api_router)

# Asosiy Mini App sahifasi
@app.get("/")
@app.get("/app")
async def serve_index():
    index_file = os.path.join(BASE_DIR, "templates", "index.html")
    return FileResponse(index_file)

