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
    scene_id: str | int
    duration: Optional[int] = 10
    pan_direction: Optional[str] = "vertical"
    subtitles: Optional[List[SubtitleItem]] = None
    callback_url: Optional[str] = None
    project_id: Optional[str | int] = None
    scene_number: Optional[int] = None
    skip_cdn: Optional[bool] = False


class MergeVideoAudioRequest(BaseModel):
    video_url: str
    audio_url: str
    scene_id: str | int
    narration: Optional[str] = None
    callback_url: Optional[str] = None
    project_id: Optional[str | int] = None
    scene_number: Optional[int] = None
    skip_cdn: Optional[bool] = False


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
    callback_url: str,
    project_id: str = None,
    scene_number: int = None
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
        subtitles=subtitle_dicts,
        project_id=project_id,
        scene_number=scene_number
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
    """Video üretimini başlat (async)"""
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
        request.callback_url,
        str(request.project_id) if request.project_id else None,
        request.scene_number
    )
    
    return GenerateVideoResponse(
        success=True,
        message="Video üretimi başlatıldı",
        scene_id=request.scene_id
    )


@router.post("/generate-sync")
async def generate_video_sync(request: GenerateVideoRequest):
    """Video üretimini senkron çalıştır (test için)"""
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
        subtitles=subtitle_dicts,
        project_id=str(request.project_id) if request.project_id else None,
        scene_number=request.scene_number,
        skip_cdn=request.skip_cdn
    )
    
    return result


@router.post("/merge-video-audio")
async def merge_video_audio_endpoint(request: MergeVideoAudioRequest):
    """Sessiz video ile sesi birleştir (senkron)"""
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
        narration=request.narration,
        project_id=str(request.project_id) if request.project_id else None,
        scene_number=request.scene_number,
        skip_cdn=request.skip_cdn
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


# GPU Test Endpoint
class GpuTestRequest(BaseModel):
    video_urls: List[str]  # 3 CDN video URL (her biri ~10 saniye)
    target_duration_seconds: int = 900  # Hedef süre (default: 15 dakika)
    test_name: Optional[str] = "gpu_test"  # Test adı


@router.post("/gpu-test")
async def gpu_test_endpoint(request: GpuTestRequest):
    """
    🧪 RunPod GPU Test Endpoint
    
    Hazır video sahnelerini alır, hedef süreye ulaşana kadar tekrarlar.
    GPU encoding performansını test etmek için kullanılır.
    
    Örnek:
    - 3 video URL ver (her biri 10 saniye)
    - target_duration_seconds: 900 (15 dakika)
    - 30 sahne = 900 saniye video
    """
    from services.video_service import gpu_test_loop_videos
    
    if not request.video_urls or len(request.video_urls) == 0:
        raise HTTPException(status_code=400, detail="video_urls listesi boş olamaz")
    
    if request.target_duration_seconds < 10:
        raise HTTPException(status_code=400, detail="target_duration_seconds en az 10 olmalı")
    
    result = gpu_test_loop_videos(
        video_urls=request.video_urls,
        target_duration_seconds=request.target_duration_seconds,
        test_name=request.test_name
    )
    
    return result


# Download to local - Harici URL'i proje dizinine indir
class DownloadToLocalRequest(BaseModel):
    url: str
    project_id: str | int
    filename: str


@router.post("/download-to-local")
async def download_to_local(request: DownloadToLocalRequest):
    """Harici URL'i proje dizinine indir (CDN atlama)"""
    from services.video_service import get_project_dir, download_file
    
    try:
        project_dir = get_project_dir(str(request.project_id))
        local_path = os.path.join(project_dir, request.filename)
        
        print(f"📥 İndiriliyor: {request.url[:80]}...")
        print(f"📂 Hedef: {local_path}")
        
        download_file(request.url, local_path)
        
        print(f"✅ İndirildi: {local_path}")
        
        return {
            "success": True,
            "local_path": local_path,
            "filename": request.filename
        }
    except Exception as e:
        print(f"❌ İndirme hatası: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# Toplu CDN Upload - Proje dosyalarını CDN'e yükle
class UploadProjectAssetsRequest(BaseModel):
    project_id: str | int
    files: List[dict]  # [{"local_path": "...", "type": "image|video|merged", "scene_number": 1}]


class FileUploadItem(BaseModel):
    local_path: str
    type: str  # image, video, merged
    scene_number: int


@router.post("/upload-project-assets")
async def upload_project_assets(request: UploadProjectAssetsRequest):
    """
    Proje dosyalarını toplu CDN'e yükle.
    Pipeline sonunda çağrılır - tüm lokal dosyaları CDN'e yükler.
    """
    from services.cdn_service import upload_file
    import time
    
    project_id = str(request.project_id)
    results = []
    failed = 0
    
    print(f"\n☁️ ========== TOPLU CDN UPLOAD ==========")
    print(f"📁 Proje: {project_id}")
    print(f"📦 Dosya sayısı: {len(request.files)}")
    print(f"==========================================\n")
    
    for item in request.files:
        local_path = item.get("local_path", "")
        file_type = item.get("type", "unknown")
        scene_number = item.get("scene_number", 0)
        
        if not os.path.exists(local_path):
            print(f"⚠️ Dosya bulunamadı: {local_path}")
            failed += 1
            continue
        
        try:
            timestamp = int(time.time())
            scene_tag = str(scene_number).zfill(3)
            
            # Dosya tipine göre key ve content_type belirle
            if file_type == "image":
                ext = os.path.splitext(local_path)[1] or ".png"
                key = f"images/{project_id}_scene_{scene_tag}_{timestamp}{ext}"
                content_type = "image/png"
            elif file_type == "video":
                key = f"videos/{project_id}_scene_{scene_tag}_{timestamp}.mp4"
                content_type = "video/mp4"
            elif file_type == "merged":
                key = f"videos/{project_id}_merged_{scene_tag}_{timestamp}.mp4"
                content_type = "video/mp4"
            else:
                key = f"files/{project_id}_{scene_tag}_{timestamp}"
                content_type = "application/octet-stream"
            
            cdn_url = upload_file(local_path, key, content_type)
            
            results.append({
                "scene_number": scene_number,
                "type": file_type,
                "cdn_url": cdn_url,
                "local_path": local_path
            })
            
            print(f"✅ [{file_type}] Sahne {scene_number} → {cdn_url}")
            
        except Exception as e:
            print(f"❌ [{file_type}] Sahne {scene_number} yükleme hatası: {str(e)}")
            failed += 1
    
    print(f"\n🎉 Toplu upload tamamlandı: {len(results)} başarılı, {failed} başarısız\n")
    
    return {
        "success": True,
        "uploads": results,
        "total": len(request.files),
        "uploaded": len(results),
        "failed": failed
    }


class CleanupProjectRequest(BaseModel):
    project_id: str | int


@router.post("/cleanup-project")
async def cleanup_project(request: CleanupProjectRequest):
    """Pipeline sonunda proje dizinini temizle"""
    import shutil
    from services.video_service import get_project_dir
    
    project_dir = get_project_dir(str(request.project_id))
    
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
        print(f"🧹 Proje dosyaları temizlendi: {project_dir}")
        return {"success": True, "message": f"Proje dizini silindi: {project_dir}"}
    else:
        return {"success": True, "message": "Dizin zaten mevcut değil"}


# Ses parçalarını birleştir (Multilingual TTS chunking için)
class ConcatAudioRequest(BaseModel):
    audio_paths: List[str]  # Lokal ses dosya yolları
    project_id: str | int
    output_filename: str = "audio_merged.wav"


@router.post("/concat-audio")
async def concat_audio(request: ConcatAudioRequest):
    """Birden fazla ses dosyasını FFmpeg ile birleştir"""
    import subprocess
    import json
    from services.video_service import get_project_dir

    project_dir = get_project_dir(str(request.project_id))
    output_path = os.path.join(project_dir, request.output_filename)

    print(f"\n🔗 ========== SES BİRLEŞTİRME ==========")
    print(f"📦 Parça sayısı: {len(request.audio_paths)}")
    print(f"📂 Çıktı: {output_path}")
    print(f"==========================================\n")

    try:
        if len(request.audio_paths) == 1:
            # Tek dosya - kopyala
            import shutil
            shutil.copy2(request.audio_paths[0], output_path)
        else:
            # FFmpeg concat listesi oluştur
            concat_list_path = os.path.join(project_dir, "audio_concat_list.txt")
            with open(concat_list_path, 'w') as f:
                for path in request.audio_paths:
                    f.write(f"file '{path}'\n")

            # FFmpeg ile birleştir
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_list_path,
                '-c', 'copy',
                output_path
            ]

            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

            if result.returncode != 0:
                # copy ile olmazsa re-encode et
                ffmpeg_cmd = [
                    'ffmpeg', '-y',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', concat_list_path,
                    '-c:a', 'pcm_s16le',
                    '-ar', '24000',
                    output_path
                ]
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"FFmpeg hatası: {result.stderr[-200:]}")

            # Concat listesini temizle
            os.remove(concat_list_path)

        # Süreyi al
        duration = None
        try:
            probe_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', output_path]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            probe_data = json.loads(probe_result.stdout)
            duration = float(probe_data['format']['duration'])
        except:
            pass

        print(f"✅ Ses birleştirme tamamlandı: {output_path}")
        if duration:
            print(f"⏱️ Toplam süre: {duration:.2f}s")

        # Chunk dosyalarını temizle
        for path in request.audio_paths:
            if "chunk" in path and os.path.exists(path):
                os.remove(path)

        return {
            "success": True,
            "local_path": output_path,
            "duration": duration
        }

    except Exception as e:
        print(f"❌ Ses birleştirme hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/health")
async def health_check():
    """API sağlık kontrolü"""
    return {"status": "ok", "service": "video-generator"}

