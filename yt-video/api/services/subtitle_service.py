"""
Subtitle Service - FFmpeg tabanlı stilli altyazı (ASS/Word Highlight)
"""
import subprocess
import os
import textwrap

# imageio-ffmpeg kullanarak FFmpeg yolunu bul
try:
    import imageio_ffmpeg
    FFMPEG_BINARY = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG_BINARY = 'ffmpeg' # Fallback to system command





def generate_ass_header(width=1080, height=1920, font_size=130):
    """ASS dosya başlığı ve stillerini oluşturur."""
    # MarginV: 200 - alttan yukarıya mesafe (fazla yukarı olmasın)
    margin_v = 200
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,0,2,10,10,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def format_time_ass(seconds):
    """Saniye -> ASS zaman formatı (H:MM:SS.cs)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

def generate_ass_content(text: str, duration: float, font_size=90, max_chars_per_line=25):
    """ASS içeriği oluşturur (Kelime vurgulu)"""
    words = text.split()
    if not words:
        return ""

    word_duration = duration / len(words)
    ass_lines = []
    
    # Kelime Zamanlamaları
    word_timings = []
    for i, word in enumerate(words):
        start = i * word_duration
        end = (i + 1) * word_duration
        word_timings.append({"text": word, "start": start, "end": end})
    
    # Satırlara böl
    lines = [] 
    current_line = []
    current_length = 0
    
    for w in word_timings:
        word_len = len(w['text'])
        if current_length + word_len + len(current_line) > max_chars_per_line and current_line:
            lines.append(current_line)
            current_line = []
            current_length = 0
        current_line.append(w)
        current_length += word_len
        
    if current_line:
        lines.append(current_line)
        
    # Karaoke satırlarını oluştur
    for line_words in lines:
        if not line_words: continue
        
        for i, active_word in enumerate(line_words):
            current_start = active_word['start']
            current_end = active_word['end']
            
            text_parts = []
            for j, w in enumerate(line_words):
                word_text = w['text']
                if i == j:
                    # Aktif Kelime: 
                    # \1c&HFFFFFF& -> Beyaz Renk
                    # \alpha&H00& -> Tam Görünür (Opak)
                    # \bord15 -> Çok Kalın Siyah Kenar
                    # \blur5 -> Yumuşatma (Kenarları eritir, boğumları yok eder, soft gölge yapar)
                    # \3c&H000000& -> Siyah Kenar Rengi
                    text_parts.append(f"{{\\1c&HFFFFFF&}}{{\\alpha&H00&}}{{\\3c&H000000&}}{{\\bord15}}{{\\blur5}}{word_text}")
                else:
                    # Pasif Kelime:
                    # \alpha&H00& -> Tam Görünür (Opak Beyaz)
                    # \bord0 -> Kenar Yok
                    # \blur0 -> Blur Yok
                    text_parts.append(f"{{\\1c&HFFFFFF&}}{{\\alpha&H00&}}{{\\bord0}}{{\\blur0}}{word_text}")
            
            full_line_text = " ".join(text_parts)
            full_line_text = full_line_text.replace("  ", " ")
            
            ass_lines.append(
                f"Dialogue: 0,{format_time_ass(current_start)},{format_time_ass(current_end)},Default,,0,0,0,,{full_line_text}"
            )
            
    return "\n".join(ass_lines)


def add_karaoke_subtitles(
    video_path: str,
    text: str,
    duration: float,
    output_path: str,
    style: str = 'yellow', 
    max_words_per_line: int = 8,
    font_size: int = 24 
) -> str:
    """
    FFmpeg ve ASS formatı kullanarak videoya kelime vurgulu altyazı ekle
    """
    # Font boyutunu zorla sabitle (130px)
    fixed_font_size = 130
    
    print(f"\n📝 ========== ASS KARAOKE ALTYAZI ==========")
    print(f"📄 Metin: {text[:50]}...")
    print(f"⏱️ Süre: {duration:.2f}s")
    print(f"📏 Font Boyutu: {fixed_font_size}pt")
    print(f"🎨 Stil: Soft Shadow Highlight (Blur)")
    print(f"🛠️ FFmpeg Yolu: {FFMPEG_BINARY}")
    print(f"===========================================\n")
    print(f"📄 Metin: {text[:50]}...")
    print(f"⏱️ Süre: {duration:.2f}s")
    print(f"📏 Font Boyutu: {fixed_font_size}pt")
    print(f"🎨 Stil: White text with Yellow Highlight")
    print(f"🛠️ FFmpeg Yolu: {FFMPEG_BINARY}")
    print(f"===========================================\n")

    # 1. ASS dosyasını oluştur
    ass_header = generate_ass_header(font_size=fixed_font_size)
    ass_body = generate_ass_content(text, duration, font_size=fixed_font_size)
    ass_content = ass_header + ass_body
    
    # 2. ASS dosyasını kaydet
    ass_path = output_path.replace('.mp4', '.ass')
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)
        
    print(f"📝 ASS oluşturuldu: {ass_path}")

    # Dosya adlarını ve dizini hazırla
    input_dir = os.path.dirname(video_path)
    input_filename = os.path.basename(video_path)
    output_filename = os.path.basename(output_path)
    ass_filename = os.path.basename(ass_path)
    
    try:
        # FFmpeg komutu - Sadece dosya adları, path yok (cwd değiştireceğiz)
        cmd = [
            FFMPEG_BINARY,
            '-y', 
            '-i', input_filename,
            '-vf', f"ass={ass_filename}", 
            '-c:a', 'copy',
            '-c:v', 'libx264',
            output_filename
        ]
        
        print(f"🚀 FFmpeg çalıştırılıyor (Dizin: {input_dir})...")
        # cwd=input_dir ile çalıştırıyoruz ki path sorunu olmasın
        result = subprocess.run(
            cmd, 
            cwd=input_dir, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            check=False # Hata durumunda biz handle edelim
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.decode()
            print(f"❌ FFmpeg Hatası:\n{error_msg}")
            
            if "Fontconfig error" in error_msg or "error opening file" in error_msg:
                 print("⚠️ Font hatası olabilir, basit mod deneniyor...")
            
            print("⚠️ Orijinal video dönülüyor.")
            return video_path
            
        print(f"✅ Altyazı başarıyla eklendi: {output_path}")
        
    except Exception as e:
        print(f"❌ Beklenmeyen Hata: {e}")
        return video_path
    
    # Temizlik
    full_ass_path = os.path.join(input_dir, ass_filename)
    if os.path.exists(full_ass_path):
        try:
            os.remove(full_ass_path)
        except:
            pass
            
    return output_path
