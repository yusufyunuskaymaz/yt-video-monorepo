FROM pytorch/pytorch:2.4.0-cuda12.4-cudnn9-runtime

# Sistem paketleri
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python paketleri
RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn==0.30.6 \
    diffusers==0.30.0 \
    transformers==4.44.0 \
    accelerate==0.33.0 \
    sentencepiece \
    protobuf \
    safetensors \
    python-multipart \
    boto3

WORKDIR /app

# API kodu
COPY api.py /app/api.py
COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# Model cache dizini
RUN mkdir -p /app/models /app/outputs

EXPOSE 8888

CMD ["/app/startup.sh"]
