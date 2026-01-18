"""
Video API Routes
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import requests
import os
import sys

# Services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.video_service import process_video, merge_video_with_audio, concatenate_videos

router = APIRouter(prefix="/api/video", tags=["video"])


# Request/Response Models
class SubtitleItem(BaseModel):
    start: float
    end: float
    text: str


class GenerateVideoRequest(BaseModel):
    image_url: str
    scene_id: str | int  # String veya Int kabul et
    duration: Optional[int] = 10
    pan_direction: Optional[str] = "vertical"  # "horizontal" veya "vertical" (default: aşağıdan yukarı)
    subtitles: Optional[List[SubtitleItem]] = None
    callback_url: Optional[str] = None


class MergeVideoAudioRequest(BaseModel):
    video_url: str
    audio_url: str
    scene_id: str | int  # String veya Int kabul et
    narration: Optional[str] = None  # Altyazı metni
    callback_url: Optional[str] = None


class GenerateVideoResponse(BaseModel):
    success: bool
    message: str
    scene_id: str | int


# Background task - Video işleme ve callback
def process_video_task(
    image_url: str,
    scene_id: str,
    duration: int,
    pan_direction: str,
    subtitles: list,
    callback_url: str
):
    """Arka planda video işle ve callback yap"""
    print(f"\n🔄 Background task başlatıldı: {scene_id}")
    
    # Subtitles'ı dict listesine çevir
    subtitle_dicts = None
    if subtitles:
        subtitle_dicts = [{"start": s.start, "end": s.end, "text": s.text} for s in subtitles]
    
    # Video işle
    result = process_video(
        image_url=image_url,
        scene_id=scene_id,
        duration=duration,
        pan_direction=pan_direction,
        subtitles=subtitle_dicts
    )
    
    # Callback yap (Node.js'e haber ver)
    if callback_url:
        try:
            print(f"\n📤 Callback gönderiliyor: {callback_url}")
            payload = {
                "scene_id": scene_id,
                "status": "completed" if result["success"] else "failed",
                "video_url": result.get("video_url"),
                "error": result.get("error")
            }
            response = requests.post(callback_url, json=payload, timeout=10)
            print(f"✅ Callback başarılı: {response.status_code}")
        except Exception as e:
            print(f"❌ Callback hatası: {str(e)}")
    
    return result


# Endpoints
@router.post("/generate", response_model=GenerateVideoResponse)
async def generate_video(request: GenerateVideoRequest, background_tasks: BackgroundTasks):
    """
    Video üretimini başlat (async)
    
    - Resmi indirir
    - Ken Burns efekti ile video oluşturur
    - Opsiyonel olarak altyazı ekler
    - CDN'e yükler
    - Callback URL'e sonucu bildirir
    """
    if not request.image_url:
        raise HTTPException(status_code=400, detail="image_url gerekli")
    
    if not request.scene_id:
        raise HTTPException(status_code=400, detail="scene_id gerekli")
    
    # İşlemi arka plana at
    background_tasks.add_task(
        process_video_task,
        request.image_url,
        request.scene_id,
        request.duration,
        request.pan_direction,
        request.subtitles,
        request.callback_url
    )
    
    return GenerateVideoResponse(
        success=True,
        message="Video üretimi başlatıldı",
        scene_id=request.scene_id
    )


@router.post("/generate-sync")
async def generate_video_sync(request: GenerateVideoRequest):
    """
    Video üretimini senkron çalıştır (test için)
    İşlem bitene kadar bekler ve sonucu döner
    """
    if not request.image_url:
        raise HTTPException(status_code=400, detail="image_url gerekli")
    
    if not request.scene_id:
        raise HTTPException(status_code=400, detail="scene_id gerekli")
    
    # Subtitles'ı dict listesine çevir
    subtitle_dicts = None
    if request.subtitles:
        subtitle_dicts = [{"start": s.start, "end": s.end, "text": s.text} for s in request.subtitles]
    
    # Video işle (senkron)
    result = process_video(
        image_url=request.image_url,
        scene_id=request.scene_id,
        duration=request.duration,
        pan_direction=request.pan_direction,
        subtitles=subtitle_dicts
    )
    
    return result


@router.post("/merge-video-audio")
async def merge_video_audio_endpoint(request: MergeVideoAudioRequest):
    """
    Sessiz video ile sesi birleştir (senkron)
    
    - Sessiz videoyu indirir
    - Sesi indirir
    - Birleştirir
    - CDN'e yükler
    """
    if not request.video_url:
        raise HTTPException(status_code=400, detail="video_url gerekli")
    
    if not request.audio_url:
        raise HTTPException(status_code=400, detail="audio_url gerekli")
    
    if not request.scene_id:
        raise HTTPException(status_code=400, detail="scene_id gerekli")
    
    # Birleştir
    result = merge_video_with_audio(
        video_url=request.video_url,
        audio_url=request.audio_url,
        scene_id=request.scene_id,
        narration=request.narration
    )
    
    return result


class ConcatenateVideosRequest(BaseModel):
    video_urls: List[str]  # Sıralı video URL listesi
    project_id: str | int  # String veya Int kabul et


@router.post("/concatenate")
async def concatenate_videos_endpoint(request: ConcatenateVideosRequest):
    """
    Birden fazla videoyu tek videoya birleştir (senkron)
    
    - Tüm videoları indirir
    - FFmpeg concat ile birleştirir
    - CDN'e yükler
    """
    if not request.video_urls or len(request.video_urls) == 0:
        raise HTTPException(status_code=400, detail="video_urls listesi boş olamaz")
    
    if not request.project_id:
        raise HTTPException(status_code=400, detail="project_id gerekli")
    
    result = concatenate_videos(
        video_urls=request.video_urls,
        project_id=request.project_id
    )
    
    return result


@router.get("/health")
async def health_check():
    """API sağlık kontrolü"""
    return {"status": "ok", "service": "video-generator"}
