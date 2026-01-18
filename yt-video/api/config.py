"""
Konfigürasyon - Ortam Değişkenleri
"""
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# R2 CDN Ayarları
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL")

# API Ayarları
NODE_CALLBACK_URL = os.getenv("NODE_CALLBACK_URL", "http://localhost:3000/webhook")
API_PORT = int(os.getenv("PYTHON_API_PORT", "8000"))

# Video Ayarları
DEFAULT_VIDEO_DURATION = 10
DEFAULT_FPS = 30
DEFAULT_VISIBILITY_RATIO = 0.90
DEFAULT_PAN_DIRECTION = "vertical"  # "horizontal" veya "vertical"