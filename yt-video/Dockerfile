FROM python:3.12-slim

# Sistem bağımlılıklarını yükle
# ffmpeg: Video işleme
# imagemagick: MoviePy TextClip için (altyazı vs)
# libsm6, libxext6: OpenCV bağımlılıkları
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    libsm6 \
    libxext6 \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# ImageMagick policy düzenlemesi (MoviePy'nin çalışması için gerekli)
# "none" olan policy'i "read|write" olarak değiştirir
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml

# Çalışma dizini
WORKDIR /app

# Bağımlılıkları kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodlarını kopyala
COPY . .

# Geçici klasörler için izinler
RUN mkdir -p temp_videos && chmod 777 temp_videos

# Port
EXPOSE 8000

# Çalıştırma komutu
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
