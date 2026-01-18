#!/usr/bin/env python3
"""
Video'ya zamanlı altyazı ekle
Kullanım: python add_subtitles.py video.mp4
"""

import sys
import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip


def add_timed_subtitles(video_path, subtitles, output_path):
    """
    Zamanlı altyazılar ekle
    
    subtitles format:
    [
        {"start": 0, "end": 3, "text": "İlk cümle"},
        {"start": 3, "end": 6, "text": "İkinci cümle"},
    ]
    """
    print(f"📹 Video yükleniyor: {video_path}")
    video = VideoFileClip(video_path)
    
    subtitle_clips = []
    
    for sub in subtitles:
        # Her altyazı için TextClip oluştur
        txt = TextClip(
            text=sub['text'],
            font_size=45,
            color='white',
            stroke_color='black',
            stroke_width=2,
            font='/System/Library/Fonts/Helvetica.ttc',
            size=(video.w - 100, None),
            method='caption',
            text_align='center'
        )
        
        # Zamanla ve konumla
        txt = txt.with_start(sub['start']).with_end(sub['end'])
        txt = txt.with_position(('center', video.h - 150))
        
        subtitle_clips.append(txt)
        print(f"   📝 [{sub['start']:.1f}s - {sub['end']:.1f}s] {sub['text']}")
    
    # Video + tüm altyazılar
    print(f"🎬 Altyazılar ekleniyor...")
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
    
    print(f"✅ Altyazılı video oluşturuldu: {output_path}")
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Kullanım: python add_subtitles.py <video_yolu>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    if not os.path.exists(video_path):
        print(f"❌ Hata: Video bulunamadı: {video_path}")
        sys.exit(1)
    
    # Örnek altyazılar (10 saniye için)
    subtitles = [
        {"start": 0, "end": 2.5, "text": "Gökyüzünün sonsuzluğuna bak..."},
        {"start": 2.5, "end": 5, "text": "Her yıldız bir hikaye anlatır."},
        {"start": 5, "end": 7.5, "text": "Evren, keşfedilmeyi bekliyor."},
        {"start": 7.5, "end": 10, "text": "Hayal et, ulaş, yaşa."}
    ]
    
    # Çıktı dosyası
    base_name = os.path.splitext(video_path)[0]
    output_path = f"{base_name}_subtitled.mp4"
    
    add_timed_subtitles(video_path, subtitles, output_path)


if __name__ == "__main__":
    main()
