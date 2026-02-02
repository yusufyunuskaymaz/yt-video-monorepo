#!/bin/bash
# ==========================================
# RunPod Hızlı Deploy Script
# ==========================================
# Kullanım: ./runpod-deploy.sh
#
# Bu script RunPod pod'unda çalıştırılmalı
# Önce .env dosyasını hazırlayın!

set -e

echo "🚀 RunPod Video İşleme Servisi Deploy Ediliyor..."

# 1. Gerekli dizinleri oluştur
echo "📁 Temp dizinleri oluşturuluyor..."
mkdir -p temp_videos
chmod 777 temp_videos

# 2. .env kontrolü
if [ ! -f .env ]; then
    echo "❌ HATA: .env dosyası bulunamadı!"
    echo "   .env.example dosyasını kopyalayıp değerleri doldurun:"
    echo "   cp .env.example .env"
    exit 1
fi

echo "✅ .env dosyası bulundu"

# 3. Docker Compose ile başlat (GPU destekli)
echo "🐳 Docker containers başlatılıyor (GPU destekli)..."
docker compose -f docker-compose.runpod.yml up --build -d

# 4. Log takibi
echo ""
echo "=========================================="
echo "✅ Deploy tamamlandı!"
echo "=========================================="
echo ""
echo "🌐 Backend API:    http://localhost:3000"
echo "🎬 Video API:      http://localhost:8000"
echo "📚 API Docs:       http://localhost:8000/docs"
echo ""
echo "📋 Logları görmek için:"
echo "   docker compose -f docker-compose.runpod.yml logs -f"
echo ""
echo "🛑 Durdurmak için:"
echo "   docker compose -f docker-compose.runpod.yml down"
echo ""
