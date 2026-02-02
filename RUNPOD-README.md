# 🚀 RunPod GPU Deployment Guide

Bu proje RunPod'da RTX 5090 GPU ile hızlı video işleme için optimize edilmiştir.

## 📋 Ön Koşullar

1. RunPod hesabı
2. RTX 5090 (veya başka NVIDIA GPU) bulunan pod
3. Harici PostgreSQL veritabanı (Neon, Supabase, vb.)
4. Cloudflare R2 bucket (veya S3 uyumlu storage)
5. Fal.ai API key

---

## 🎯 Hızlı Başlangıç (5 Dakika)

### 1. Pod Oluştur

RunPod'da yeni pod oluştur:

- **GPU**: RTX 5090 (veya istediğiniz)
- **Template**: Docker + Docker Compose
- **Container Disk**: 20GB+ (video temp dosyaları için)
- **Volume**: Opsiyonel (kalıcı veri için)

### 2. Projeyi Clone'la

```bash
cd /workspace
git clone https://github.com/your-repo/yt-video-monorepo.git
cd yt-video-monorepo
```

### 3. Environment Ayarla

```bash
cp .env.example .env
nano .env  # Veya vim, değerleri doldurun
```

### 4. Deploy Et

```bash
chmod +x runpod-deploy.sh
./runpod-deploy.sh
```

---

## 📁 Dosya Yapısı

```
ortak/
├── docker-compose.runpod.yml   # GPU destekli compose
├── .env.example                 # Environment template
├── runpod-deploy.sh             # Deploy script
├── yt-auto-video/               # Node.js Backend
│   └── Dockerfile
└── yt-video/                    # Python Video API
    ├── Dockerfile               # CPU versiyonu
    └── Dockerfile.gpu           # GPU versiyonu (RunPod için)
```

---

## ⚙️ Environment Variables

| Değişken               | Açıklama                     |
| ---------------------- | ---------------------------- |
| `DATABASE_URL`         | PostgreSQL connection string |
| `R2_ACCOUNT_ID`        | Cloudflare hesap ID          |
| `R2_ACCESS_KEY_ID`     | R2 access key                |
| `R2_SECRET_ACCESS_KEY` | R2 secret key                |
| `R2_BUCKET_NAME`       | Bucket adı                   |
| `R2_PUBLIC_URL`        | Public bucket URL            |
| `FAL_KEY`              | Fal.ai API key               |

---

## 🔧 Yaygın Komutlar

```bash
# Container'ları başlat
docker compose -f docker-compose.runpod.yml up -d

# Logları takip et
docker compose -f docker-compose.runpod.yml logs -f

# Sadece video-api logları
docker compose -f docker-compose.runpod.yml logs -f video-api

# Container'ları durdur
docker compose -f docker-compose.runpod.yml down

# Her şeyi temizle (image'lar dahil)
docker compose -f docker-compose.runpod.yml down --rmi all -v
```

---

## 🎥 GPU Hızlandırması

FFmpeg NVENC kullanarak video encoding'i GPU'da yapılır:

- H.264/HEVC encoding
- Video merge işlemleri
- Ken Burns effect rendering

**Performans Karşılaştırması** (tahmini):
| İşlem | CPU | GPU (RTX 5090) |
|-------|-----|----------------|
| 10s video render | ~30s | ~3s |
| Video merge (5 parça) | ~60s | ~8s |
| Full project (10 scene) | ~5dk | ~30s |

---

## 🧹 Pod'u Silmeden Önce

İşiniz bittiğinde:

```bash
# Container'ları durdur
docker compose -f docker-compose.runpod.yml down

# (Opsiyonel) Projeyi sil
cd /workspace && rm -rf yt-video-monorepo
```

Sonra RunPod panelinden pod'u terminate edin.

---

## 🐛 Sorun Giderme

### GPU Görünmüyor

```bash
nvidia-smi  # GPU durumunu kontrol et
docker info | grep nvidia  # Docker NVIDIA runtime kontrol
```

### Container Başlamıyor

```bash
docker compose -f docker-compose.runpod.yml logs video-api
```

### ImageMagick Hatası

```bash
docker exec -it <container_id> cat /etc/ImageMagick-6/policy.xml
```
