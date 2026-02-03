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
    subtitles: list = None,
    project_id: str = None,
    scene_number: int = None
) -> dict:
    """
    Resimden video oluştur ve CDN'e yükle
    """
    print(f"\n🎬 ========== VIDEO İŞLEME BAŞLADI ==========")
    print(f"📷 Resim URL: {image_url}")
    print(f"🎯 Scene ID: {scene_id}")
    print(f"⏱️ Süre: {duration}s")
    print(f"➡️ Yön: {pan_direction}")
    if project_id: print(f"📁 Proje ID: {project_id}")
    if scene_number: print(f"🎬 Sahne No: {scene_number}")
    print(f"================================================\n")
    
    # Geçici klasör oluştur
    temp_dir = tempfile.mkdtemp(prefix="video_")
    
    try:
        # Metada for logging
        meta = {"scene_id": scene_id, "project_id": project_id, "scene_number": scene_number}

        # 1. Resmi indir
        image_ext = os.path.splitext(urlparse(image_url).path)[1] or ".jpg"
        image_path = os.path.join(temp_dir, f"input{image_ext}")
        with Timer("PY_IMAGE_DOWNLOAD", meta):
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
        
        with Timer("PY_KEN_BURNS_VIDEO", {**meta, "duration": duration}):
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
            with Timer("PY_ADD_SUBTITLES", meta):
                add_timed_subtitles(video_path, subtitles, subtitled_path)
            video_path = subtitled_path
        
        # 4. CDN'e yükle
        print(f"\n☁️ CDN'e yükleniyor...")
        with Timer("PY_CDN_VIDEO_UPLOAD", meta):
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
    narration: str = None,
    project_id: str = None,
    scene_number: int = None
) -> dict:
    """
    Sessiz video ile sesi birleştir, altyazı ekle ve CDN'e yükle
    """
    from moviepy import VideoFileClip, AudioFileClip
    from services.subtitle_service import add_karaoke_subtitles
    
    print(f"\n🔗 ========== VIDEO + SES BİRLEŞTİRME ==========")
    print(f"🎬 Video URL: {video_url}")
    print(f"🔊 Audio URL: {audio_url}")
    print(f"🎯 Scene ID: {scene_id}")
    print(f"📝 Altyazı: {'Var' if narration else 'Yok'}")
    if project_id: print(f"📁 Proje ID: {project_id}")
    if scene_number: print(f"🎬 Sahne No: {scene_number}")
    print(f"=================================================\n")
    
    temp_dir = tempfile.mkdtemp(prefix="merge_")
    
    try:
        # Metada for logging
        meta = {"scene_id": scene_id, "project_id": project_id, "scene_number": scene_number}

        # 1. Video indir
        video_path = os.path.join(temp_dir, "video.mp4")
        with Timer("PY_MERGE_VIDEO_DOWNLOAD", meta):
            download_file(video_url, video_path)
        
        # 2. Ses indir
        audio_path = os.path.join(temp_dir, "audio.mp3")
        with Timer("PY_MERGE_AUDIO_DOWNLOAD", meta):
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
        
        with Timer("PY_MOVIEPY_WRITE_VIDEO", meta):
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
            with Timer("PY_KARAOKE_SUBTITLES", meta):
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
        with Timer("PY_CDN_MERGED_UPLOAD", meta):
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


def gpu_test_loop_videos(
    video_urls: list,
    target_duration_seconds: int = 900,
    test_name: str = "gpu_test"
) -> dict:
    """
    🧪 GPU Test: Hazır videoları hedef süreye kadar döngüsel birleştir
    
    Resim oluşturma, altyazı ekleme gibi adımları atlar.
    Sadece video birleştirme ve GPU encoding performansını test eder.
    
    Args:
        video_urls: Hazır video URL'leri (CDN'den)
        target_duration_seconds: Hedef video süresi (saniye)
        test_name: Test adı (CDN dosya adı için)
        
    Returns:
        {
            "success": True,
            "video_url": "https://cdn.../test_video.mp4",
            "metrics": {
                "total_duration": 900,
                "video_count": 30,
                "download_time_ms": 1234,
                "encode_time_ms": 56789,
                "upload_time_ms": 2345
            }
        }
    """
    from moviepy import VideoFileClip, concatenate_videoclips
    import shutil
    import time
    
    print(f"\n🧪 ========== GPU TEST BAŞLADI ==========")
    print(f"📦 Video URL Sayısı: {len(video_urls)}")
    print(f"⏱️ Hedef Süre: {target_duration_seconds} saniye ({target_duration_seconds/60:.1f} dakika)")
    print(f"📝 Test Adı: {test_name}")
    print(f"=============================================\n")
    
    if not video_urls or len(video_urls) == 0:
        return {
            "success": False,
            "error": "Video URL listesi boş",
            "test_name": test_name
        }
    
    temp_dir = tempfile.mkdtemp(prefix="gpu_test_")
    metrics = {
        "download_time_ms": 0,
        "encode_time_ms": 0,
        "upload_time_ms": 0,
        "total_duration": 0,
        "video_count": 0,
        "input_videos": len(video_urls)
    }
    
    try:
        # 1. Videoları indir ve süreleri hesapla
        print("📥 Videolar indiriliyor...")
        download_start = time.time()
        
        downloaded_clips = []
        total_source_duration = 0
        
        for i, url in enumerate(video_urls):
            local_path = os.path.join(temp_dir, f"source_{i:03d}.mp4")
            print(f"   ⬇️ ({i+1}/{len(video_urls)}) {url[:60]}...")
            download_file(url, local_path)
            
            # VideoFileClip ile süre hesapla
            clip = VideoFileClip(local_path)
            total_source_duration += clip.duration
            downloaded_clips.append({"path": local_path, "clip": clip, "duration": clip.duration})
            print(f"      ✅ Süre: {clip.duration:.2f}s")
        
        download_end = time.time()
        metrics["download_time_ms"] = int((download_end - download_start) * 1000)
        
        print(f"\n📊 Kaynak videoların toplam süresi: {total_source_duration:.2f}s")
        
        # 2. Hedef süreye ulaşmak için kaç tekrar gerekli hesapla
        repeat_count = int(target_duration_seconds / total_source_duration) + 1
        print(f"🔄 Tekrar sayısı: {repeat_count} (hedef: {target_duration_seconds}s)")
        
        # 3. Döngüsel clip listesi oluştur
        print("\n🎬 Video klipleri hazırlanıyor...")
        all_clips = []
        current_duration = 0
        video_index = 0
        
        while current_duration < target_duration_seconds:
            clip_info = downloaded_clips[video_index % len(downloaded_clips)]
            
            # Son klip için süreyi kes (gerekirse)
            remaining = target_duration_seconds - current_duration
            if clip_info["duration"] > remaining:
                # Son klibi kes
                trimmed_clip = clip_info["clip"].subclipped(0, remaining)
                all_clips.append(trimmed_clip)
                current_duration += remaining
                print(f"   ✂️ Klip {len(all_clips)}: {remaining:.2f}s (kesildi)")
            else:
                # Tüm klibi ekle (yeni instance)
                all_clips.append(clip_info["clip"])
                current_duration += clip_info["duration"]
                print(f"   ➕ Klip {len(all_clips)}: {clip_info['duration']:.2f}s (toplam: {current_duration:.2f}s)")
            
            video_index += 1
        
        metrics["video_count"] = len(all_clips)
        metrics["total_duration"] = current_duration
        
        print(f"\n📦 Toplam klip sayısı: {len(all_clips)}")
        print(f"⏱️ Toplam süre: {current_duration:.2f}s ({current_duration/60:.1f} dakika)")
        
        # 4. Birleştir ve encode et (GPU test!)
        print("\n🔗 Videolar birleştiriliyor (GPU ENCODING)...")
        encode_start = time.time()
        
        final_clip = concatenate_videoclips(all_clips, method="compose")
        
        output_path = os.path.join(temp_dir, f"{test_name}_output.mp4")
        print(f"💾 Encode ediliyor: {output_path}")
        
        final_clip.write_videofile(
            output_path,
            codec='h264_nvenc',  # NVIDIA GPU encoding (RTX 4090)
            audio_codec='aac',
            preset='p4',  # NVENC preset: p1-p7 (p4 = medium quality/speed)
            fps=30,
            logger='bar'
        )
        
        encode_end = time.time()
        metrics["encode_time_ms"] = int((encode_end - encode_start) * 1000)
        
        # Kaynak klipleri kapat
        for clip_info in downloaded_clips:
            clip_info["clip"].close()
        final_clip.close()
        
        print(f"\n✅ Encoding tamamlandı!")
        print(f"   ⏱️ Encoding süresi: {metrics['encode_time_ms']/1000:.2f}s")
        
        # 5. CDN'e yükle
        print("\n☁️ CDN'e yükleniyor...")
        upload_start = time.time()
        
        cdn_url = upload_video(output_path, f"gpu_test_{test_name}")
        
        upload_end = time.time()
        metrics["upload_time_ms"] = int((upload_end - upload_start) * 1000)
        
        # Performans özeti
        total_time_ms = metrics["download_time_ms"] + metrics["encode_time_ms"] + metrics["upload_time_ms"]
        
        print(f"\n🎉 ========== GPU TEST TAMAMLANDI ==========")
        print(f"🔗 CDN URL: {cdn_url}")
        print(f"\n📊 PERFORMANS METRİKLERİ:")
        print(f"   ⬇️ İndirme: {metrics['download_time_ms']/1000:.2f}s")
        print(f"   🎬 Encoding: {metrics['encode_time_ms']/1000:.2f}s")
        print(f"   ⬆️ Yükleme: {metrics['upload_time_ms']/1000:.2f}s")
        print(f"   ⏱️ TOPLAM: {total_time_ms/1000:.2f}s")
        print(f"\n   📦 Video sayısı: {metrics['video_count']}")
        print(f"   ⏱️ Video süresi: {metrics['total_duration']:.2f}s")
        print(f"   📈 Encoding hızı: {metrics['total_duration']/(metrics['encode_time_ms']/1000):.2f}x realtime")
        print(f"==============================================\n")
        
        return {
            "success": True,
            "video_url": cdn_url,
            "test_name": test_name,
            "metrics": metrics
        }
        
    except Exception as e:
        print(f"\n❌ GPU TEST HATASI: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "test_name": test_name,
            "metrics": metrics
        }
        
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"🧹 Geçici dosyalar temizlendi")
