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

# .env dosyasını kontrol et
if [ ! -f "/workspace/.env" ]; then
  echo "⚠️ /workspace/.env bulunamadı - lütfen RunPod environment variables ayarlayın"
fi

# Environment variables yükle
if [ -f "/workspace/.env" ]; then
  export $(cat /workspace/.env | xargs)
fi

# FFmpeg binary'yi ayarla
export FFMPEG_BINARY=/usr/bin/ffmpeg
export IMAGEMAGICK_BINARY=/usr/bin/convert

echo "✅ Kod hazır: $CODE_DIR"
echo "🚀 API başlatılıyor..."

# API'yi başlat
cd $CODE_DIR/yt-video/api
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
