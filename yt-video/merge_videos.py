#!/usr/bin/env python3
"""
Downloads klasöründeki tüm videoları birleştir
Kullanım: python merge_videos.py
"""

import os
import glob
from moviepy import VideoFileClip, concatenate_videoclips


def merge_videos(input_dir="downloads", output_path="downloads/merged_video.mp4"):
    """Downloads klasöründeki tüm mp4 dosyalarını birleştir"""
    
    # Tüm mp4 dosyalarını bul (merged hariç)
    video_files = sorted(glob.glob(os.path.join(input_dir, "*.mp4")))
    video_files = [f for f in video_files if "merged" not in f]
    
    if not video_files:
        print("❌ Birleştirilecek video bulunamadı!")
        return
    
    print(f"📹 {len(video_files)} video bulundu:")
    for f in video_files:
        print(f"   - {os.path.basename(f)}")
    
    # Videoları yükle
    print(f"\n🎬 Videolar yükleniyor...")
    clips = []
    for video_file in video_files:
        clip = VideoFileClip(video_file)
        clips.append(clip)
        print(f"   ✓ {os.path.basename(video_file)} ({clip.duration:.1f}s)")
    
    # Birleştir
    print(f"\n🔗 Videolar birleştiriliyor...")
    final = concatenate_videoclips(clips, method="compose")
    
    print(f"   Toplam süre: {final.duration:.1f} saniye")
    
    # Kaydet
    print(f"\n💾 Kaydediliyor: {output_path}")
    final.write_videofile(
        output_path,
        codec='libx264',
        audio=False,
        fps=30,
        logger='bar'
    )
    
    # Temizlik
    for clip in clips:
        clip.close()
    final.close()
    
    print(f"\n✅ Birleştirilmiş video: {output_path}")


if __name__ == "__main__":
    merge_videos()
