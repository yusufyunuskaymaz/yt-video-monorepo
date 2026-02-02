# GPU Video İşleme Servisi - RunPod için
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Sistem bağımlılıkları ve Python 3.12 için PPA ekleme
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip \
    ffmpeg \
    imagemagick \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    ghostscript \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python symlink düzenlemesi
RUN ln -sf /usr/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/bin/python3 /usr/bin/python

# Pip güncellemesi (Python 3.12 ile uyum için)
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

WORKDIR /app

# Python bağımlılıkları
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Uygulama kodları
COPY . .

RUN mkdir -p temp_videos && chmod 777 temp_videos

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]