"""
Video İşleme Servisi
Mevcut Python scriptlerini kullanarak video üretimi
"""
import os
import sys
import tempfile
import requests
from urllib.parse import urlparse

# API dizini
API_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Ana yt-video dizini (mevcut scriptler burada)
ROOT_DIR = os.path.dirname(API_DIR)
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, API_DIR)

from image_to_video import create_ken_burns_video
from add_subtitles import add_timed_subtitles
from services.cdn_service import upload_video
from utils.timing import start_timer, end_timer, Timer


def download_image(image_url: str, dest_path: str) -> str:
    """
    URL'den resmi indir
    
    Args:
        image_url: Kaynak URL
        dest_path: Hedef dosya yolu
        
    Returns:
        İndirilen dosya yolu
    """
    print(f"⬇️ Resim indiriliyor: {image_url}")
    
    response = requests.get(image_url, stream=True, timeout=30)
    response.raise_for_status()
    
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"✅ Resim indirildi: {dest_path}")
    return dest_path


def process_video(
    image_url: str,
    scene_id: str,
    duration: int = 10,
    pan_direction: str = "horizontal",
    subtitles: list = None
) -> dict:
    """
    Resimden video oluştur ve CDN'e yükle
    
    Args:
        image_url: Kaynak resim URL'i
        scene_id: Sahne ID
        duration: Video süresi (saniye)
        pan_direction: Pan yönü ("horizontal" veya "vertical")
        subtitles: Altyazı listesi (opsiyonel)
        
    Returns:
        {
            "success": True,
            "video_url": "https://cdn.../video.mp4",
            "scene_id": "..."
        }
    """
    print(f"\n🎬 ========== VIDEO İŞLEME BAŞLADI ==========")
    print(f"📷 Resim URL: {image_url}")
    print(f"🎯 Scene ID: {scene_id}")
    print(f"⏱️ Süre: {duration}s")
    print(f"➡️ Yön: {pan_direction}")
    print(f"================================================\n")
    
    # Geçici klasör oluştur
    temp_dir = tempfile.mkdtemp(prefix="video_")
    
    try:
        # 1. Resmi indir
        image_ext = os.path.splitext(urlparse(image_url).path)[1] or ".jpg"
        image_path = os.path.join(temp_dir, f"input{image_ext}")
        with Timer("PY_IMAGE_DOWNLOAD", {"scene_id": scene_id}):
            download_image(image_url, image_path)
        
        # 2. Video oluştur
        video_path = os.path.join(temp_dir, "output.mp4")
        
        # Pan yönünü dönüştür
        if pan_direction == "horizontal":
            pan_dir = "left_to_right"
        elif pan_direction == "vertical":
            pan_dir = "bottom_to_top"  # Aşağıdan yukarıya
        elif pan_direction == "vertical_reverse":
            pan_dir = "top_to_bottom"  # Yukarıdan aşağıya
        else:
            pan_dir = pan_direction
        
        with Timer("PY_KEN_BURNS_VIDEO", {"scene_id": scene_id, "duration": duration}):
            create_ken_burns_video(
                image_path=image_path,
                output_path=video_path,
                duration=duration,
                visibility_ratio=0.90,
                pan_direction=pan_dir
            )
        
        # 3. Altyazı ekle (opsiyonel)
        if subtitles and len(subtitles) > 0:
            print(f"\n📝 Altyazılar ekleniyor...")
            subtitled_path = os.path.join(temp_dir, "output_subtitled.mp4")
            with Timer("PY_ADD_SUBTITLES", {"scene_id": scene_id}):
                add_timed_subtitles(video_path, subtitles, subtitled_path)
            video_path = subtitled_path
        
        # 4. CDN'e yükle
        print(f"\n☁️ CDN'e yükleniyor...")
        with Timer("PY_CDN_VIDEO_UPLOAD", {"scene_id": scene_id}):
            cdn_url = upload_video(video_path, scene_id)
        
        print(f"\n🎉 ========== VIDEO TAMAMLANDI ==========")
        print(f"🔗 CDN URL: {cdn_url}")
        print(f"==========================================\n")
        
        return {
            "success": True,
            "video_url": cdn_url,
            "scene_id": scene_id,
            "duration": duration
        }
        
    except Exception as e:
        print(f"\n❌ VIDEO İŞLEME HATASI: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "scene_id": scene_id
        }
        
    finally:
        # Geçici dosyaları temizle
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"🧹 Geçici dosyalar temizlendi")


def download_file(url: str, dest_path: str) -> str:
    """URL'den dosya indir"""
    print(f"⬇️ İndiriliyor: {url[:60]}...")
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"✅ İndirildi: {dest_path}")
    return dest_path


def merge_video_with_audio(
    video_url: str,
    audio_url: str,
    scene_id: str,
    narration: str = None
) -> dict:
    """
    Sessiz video ile sesi birleştir, altyazı ekle ve CDN'e yükle
    
    Args:
        video_url: Sessiz video URL'i
        audio_url: Ses URL'i
        scene_id: Sahne ID
        narration: Altyazı metni (opsiyonel)
        
    Returns:
        {
            "success": True,
            "merged_video_url": "https://cdn.../merged_video.mp4",
            "duration": 10.5
        }
    """
    from moviepy import VideoFileClip, AudioFileClip
    from services.subtitle_service import add_karaoke_subtitles
    
    print(f"\n🔗 ========== VIDEO + SES BİRLEŞTİRME ==========")
    print(f"🎬 Video URL: {video_url}")
    print(f"🔊 Audio URL: {audio_url}")
    print(f"🎯 Scene ID: {scene_id}")
    print(f"📝 Altyazı: {'Var' if narration else 'Yok'}")
    print(f"=================================================\n")
    
    temp_dir = tempfile.mkdtemp(prefix="merge_")
    
    try:
        # 1. Video indir
        video_path = os.path.join(temp_dir, "video.mp4")
        with Timer("PY_MERGE_VIDEO_DOWNLOAD", {"scene_id": scene_id}):
            download_file(video_url, video_path)
        
        # 2. Ses indir
        audio_path = os.path.join(temp_dir, "audio.mp3")
        with Timer("PY_MERGE_AUDIO_DOWNLOAD", {"scene_id": scene_id}):
            download_file(audio_url, audio_path)
        
        # 3. Video ve sesi yükle
        print(f"🎬 Video yükleniyor...")
        video = VideoFileClip(video_path)
        
        print(f"🔊 Ses yükleniyor...")
        audio = AudioFileClip(audio_path)
        
        audio_duration = audio.duration
        print(f"   Video süresi: {video.duration:.2f}s")
        print(f"   Ses süresi: {audio_duration:.2f}s")
        
        # 4. Sesi videoya ekle
        print(f"🔗 Birleştiriliyor...")
        
        final_video = video.with_audio(audio)
        
        # 5. Kaydet (altyazısız versiyon)
        merged_path = os.path.join(temp_dir, "merged.mp4")
        print(f"💾 Kaydediliyor: {merged_path}")
        
        with Timer("PY_MOVIEPY_WRITE_VIDEO", {"scene_id": scene_id}):
            final_video.write_videofile(
                merged_path,
                codec='libx264',
                audio_codec='aac',
                fps=video.fps,
                logger='bar'
            )
        
        # Kaynakları kapat
        video.close()
        audio.close()
        final_video.close()
        
        # 6. Altyazı ekle (narration varsa)
        output_path = merged_path
        if narration and len(narration.strip()) > 0:
            print(f"\n📝 Altyazı ekleniyor...")
            subtitled_path = os.path.join(temp_dir, "merged_subtitled.mp4")
            with Timer("PY_KARAOKE_SUBTITLES", {"scene_id": scene_id}):
                output_path = add_karaoke_subtitles(
                    video_path=merged_path,
                    text=narration,
                    duration=audio_duration,
                    output_path=subtitled_path,
                    font_size=45,
                    max_words_per_line=5
                )
        
        # 7. CDN'e yükle
        print(f"\n☁️ CDN'e yükleniyor...")
        import time
        timestamp = int(time.time())
        with Timer("PY_CDN_MERGED_UPLOAD", {"scene_id": scene_id}):
            cdn_url = upload_video(output_path, f"merged_{scene_id}")
        
        print(f"\n🎉 ========== BİRLEŞTİRME TAMAMLANDI ==========")
        print(f"🔗 CDN URL: {cdn_url}")
        print(f"===============================================\n")
        
        return {
            "success": True,
            "merged_video_url": cdn_url,
            "scene_id": scene_id,
            "duration": audio_duration
        }
        
    except Exception as e:
        print(f"\n❌ BİRLEŞTİRME HATASI: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "scene_id": scene_id
        }
        
    finally:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"🧹 Geçici dosyalar temizlendi")


def concatenate_videos(video_urls: list, project_id: str) -> dict:
    """
    Birden fazla video URL'sini sırayla birleştirip tek video yapar.
    FFmpeg concat demuxer kullanır.
    
    Args:
        video_urls: Sıralı video URL listesi
        project_id: Proje ID
        
    Returns:
        {
            "success": True,
            "video_url": "https://cdn.../final_video.mp4",
            "project_id": "..."
        }
    """
    import shutil
    
    # imageio-ffmpeg kullanarak FFmpeg yolunu bul
    try:
        import imageio_ffmpeg
        ffmpeg_binary = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ffmpeg_binary = 'ffmpeg'
    
    print(f"\n🎬 ========== VİDEO BİRLEŞTİRME (CONCAT) ==========")
    print(f"📦 Video Sayısı: {len(video_urls)}")
    print(f"🎯 Proje ID: {project_id}")
    print(f"===================================================\n")
    
    if not video_urls or len(video_urls) == 0:
        return {
            "success": False,
            "error": "Video URL listesi boş",
            "project_id": project_id
        }
    
    # Tek video varsa direkt döndür
    if len(video_urls) == 1:
        print("⚠️ Sadece 1 video var, birleştirme gerekmiyor.")
        return {
            "success": True,
            "video_url": video_urls[0],
            "project_id": project_id
        }
    
    # Geçici dizin oluştur
    temp_dir = tempfile.mkdtemp(prefix="concat_")
    
    try:
        # 1. Tüm videoları indir
        downloaded_files = []
        with Timer("PY_CONCAT_DOWNLOAD_ALL", {"project_id": project_id, "count": len(video_urls)}):
            for i, url in enumerate(video_urls):
                print(f"⬇️ İndiriliyor ({i+1}/{len(video_urls)}): {url[:60]}...")
                local_path = os.path.join(temp_dir, f"video_{i:03d}.mp4")
                download_file(url, local_path)
                downloaded_files.append(local_path)
                print(f"✅ İndirildi: {local_path}")
        
        # 2. MoviePy ile birleştir (FFmpeg concat demuxer ses kayması yapıyordu)
        from moviepy import VideoFileClip, concatenate_videoclips
        
        print("🎬 MoviePy ile videolar yükleniyor...")
        clips = []
        for video_path in downloaded_files:
            clip = VideoFileClip(video_path)
            clips.append(clip)
            print(f"   ✅ Yüklendi: {os.path.basename(video_path)} ({clip.duration:.2f}s)")
        
        print("🔗 Videolar birleştiriliyor...")
        final_clip = concatenate_videoclips(clips, method="compose")
        
        output_path = os.path.join(temp_dir, "final_video.mp4")
        print(f"💾 Kaydediliyor: {output_path}")
        with Timer("PY_MOVIEPY_CONCAT_WRITE", {"project_id": project_id, "count": len(video_urls)}):
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                preset='fast',
                threads=4,
                logger='bar'
            )
        
        # Clipleri kapat
        for clip in clips:
            clip.close()
        final_clip.close()
        
        print(f"✅ Birleştirme tamamlandı: {output_path}")
        
        # 4. CDN'e yükle
        print("\n☁️ CDN'e yükleniyor...")
        with Timer("PY_CDN_FINAL_UPLOAD", {"project_id": project_id}):
            cdn_url = upload_video(output_path, f"final_{project_id}")
        
        print(f"\n🎉 ========== CONCAT TAMAMLANDI ==========")
        print(f"🔗 CDN URL: {cdn_url}")
        print(f"==========================================\n")
        
        return {
            "success": True,
            "video_url": cdn_url,
            "project_id": project_id
        }
        
    except Exception as e:
        print(f"\n❌ CONCAT HATASI: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "project_id": project_id
        }
        
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"🧹 Geçici dosyalar temizlendi")
