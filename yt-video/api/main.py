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
from routes.performance import router as performance_router

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
app.include_router(performance_router)


# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Video Generator API",
        "version": "1.0.0",
        "endpoints": {
            "generate_async": "POST /api/video/generate",
            "generate_sync": "POST /api/video/generate-sync",
            "merge_video_audio": "POST /api/video/merge-video-audio",
            "health": "GET /api/video/health",
            "performance_summary": "GET /api/performance/summary",
            "performance_project": "GET /api/performance/project/{id}",
            "performance_all": "GET /api/performance/projects",
            "performance_clear": "POST /api/performance/clear"
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
