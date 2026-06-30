from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.utils.db import init_db
from app.api.routes import router
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting School AI Assistant...")
    init_db()
    yield
    print("🛑 Shutting down...")

app = FastAPI(
    title="School AI ERP Assistant",
    description="AI-powered School ERP Assistant using LangGraph + Groq",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router, prefix="/api/v1")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "app", "static")

@app.get("/")
def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")