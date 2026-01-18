#!/usr/bin/env python3
"""
Karaoke tarzı kelime kelime takipli altyazı
Kullanım: python karaoke_subtitles.py video.mp4
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip


def create_word_highlight_frame(words, current_word_idx, video_width, video_height, font_path, font_size=50):
    """
    Kelime kelime highlight edilmiş frame oluştur
    Aktif kelime: kırmızı arka plan + beyaz yazı
    Diğer kelimeler: beyaz yazı + siyah stroke
    """
    # Yeterince büyük bir canvas oluştur
    img = Image.new('RGBA', (video_width, 200), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        # Bold font kullan
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
    
    # Kelimeleri büyük harfe çevir
    words_upper = [w.upper() for w in words]
    
    # Kelimelerin genişliklerini hesapla
    word_widths = []
    space_width = draw.textbbox((0, 0), " ", font=font)[2]
    
    for word in words_upper:
        bbox = draw.textbbox((0, 0), word, font=font)
        word_widths.append(bbox[2] - bbox[0])
    
    # Toplam genişlik
    total_width = sum(word_widths) + space_width * (len(words_upper) - 1)
    
    # Başlangıç x pozisyonu (ortala)
    x = (video_width - total_width) // 2
    y = 50
    
    padding_x = 12
    padding_y = 8
    
    for i, word in enumerate(words_upper):
        word_width = word_widths[i]
        
        if i == current_word_idx:
            # Aktif kelime - SİYAH arka plan
            draw.rectangle(
                [x - padding_x, y - padding_y, x + word_width + padding_x, y + font_size + padding_y],
                fill=(0, 0, 0, 230)  # Siyah
            )
            draw.text((x, y), word, font=font, fill=(255, 255, 255, 255))
        else:
            # Diğer kelimeler - beyaz yazı + kalın siyah stroke
            stroke_width = 3
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), word, font=font, fill=(0, 0, 0, 255))
            draw.text((x, y), word, font=font, fill=(255, 255, 255, 255))
        
        x += word_width + space_width
    
    return np.array(img)


def add_karaoke_subtitles(video_path, subtitles, output_path):
    """
    Karaoke tarzı kelime kelime takipli altyazı ekle
    
    subtitles format:
    [
        {"start": 0, "end": 3, "text": "İlk cümle burada"},
        {"start": 3, "end": 6, "text": "İkinci cümle burada"},
    ]
    """
    print(f"📹 Video yükleniyor: {video_path}")
    video = VideoFileClip(video_path)
    
    font_path = '/System/Library/Fonts/Helvetica.ttc'
    
    subtitle_clips = []
    
    for sub in subtitles:
        words = sub['text'].split()
        num_words = len(words)
        duration = sub['end'] - sub['start']
        word_duration = duration / num_words
        
        print(f"   📝 [{sub['start']:.1f}s - {sub['end']:.1f}s] {sub['text']}")
        print(f"      {num_words} kelime, her biri {word_duration:.2f}s")
        
        # Her kelime için ayrı clip oluştur
        for word_idx in range(num_words):
            word_start = sub['start'] + word_idx * word_duration
            word_end = word_start + word_duration
            
            # Bu kelime için frame oluştur (tek seferlik)
            frame = create_word_highlight_frame(
                words, word_idx, video.w, video.h, font_path
            )
            
            clip = ImageClip(frame, duration=word_duration)
            clip = clip.with_start(word_start)
            clip = clip.with_position(('center', video.h - 180))
            
            subtitle_clips.append(clip)
    
    # Video + tüm altyazılar
    print(f"🎬 Karaoke altyazılar ekleniyor...")
    final = CompositeVideoClip([video] + subtitle_clips)
    
    # Kaydet
    print(f"💾 Video kaydediliyor: {output_path}")
    final.write_videofile(
        output_path,
        codec='libx264',
        audio=False,
        fps=video.fps,
        logger='bar'
    )
    
    video.close()
    final.close()
    
    print(f"✅ Karaoke altyazılı video oluşturuldu: {output_path}")
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Kullanım: python karaoke_subtitles.py <video_yolu>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    if not os.path.exists(video_path):
        print(f"❌ Hata: Video bulunamadı: {video_path}")
        sys.exit(1)
    
    # Örnek altyazılar (10 saniye için)
    subtitles = [
        {"start": 0, "end": 2.5, "text": "Gökyüzünün sonsuzluğuna bak"},
        {"start": 2.5, "end": 5, "text": "Her yıldız bir hikaye anlatır"},
        {"start": 5, "end": 7.5, "text": "Evren keşfedilmeyi bekliyor"},
        {"start": 7.5, "end": 10, "text": "Hayal et ulaş yaşa"}
    ]
    
    # Çıktı dosyası
    base_name = os.path.splitext(video_path)[0]
    output_path = f"{base_name}_karaoke.mp4"
    
    add_karaoke_subtitles(video_path, subtitles, output_path)


if __name__ == "__main__":
    main()
