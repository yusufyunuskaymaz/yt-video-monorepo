#!/bin/bash
# ========================================
# RunPod'da Python Video API Başlatma Scripti
# Git-Based Kod Güncelleme Desteği ile
# ========================================

set -e

# Renkler
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# GitHub repo (public olmalı, ya da token ile private)
GITHUB_REPO="https://github.com/YusufYunusKaymaz/yt-video-monorepo.git"
CODE_DIR="/workspace/repo"

echo -e "${YELLOW}🚀 RunPod Video API Kurulumu${NC}"
echo "=================================="

# 1. Kodu GitHub'dan çek
if [ -d "$CODE_DIR" ]; then
  echo -e "${YELLOW}📥 Mevcut kod güncelleniyor...${NC}"
  cd $CODE_DIR
  git pull origin main
else
  echo -e "${YELLOW}📥 Kod indiriliyor...${NC}"
  git clone $GITHUB_REPO $CODE_DIR
fi

echo -e "${GREEN}✅ Kod hazır: $CODE_DIR${NC}"

# 2. Ortam değişkenlerini kontrol et
if [ -z "$R2_ACCOUNT_ID" ]; then
  echo -e "${YELLOW}⚠️ Ortam değişkenleri ayarlanmamış. .env dosyasından yükleniyor...${NC}"
  if [ -f "/workspace/.env" ]; then
    export $(cat /workspace/.env | xargs)
    echo -e "${GREEN}✅ .env yüklendi${NC}"
  else
    echo "❌ /workspace/.env dosyası bulunamadı!"
    echo "Lütfen ortam değişkenlerini ayarlayın."
    exit 1
  fi
fi

# 3. Mevcut container'ı durdur (varsa)
docker stop video-api 2>/dev/null || true
docker rm video-api 2>/dev/null || true

# 4. Container'ı başlat (kod volume mount ile)
echo -e "${YELLOW}🐳 Docker container başlatılıyor...${NC}"

docker run -d \
  --name video-api \
  --gpus all \
  -p 8000:8000 \
  -v $CODE_DIR/yt-video/api:/app/api \
  -e PYTHON_API_PORT=8000 \
  -e R2_ACCOUNT_ID="$R2_ACCOUNT_ID" \
  -e R2_ENDPOINT="$R2_ENDPOINT" \
  -e R2_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" \
  -e R2_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" \
  -e R2_BUCKET_NAME="$R2_BUCKET_NAME" \
  -e R2_PUBLIC_URL="$R2_PUBLIC_URL" \
  -e FAL_KEY="$FAL_KEY" \
  -e NODE_CALLBACK_URL="$NODE_CALLBACK_URL" \
  -e IMAGEMAGICK_BINARY=/usr/bin/convert \
  kaymazyusuf/video-api:latest

echo ""
echo -e "${GREEN}🎉 Video API başlatıldı!${NC}"
echo "=================================="
echo -e "📋 Loglar:     ${YELLOW}docker logs -f video-api${NC}"
echo -e "🔗 Health:     ${YELLOW}curl http://localhost:8000/api/video/health${NC}"
echo -e "🔄 Güncelle:   ${YELLOW}./update-code.sh${NC}"
echo -e "🛑 Durdur:     ${YELLOW}docker stop video-api${NC}"