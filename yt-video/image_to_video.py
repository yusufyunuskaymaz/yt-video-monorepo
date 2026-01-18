#!/usr/bin/env python3
"""
Resmi videoya dönüştür - Ken Burns efekti (zoom + pan)
Kullanım: python image_to_video.py resim.jpg
"""

import sys
import os
import numpy as np
from PIL import Image
from moviepy import VideoClip


def create_ken_burns_video(
    image_path: str,
    output_path: str = "output.mp4",
    duration: int = 10,
    fps: int = 30,
    visibility_ratio: float = 0.75,
    pan_direction: str = "left_to_right"
):
    """
    Resme pan efekti uygulayarak video oluşturur.
    Resmin belirli bir kısmı görünür ve gizli kısma doğru yavaşça kayar.
    
    Args:
        image_path: Kaynak resim dosyasının yolu
        output_path: Çıktı video dosyasının yolu
        duration: Video süresi (saniye)
        fps: Saniyedeki kare sayısı
        visibility_ratio: Resmin ne kadarının görüneceği (0.75 = %75)
        pan_direction: Pan yönü ("left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top")
    """
    
    # Resmi yükle
    print(f"📷 Resim yükleniyor: {image_path}")
    img = Image.open(image_path)
    
    # RGB'ye çevir (RGBA ise)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    img_array = np.array(img)
    original_height, original_width = img_array.shape[:2]
    
    print(f"   Boyut: {original_width}x{original_height}")
    
    # Çıktı video boyutu (1080p)
    output_width = 1920
    output_height = 1080
    
    def smooth_ease(t):
        """Lineer hareket - sabit hız, ivme yok"""
        return max(0, min(1, t))
    
    # Sabit crop boyutları (visibility_ratio'ya göre)
    # Yatay pan için genişlik küçültülür, dikey pan için yükseklik
    if pan_direction in ["left_to_right", "right_to_left"]:
        crop_width = original_width * visibility_ratio
        crop_height = original_height  # Tam yükseklik
        max_x_offset = original_width - crop_width
        max_y_offset = 0
    else:  # top_to_bottom, bottom_to_top
        crop_width = original_width  # Tam genişlik
        crop_height = original_height * visibility_ratio
        max_x_offset = 0
        max_y_offset = original_height - crop_height
    
    def make_frame(t):
        """Her kare için pan pozisyonu hesapla"""
        # Zaman ilerlemesi (0 -> 1)
        raw_progress = t / duration
        
        # Ultra smooth easing uygula
        progress = smooth_ease(raw_progress)
        
        # Pan pozisyonu hesapla
        if pan_direction == "left_to_right":
            x_offset = max_x_offset * progress
            y_offset = 0
        elif pan_direction == "right_to_left":
            x_offset = max_x_offset * (1 - progress)
            y_offset = 0
        elif pan_direction == "top_to_bottom":
            x_offset = 0
            y_offset = max_y_offset * progress
        elif pan_direction == "bottom_to_top":
            x_offset = 0
            y_offset = max_y_offset * (1 - progress)
        else:
            x_offset = max_x_offset / 2
            y_offset = max_y_offset / 2
        
        # Float koordinatlarla high-quality crop ve resize
        left = x_offset
        top = y_offset
        right = x_offset + crop_width
        bottom = y_offset + crop_height
        
        # Yüksek kaliteli crop ve resize
        cropped = img.crop((left, top, right, bottom))
        resized = cropped.resize((output_width, output_height), Image.Resampling.LANCZOS)
        
        return np.array(resized)
    
    # Video klip oluştur
    print(f"🎬 Video oluşturuluyor...")
    print(f"   Süre: {duration} saniye")
    print(f"   FPS: {fps}")
    print(f"   Görünürlük: %{int(visibility_ratio * 100)}")
    print(f"   Pan: {pan_direction}")
    
    clip = VideoClip(make_frame, duration=duration)
    clip = clip.with_fps(fps)
    
    # Video yaz
    print(f"💾 Video kaydediliyor: {output_path}")
    clip.write_videofile(
        output_path,
        fps=fps,
        codec='libx264',
        audio=False,
        preset='medium',
        threads=4,
        logger='bar'
    )
    
    print(f"✅ Video başarıyla oluşturuldu: {output_path}")
    return output_path


def get_next_filename(base_name: str, output_dir: str) -> str:
    """Sıradaki dosya adını bul (video_1.mp4, video_2.mp4, ...)"""
    counter = 1
    while True:
        filename = f"{base_name}_{counter}.mp4"
        filepath = os.path.join(output_dir, filename)
        if not os.path.exists(filepath):
            return filepath
        counter += 1


def main():
    # Komut satırı argümanları
    if len(sys.argv) < 2:
        print("Kullanım: python image_to_video.py <resim_yolu> [çıktı_adı] [süre] [yön]")
        print("Örnek: python image_to_video.py foto.jpg video 15 h")
        print("")
        print("Yön seçenekleri:")
        print("  h veya horizontal  → Soldan sağa")
        print("  v veya vertical    → Aşağıdan yukarıya")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Resim var mı kontrol et
    if not os.path.exists(image_path):
        print(f"❌ Hata: Resim bulunamadı: {image_path}")
        sys.exit(1)
    
    # Downloads klasörünü oluştur
    script_dir = os.path.dirname(os.path.abspath(__file__))
    downloads_dir = os.path.join(script_dir, "downloads")
    os.makedirs(downloads_dir, exist_ok=True)
    
    # Çıktı adı (uzantısız)
    base_name = sys.argv[2] if len(sys.argv) > 2 else "video"
    # .mp4 uzantısı varsa kaldır
    if base_name.endswith('.mp4'):
        base_name = base_name[:-4]
    
    # Sıradaki dosya adını bul
    output_path = get_next_filename(base_name, downloads_dir)
    
    # Süre
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    # Pan yönü
    direction_arg = sys.argv[4].lower() if len(sys.argv) > 4 else "h"
    if direction_arg in ["h", "horizontal"]:
        pan_direction = "left_to_right"
    elif direction_arg in ["v", "vertical"]:
        pan_direction = "bottom_to_top"
    else:
        pan_direction = "left_to_right"
    
    # Video oluştur
    create_ken_burns_video(
        image_path=image_path,
        output_path=output_path,
        duration=duration,
        visibility_ratio=0.90,
        pan_direction=pan_direction
    )


if __name__ == "__main__":
    main()  