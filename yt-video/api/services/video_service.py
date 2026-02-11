"""
Video İşleme Servisi
Mevcut Python scriptlerini kullanarak video üretimi
"""
import os
import sys
import tempfile
import shutil
import requests
from urllib.parse import urlparse

# Proje dosyaları için paylaşımlı dizin (FLUX API ile ortak)
PROJECTS_DIR = "/tmp/projects"

def get_project_dir(project_id: str) -> str:
    """Proje için paylaşımlı dizin oluştur/döndür"""
    if not project_id:
        return tempfile.mkdtemp(prefix="video_")
    d = os.path.join(PROJECTS_DIR, str(project_id))
    os.makedirs(d, exist_ok=True)
    return d

def is_local_path(path: str) -> bool:
    """URL mi yoksa lokal dosya yolu mu kontrol et"""
    return path and (path.startswith("/") or path.startswith("./"))

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
    scene_number: int = None,
    skip_cdn: bool = False
) -> dict:
    """
    Resimden video oluştur. skip_cdn=True ise lokal path döndür.
    """
    print(f"\n🎬 ========== VIDEO İŞLEME BAŞLADI ==========")
    print(f"📷 Resim: {image_url}")
    print(f"🎯 Scene ID: {scene_id}")
    print(f"⏱️ Süre: {duration}s")
    print(f"➡️ Yön: {pan_direction}")
    print(f"💾 CDN: {'Hayır (lokal)' if skip_cdn else 'Evet'}")
    if project_id: print(f"📁 Proje ID: {project_id}")
    if scene_number: print(f"🎬 Sahne No: {scene_number}")
    print(f"================================================\n")
    
    # Proje dizini veya geçici dizin
    project_dir = get_project_dir(project_id)
    use_temp = not project_id
    
    try:
        meta = {"scene_id": scene_id, "project_id": project_id, "scene_number": scene_number}

        # 1. Resim - lokal path mi URL mi?
        if is_local_path(image_url):
            image_path = image_url
            print(f"📂 Lokal resim kullanılıyor: {image_path}")
        else:
            image_ext = os.path.splitext(urlparse(image_url).path)[1] or ".jpg"
            image_path = os.path.join(project_dir, f"input_scene_{scene_number or 0}{image_ext}")
            with Timer("PY_IMAGE_DOWNLOAD", meta):
                download_image(image_url, image_path)
        
        # 2. Video oluştur
        scene_tag = f"scene_{str(scene_number).zfill(3)}" if scene_number else scene_id
        video_path = os.path.join(project_dir, f"video_{scene_tag}.mp4")
        
        if pan_direction == "horizontal":
            pan_dir = "left_to_right"
        elif pan_direction == "vertical":
            pan_dir = "bottom_to_top"
        elif pan_direction == "vertical_reverse":
            pan_dir = "top_to_bottom"
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
            subtitled_path = os.path.join(project_dir, f"video_{scene_tag}_sub.mp4")
            with Timer("PY_ADD_SUBTITLES", meta):
                add_timed_subtitles(video_path, subtitles, subtitled_path)
            video_path = subtitled_path
        
        # 4. CDN'e yükle veya lokal path döndür
        if skip_cdn:
            print(f"\n✅ Video lokal: {video_path}")
            return {
                "success": True,
                "video_url": video_path,
                "local_path": video_path,
                "scene_id": scene_id,
                "duration": duration
            }
        else:
            print(f"\n☁️ CDN'e yükleniyor...")
            with Timer("PY_CDN_VIDEO_UPLOAD", meta):
                cdn_url = upload_video(video_path, scene_id)
            print(f"🔗 CDN URL: {cdn_url}")
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
        if use_temp and os.path.exists(project_dir):
            shutil.rmtree(project_dir)
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
    scene_number: int = None,
    skip_cdn: bool = False
) -> dict:
    """
    Sessiz video ile sesi birleştir, altyazı ekle.
    skip_cdn=True ise lokal path döndür.
    Lokal path gönderilirse indirme atlanır.
    """
    import subprocess
    import json
    from services.subtitle_service import add_karaoke_subtitles
    
    print(f"\n🔗 ========== VIDEO + SES BİRLEŞTİRME (FFmpeg) ==========")
    print(f"🎬 Video: {video_url}")
    print(f"🔊 Audio: {audio_url}")
    print(f"🎯 Scene ID: {scene_id}")
    print(f"📝 Altyazı: {'Var' if narration else 'Yok'}")
    print(f"💾 CDN: {'Hayır (lokal)' if skip_cdn else 'Evet'}")
    if project_id: print(f"📁 Proje ID: {project_id}")
    if scene_number: print(f"🎬 Sahne No: {scene_number}")
    print(f"=========================================================\n")
    
    project_dir = get_project_dir(project_id)
    use_temp = not project_id
    
    try:
        meta = {"scene_id": scene_id, "project_id": project_id, "scene_number": scene_number}

        # 1. Video - lokal path mi URL mi?
        if is_local_path(video_url):
            video_path = video_url
            print(f"📂 Lokal video: {video_path}")
        else:
            video_path = os.path.join(project_dir, f"video_dl_{scene_number or 0}.mp4")
            with Timer("PY_MERGE_VIDEO_DOWNLOAD", meta):
                download_file(video_url, video_path)
        
        # 2. Audio - lokal path mi URL mi?
        if is_local_path(audio_url):
            audio_path = audio_url
            print(f"📂 Lokal audio: {audio_path}")
        else:
            audio_path = os.path.join(project_dir, f"audio_dl_{scene_number or 0}.mp3")
            with Timer("PY_MERGE_AUDIO_DOWNLOAD", meta):
                download_file(audio_url, audio_path)
        
        # 3. FFprobe ile süreleri al
        probe_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', audio_path]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        probe_data = json.loads(probe_result.stdout)
        audio_duration = float(probe_data['format']['duration'])
        
        probe_cmd_video = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', video_path]
        probe_result_video = subprocess.run(probe_cmd_video, capture_output=True, text=True)
        probe_data_video = json.loads(probe_result_video.stdout)
        video_duration = float(probe_data_video['format']['duration'])
        
        print(f"   Video süresi: {video_duration:.2f}s")
        print(f"   Ses süresi: {audio_duration:.2f}s")
        
        # 4. FFmpeg ile birleştir (GPU NVENC)
        scene_tag = f"scene_{str(scene_number).zfill(3)}" if scene_number else scene_id
        merged_path = os.path.join(project_dir, f"merged_{scene_tag}.mp4")
        print(f"🔗 FFmpeg ile birleştiriliyor (GPU NVENC)...")
        
        with Timer("PY_FFMPEG_MERGE", meta):
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'h264_nvenc',
                '-preset', 'fast',
                '-b:v', '5M',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                merged_path
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"⚠️ FFmpeg stderr: {result.stderr[-500:]}")
                raise Exception(f"FFmpeg hatası: {result.stderr[-200:]}")
        
        # 5. Altyazı ekle (narration varsa)
        output_path = merged_path
        if narration and len(narration.strip()) > 0:
            print(f"\n📝 Altyazı ekleniyor...")
            subtitled_path = os.path.join(project_dir, f"merged_{scene_tag}_sub.mp4")
            with Timer("PY_KARAOKE_SUBTITLES", meta):
                output_path = add_karaoke_subtitles(
                    video_path=merged_path,
                    text=narration,
                    duration=audio_duration,
                    output_path=subtitled_path,
                    font_size=45,
                    max_words_per_line=5
                )
        
        # 6. CDN'e yükle veya lokal path döndür
        if skip_cdn:
            print(f"\n✅ Birleştirme lokal: {output_path}")
            return {
                "success": True,
                "merged_video_url": output_path,
                "local_path": output_path,
                "scene_id": scene_id,
                "duration": audio_duration
            }
        else:
            print(f"\n☁️ CDN'e yükleniyor...")
            import time
            with Timer("PY_CDN_MERGED_UPLOAD", meta):
                cdn_url = upload_video(output_path, f"merged_{scene_id}")
            print(f"🔗 CDN URL: {cdn_url}")
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
        if use_temp and os.path.exists(project_dir):
            shutil.rmtree(project_dir)
            print(f"🧹 Geçici dosyalar temizlendi")


def concatenate_videos(video_urls: list, project_id: str) -> dict:
    """
    Birden fazla videoyu birleştirip tek video yapar ve CDN'e yükler.
    Lokal path'ler gönderilirse indirme atlanır.
    Final video HER ZAMAN CDN'e yüklenir.
    """
    import subprocess
    
    print(f"\n🎬 ========== VİDEO BİRLEŞTİRME (FFmpeg NVENC) ==========")
    print(f"📦 Video Sayısı: {len(video_urls)}")
    print(f"🎯 Proje ID: {project_id}")
    print(f"========================================================\n")
    
    if not video_urls or len(video_urls) == 0:
        return {
            "success": False,
            "error": "Video URL listesi boş",
            "project_id": project_id
        }
    
    # Tek video varsa direkt CDN'e yükle
    if len(video_urls) == 1:
        single = video_urls[0]
        if is_local_path(single):
            cdn_url = upload_video(single, f"final_{project_id}")
            return {"success": True, "video_url": cdn_url, "project_id": project_id}
        return {"success": True, "video_url": single, "project_id": project_id}
    
    project_dir = get_project_dir(project_id)
    
    try:
        # 1. Videoları hazırla (lokal path varsa indirme yok)
        local_files = []
        with Timer("PY_CONCAT_PREPARE", {"project_id": project_id, "count": len(video_urls)}):
            for i, url in enumerate(video_urls):
                if is_local_path(url):
                    local_files.append(url)
                    print(f"📂 Lokal ({i+1}/{len(video_urls)}): {url}")
                else:
                    local_path = os.path.join(project_dir, f"concat_{i:03d}.mp4")
                    print(f"⬇️ İndiriliyor ({i+1}/{len(video_urls)}): {url[:60]}...")
                    download_file(url, local_path)
                    local_files.append(local_path)
        
        # 2. FFmpeg concat listesi
        concat_list_path = os.path.join(project_dir, "concat_list.txt")
        with open(concat_list_path, 'w') as f:
            for vp in local_files:
                f.write(f"file '{vp}'\n")
        
        print(f"📝 Concat listesi: {len(local_files)} video")
        
        # 3. FFmpeg ile birleştir (GPU NVENC)
        output_path = os.path.join(project_dir, "final_video.mp4")
        print(f"🔗 FFmpeg ile birleştiriliyor (GPU NVENC)...")
        
        with Timer("PY_FFMPEG_CONCAT", {"project_id": project_id, "count": len(video_urls)}):
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_list_path,
                '-c:v', 'h264_nvenc',
                '-preset', 'fast',
                '-b:v', '5M',
                '-maxrate', '8M',
                '-bufsize', '10M',
                '-c:a', 'aac',
                '-b:a', '128k',
                output_path
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"⚠️ FFmpeg stderr: {result.stderr[-500:]}")
                raise Exception(f"FFmpeg hatası: {result.stderr[-200:]}")
        
        print(f"✅ Birleştirme tamamlandı: {output_path}")
        
        # 4. Final video CDN'e yükle (her zaman)
        print("\n☁️ Final video CDN'e yükleniyor...")
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
        # Proje dizinini temizle (tüm ara dosyalar)
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
            print(f"🧹 Proje dosyaları temizlendi: {project_dir}")



def gpu_test_loop_videos(
    video_urls: list,
    target_duration_seconds: int = 900,
    test_name: str = "gpu_test"
) -> dict:
    """
    🧪 GPU Test: FFmpeg ile direkt video birleştirme (NVENC GPU encoding)
    MoviePy yerine FFmpeg kullanarak çok daha hızlı!
    """
    import subprocess
    import shutil
    import time
    import json
    
    print(f"\n🧪 ========== GPU TEST BAŞLADI (FFmpeg Direct) ==========")
    print(f"📦 Video URL Sayısı: {len(video_urls)}")
    print(f"⏱️ Hedef Süre: {target_duration_seconds} saniye ({target_duration_seconds/60:.1f} dakika)")
    print(f"📝 Test Adı: {test_name}")
    print(f"=========================================================\n")
    
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
        # 1. Videoları indir
        print("📥 Videolar indiriliyor...")
        download_start = time.time()
        
        downloaded_files = []
        video_durations = []
        
        for i, url in enumerate(video_urls):
            local_path = os.path.join(temp_dir, f"source_{i:03d}.mp4")
            print(f"   ⬇️ ({i+1}/{len(video_urls)}) {url[:60]}...")
            download_file(url, local_path)
            downloaded_files.append(local_path)
            
            # FFprobe ile süre al
            probe_cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', local_path
            ]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            probe_data = json.loads(probe_result.stdout)
            duration = float(probe_data['format']['duration'])
            video_durations.append(duration)
            print(f"      ✅ Süre: {duration:.2f}s")
        
        download_end = time.time()
        metrics["download_time_ms"] = int((download_end - download_start) * 1000)
        
        total_source_duration = sum(video_durations)
        print(f"\n📊 Kaynak videoların toplam süresi: {total_source_duration:.2f}s")
        
        # 2. Concat listesi oluştur (hedef süreye kadar döngüsel)
        print("\n🎬 FFmpeg concat listesi hazırlanıyor...")
        concat_list_path = os.path.join(temp_dir, "concat_list.txt")
        
        current_duration = 0
        video_count = 0
        
        with open(concat_list_path, 'w') as f:
            while current_duration < target_duration_seconds:
                for i, (path, duration) in enumerate(zip(downloaded_files, video_durations)):
                    if current_duration >= target_duration_seconds:
                        break
                    
                    remaining = target_duration_seconds - current_duration
                    
                    if duration <= remaining:
                        # Tam video ekle
                        f.write(f"file '{path}'\n")
                        current_duration += duration
                        video_count += 1
                        print(f"   ➕ Video {video_count}: {duration:.2f}s (toplam: {current_duration:.2f}s)")
                    else:
                        # Son video - kırpılacak (FFmpeg ile)
                        trimmed_path = os.path.join(temp_dir, f"trimmed_{video_count}.mp4")
                        trim_cmd = [
                            'ffmpeg', '-y', '-i', path,
                            '-t', str(remaining),
                            '-c', 'copy',  # Stream copy - çok hızlı!
                            trimmed_path
                        ]
                        subprocess.run(trim_cmd, capture_output=True)
                        f.write(f"file '{trimmed_path}'\n")
                        current_duration += remaining
                        video_count += 1
                        print(f"   ✂️ Video {video_count}: {remaining:.2f}s (kesildi, toplam: {current_duration:.2f}s)")
                        break
        
        metrics["video_count"] = video_count
        metrics["total_duration"] = current_duration
        
        print(f"\n📦 Toplam video sayısı: {video_count}")
        print(f"⏱️ Toplam süre: {current_duration:.2f}s ({current_duration/60:.1f} dakika)")
        
        # 3. FFmpeg ile birleştir + NVENC encode
        print("\n🔗 FFmpeg ile birleştiriliyor (GPU NVENC)...")
        output_path = os.path.join(temp_dir, f"{test_name}_output.mp4")
        
        encode_start = time.time()
        
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_list_path,
            '-c:v', 'h264_nvenc',      # GPU encoding
            '-preset', 'fast',
            '-b:v', '5M',
            '-maxrate', '8M',
            '-bufsize', '10M',
            '-c:a', 'aac',
            '-b:a', '128k',
            output_path
        ]
        
        print(f"💾 Encode komutu: {' '.join(ffmpeg_cmd[:10])}...")
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"⚠️ FFmpeg stderr: {result.stderr[-500:]}")
            raise Exception(f"FFmpeg hatası: {result.stderr[-200:]}")
        
        encode_end = time.time()
        metrics["encode_time_ms"] = int((encode_end - encode_start) * 1000)
        
        print(f"\n✅ Encoding tamamlandı!")
        print(f"   ⏱️ Encoding süresi: {metrics['encode_time_ms']/1000:.2f}s")
        
        # 4. CDN'e yükle
        print("\n☁️ CDN'e yükleniyor...")
        upload_start = time.time()
        
        cdn_url = upload_video(output_path, f"gpu_test_{test_name}")
        
        upload_end = time.time()
        metrics["upload_time_ms"] = int((upload_end - upload_start) * 1000)
        
        # Performans özeti
        total_time_ms = metrics["download_time_ms"] + metrics["encode_time_ms"] + metrics["upload_time_ms"]
        encoding_speed = metrics["total_duration"] / (metrics["encode_time_ms"] / 1000) if metrics["encode_time_ms"] > 0 else 0
        
        print(f"\n🎉 ========== GPU TEST TAMAMLANDI ==========")
        print(f"🔗 CDN URL: {cdn_url}")
        print(f"\n📊 PERFORMANS METRİKLERİ:")
        print(f"   ⬇️ İndirme: {metrics['download_time_ms']/1000:.2f}s")
        print(f"   🎬 Encoding: {metrics['encode_time_ms']/1000:.2f}s")
        print(f"   ⬆️ Yükleme: {metrics['upload_time_ms']/1000:.2f}s")
        print(f"   ⏱️ TOPLAM: {total_time_ms/1000:.2f}s")
        print(f"\n   📦 Video sayısı: {metrics['video_count']}")
        print(f"   ⏱️ Video süresi: {metrics['total_duration']:.2f}s")
        print(f"   📈 Encoding hızı: {encoding_speed:.2f}x realtime")
        print(f"==============================================\n")
        
        return {
            "success": True,
            "video_url": cdn_url,
            "test_name": test_name,
            "metrics": metrics
        }
        
    except Exception as e:
        print(f"\n❌ HATA: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "test_name": test_name,
            "metrics": metrics
        }
        
    finally:
        # Temizlik
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"🧹 Geçici dosyalar temizlendi: {temp_dir}")