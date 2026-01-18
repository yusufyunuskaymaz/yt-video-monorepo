"""
Video Generator API - FastAPI
Node.js backend ile iletişim için
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys

# Config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import API_PORT

# Routes
from routes.video import router as video_router

# FastAPI App
app = FastAPI(
    title="Video Generator API",
    description="Resimden video üretimi servisi",
    version="1.0.0"
)

# CORS - Node.js'den erişim için
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(video_router)


# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Video Generator API",
        "version": "1.0.0",
        "endpoints": {
            "generate_async": "POST /api/video/generate",
            "generate_sync": "POST /api/video/generate-sync",
            "health": "GET /api/video/health"
        }
    }


# Ana giriş noktası
if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════╗
║           🎬 VIDEO GENERATOR API                     ║
╠══════════════════════════════════════════════════════╣
║  Endpoint: http://localhost:{API_PORT}                      ║
║  Docs:     http://localhost:{API_PORT}/docs                 ║
╚══════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=API_PORT,
        reload=True
    )
