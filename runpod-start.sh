#!/bin/bash
# ========================================
# RunPod Başlatma Scripti (Docker Hub'sız)
# ========================================
# Git'ten kod çeker, local build yapar, çalıştırır

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

GITHUB_REPO="https://github.com/yusufyunuskaymaz/yt-video-monorepo.git"
WORK_DIR="/workspace/repo"

echo -e "${YELLOW}🚀 RunPod Video API Kurulumu (Docker Hub'sız)${NC}"
echo "=================================================="

# 1. Git'ten kodu çek
if [ -d "$WORK_DIR" ]; then
  echo -e "${YELLOW}📥 Mevcut kod güncelleniyor...${NC}"
  cd $WORK_DIR
  git pull origin main
else
  echo -e "${YELLOW}📥 Kod indiriliyor...${NC}"
  git clone $GITHUB_REPO $WORK_DIR
  cd $WORK_DIR
fi

echo -e "${GREEN}✅ Kod hazır${NC}"

# 2. .env dosyasını kontrol et
if [ ! -f "/workspace/.env" ]; then
  echo -e "${RED}❌ /workspace/.env dosyası bulunamadı!${NC}"
  echo "Lütfen şu değişkenleri içeren .env oluşturun:"
  echo "  R2_ACCOUNT_ID, R2_ENDPOINT, R2_ACCESS_KEY_ID,"
  echo "  R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_PUBLIC_URL,"
  echo "  FAL_KEY, NODE_CALLBACK_URL"
  exit 1
fi

# .env'i proje dizinine kopyala
cp /workspace/.env $WORK_DIR/.env
echo -e "${GREEN}✅ .env yüklendi${NC}"

# 3. Docker Compose ile build & başlat
echo -e "${YELLOW}🐳 Docker build başlatılıyor (GPU destekli)...${NC}"

cd $WORK_DIR
docker compose -f docker-compose.runpod.yml down 2>/dev/null || true
docker compose -f docker-compose.runpod.yml build
docker compose -f docker-compose.runpod.yml up -d

echo ""
echo -e "${GREEN}🎉 Video API başlatıldı! (GPU Aktif)${NC}"
echo "=================================================="
echo -e "📋 Loglar:     ${YELLOW}docker compose -f docker-compose.runpod.yml logs -f${NC}"
echo -e "🔗 Health:     ${YELLOW}curl http://localhost:8000/api/video/health${NC}"
echo -e "🧪 GPU Test:   ${YELLOW}curl http://localhost:8000/api/video/gpu-test${NC}"
echo -e "🔄 Güncelle:   ${YELLOW}./update.sh${NC}"
echo -e "🛑 Durdur:     ${YELLOW}docker compose -f docker-compose.runpod.yml down${NC}"