FROM python:3.12-slim

# Sistem bağımlılıklarını yükle
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    libsm6 \
    libxext6 \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# ImageMagick policy düzenlemesi (Versiyon bağımsız çözüm)
# policy.xml dosyasını bul ve düzenle (6 veya 7 olabilir)
RUN if [ -f /etc/ImageMagick-6/policy.xml ]; then \
        sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml; \
    elif [ -f /etc/ImageMagick-7/policy.xml ]; then \
        sed -i 's/none/read,write/g' /etc/ImageMagick-7/policy.xml; \
    elif [ -f /etc/ImageMagick/policy.xml ]; then \
        sed -i 's/none/read,write/g' /etc/ImageMagick/policy.xml; \
    fi

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
