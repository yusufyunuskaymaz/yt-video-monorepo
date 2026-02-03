#!/bin/bash
# ========================================
# Kod Güncelleme Scripti (RunPod'da çalıştır)
# ========================================
# Git'ten son değişiklikleri çeker ve container'ı restart eder

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CODE_DIR="/workspace/repo"

echo -e "${YELLOW}🔄 Kod güncelleniyor...${NC}"

# Git pull
cd $CODE_DIR
git pull origin main

echo -e "${GREEN}✅ Kod güncellendi${NC}"

# Container'ı restart et (volume mount olduğu için yeni kod otomatik yüklenir)
echo -e "${YELLOW}🔄 Container yeniden başlatılıyor...${NC}"
docker restart video-api

echo ""
echo -e "${GREEN}🎉 Güncelleme tamamlandı!${NC}"
echo -e "📋 Logları kontrol et: ${YELLOW}docker logs -f video-api${NC}"
