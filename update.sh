#!/bin/bash
# ========================================
# Kod Güncelleme Scripti (RunPod)
# ========================================
# Git pull yapar, container otomatik yenilenir (hot-reload)

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

WORK_DIR="/workspace/repo"

echo -e "${YELLOW}🔄 Kod güncelleniyor...${NC}"

cd $WORK_DIR
git pull origin main

echo -e "${GREEN}✅ Kod güncellendi!${NC}"
echo ""
echo -e "Volume mount aktif olduğu için container otomatik yenilenir."
echo -e "Eğer yenilenmezse: ${YELLOW}docker compose -f docker-compose.runpod.yml restart${NC}"