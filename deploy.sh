#!/bin/bash

# 🚀 Docker Hub'a Build & Push Script
# Kullanım: ./deploy.sh [backend|video-api|all]

set -e

DOCKER_USER="kaymazyusuf"

# Renklendirme
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Docker Build & Push Script${NC}"
echo "=================================="

# Backend build & push
build_backend() {
    echo -e "\n${YELLOW}📦 Building Node.js Backend...${NC}"
    docker build --platform linux/amd64 -t $DOCKER_USER/backend_nodejs:latest ./yt-auto-video
    echo -e "${GREEN}✅ Backend build tamamlandı${NC}"
    
    echo -e "${YELLOW}⬆️  Pushing to Docker Hub...${NC}"
    docker push $DOCKER_USER/backend_nodejs:latest
    echo -e "${GREEN}✅ Backend push tamamlandı${NC}"
}

# Video API build & push
build_video_api() {
    echo -e "\n${YELLOW}🎬 Building Python Video API...${NC}"
    docker build --platform linux/amd64 -t $DOCKER_USER/video-api:latest ./yt-video
    echo -e "${GREEN}✅ Video API build tamamlandı${NC}"
    
    echo -e "${YELLOW}⬆️  Pushing to Docker Hub...${NC}"
    docker push $DOCKER_USER/video-api:latest
    echo -e "${GREEN}✅ Video API push tamamlandı${NC}"
}

# Parametre kontrolü
case "${1:-all}" in
    backend)
        build_backend
        ;;
    video-api)
        build_video_api
        ;;
    all)
        build_backend
        build_video_api
        ;;
    *)
        echo -e "${RED}❌ Geçersiz parametre: $1${NC}"
        echo "Kullanım: ./deploy.sh [backend|video-api|all]"
        exit 1
        ;;
esac

echo -e "\n${GREEN}🎉 Deploy tamamlandı!${NC}"
echo "=================================="
echo -e "Yeni image'ları çekmek için:"
echo -e "  ${YELLOW}docker pull $DOCKER_USER/backend_nodejs:latest${NC}"
echo -e "  ${YELLOW}docker pull $DOCKER_USER/video-api:latest${NC}"
