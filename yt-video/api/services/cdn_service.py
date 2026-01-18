"""
R2 CDN Servisi - Video/Resim yükleme
"""
import os
import sys
import boto3
from botocore.config import Config

# API dizinine path ekle
API_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, API_DIR)

from config import (
    R2_ENDPOINT,
    R2_ACCESS_KEY_ID, 
    R2_SECRET_ACCESS_KEY,
    R2_BUCKET_NAME,
    R2_PUBLIC_URL
)


def get_s3_client():
    """R2 S3 client oluştur"""
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )


def upload_file(filepath: str, key: str, content_type: str = "video/mp4") -> str:
    """
    Dosyayı R2'ye yükle
    
    Args:
        filepath: Yerel dosya yolu
        key: R2 key (dosya adı)
        content_type: MIME type
        
    Returns:
        Public URL
    """
    print(f"\n========== R2 UPLOAD ==========")
    print(f"📁 Dosya: {filepath}")
    print(f"🔑 Key: {key}")
    print(f"🪣 Bucket: {R2_BUCKET_NAME}")
    
    if not os.path.exists(filepath):
        print(f"❌ HATA: Dosya bulunamadı!")
        raise FileNotFoundError(f"Dosya bulunamadı: {filepath}")
    
    file_size = os.path.getsize(filepath)
    size_mb = file_size / (1024 * 1024)
    print(f"📦 Dosya boyutu: {size_mb:.2f} MB")
    print(f"☁️ R2'ye yükleniyor...")
    
    try:
        client = get_s3_client()
        
        with open(filepath, 'rb') as f:
            client.put_object(
                Bucket=R2_BUCKET_NAME,
                Key=key,
                Body=f,
                ContentType=content_type
            )
        
        # URL oluştur
        url = f"{R2_PUBLIC_URL}/{key}"
        print(f"✅ R2 BAŞARILI!")
        print(f"🔗 URL: {url}")
        print(f"================================\n")
        
        return url
        
    except Exception as e:
        print(f"❌ R2 HATA: {str(e)}")
        print(f"================================\n")
        raise


def upload_video(filepath: str, scene_id: str) -> str:
    """
    Video dosyasını R2'ye yükle
    
    Args:
        filepath: Video dosya yolu
        scene_id: Sahne ID (dosya adı için)
        
    Returns:
        CDN URL
    """
    import time
    timestamp = int(time.time())
    key = f"videos/{scene_id}_{timestamp}.mp4"
    return upload_file(filepath, key, "video/mp4")
