#!/bin/bash
# ========================================
# RunPod Startup Script
# ========================================
# Pod her başladığında otomatik çalışır

set -e

echo "🚀 RunPod Startup Script Başladı"

# GitHub'dan kodu çek
REPO_URL="https://github.com/yusufyunuskaymaz/yt-video-monorepo.git"
CODE_DIR="/workspace/code"

if [ -d "$CODE_DIR" ]; then
  echo "📥 Kod güncelleniyor..."
  cd $CODE_DIR
  git pull origin main
else
  echo "📥 Kod indiriliyor..."
  git clone $REPO_URL $CODE_DIR
fi

# Environment variables kontrolü
# RunPod env variables container'a otomatik aktarılır - .env dosyasına gerek yok
if [ -z "$R2_BUCKET_NAME" ]; then
  echo "⚠️ R2_BUCKET_NAME ayarlanmamış - RunPod Environment Variables kontrol et!"
else
  echo "✅ Environment variables yüklendi (R2_BUCKET: $R2_BUCKET_NAME)"
fi

# FFmpeg ve ImageMagick binary paths (MoviePy için)
export FFMPEG_BINARY=/usr/bin/ffmpeg
export IMAGEMAGICK_BINARY=/usr/bin/convert

echo "🔧 FFmpeg: $(ffmpeg -version | head -n1)"
echo "🔧 NVENC: $(ffmpeg -encoders 2>/dev/null | grep nvenc | wc -l) encoders available"

echo "✅ Kod hazır: $CODE_DIR"
echo "🚀 API'ler başlatılıyor..."

# FLUX API'yi arka planda başlat (port 8888)
echo "🎨 FLUX API başlatılıyor (port 8888)..."
cd $CODE_DIR/ai-service
python3 -c "import uvicorn; uvicorn.run('api:app', host='0.0.0.0', port=8888)" &

# Video API'yi ön planda başlat (port 8000)
echo "🎬 Video API başlatılıyor (port 8000)..."
cd $CODE_DIR/yt-video/api
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
