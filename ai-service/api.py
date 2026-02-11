"""
FLUX Image Generation API
RunPod üzerinde çalışır, Node.js backend'den çağrılır
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import torch
import time
import os
import boto3
from botocore.config import Config

app = FastAPI(title="FLUX API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Config ============
MODELS_DIR = os.getenv("MODELS_DIR", "/app/models")
OUTPUTS_DIR = os.getenv("OUTPUTS_DIR", "/app/outputs")
PROJECTS_DIR = "/tmp/projects"  # Video API ile paylaşımlı dizin

# R2 CDN Config (env'den)
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "ai-voice")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "https://voicy.site")


# ============ Global Model State ============
flux_pipe = None


# ============ R2 Upload ============
def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )


def upload_to_r2(filepath: str, key: str, content_type: str = "image/png") -> str:
    """Dosyayı R2'ye yükle, CDN URL döndür"""
    print(f"☁️ R2'ye yükleniyor: {key}")
    client = get_s3_client()
    with open(filepath, 'rb') as f:
        client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=key,
            Body=f,
            ContentType=content_type
        )
    url = f"{R2_PUBLIC_URL}/{key}"
    print(f"✅ R2 URL: {url}")
    return url


# ============ Request/Response Models ============
class ImageRequest(BaseModel):
    prompt: str
    num_inference_steps: int = 4
    width: int = 1024
    height: int = 768
    seed: Optional[int] = None
    upload_to_cdn: bool = True
    project_id: Optional[str] = None
    scene_number: Optional[int] = None


class ImageResponse(BaseModel):
    success: bool
    cdn_url: Optional[str] = None
    local_path: Optional[str] = None
    filename: Optional[str] = None
    generation_time: Optional[float] = None
    error: Optional[str] = None


# ============ Model Loading ============
def load_flux():
    """FLUX modelini yükle (lazy loading - ilk istekte)"""
    global flux_pipe

    if flux_pipe is not None:
        return flux_pipe

    print("🚀 FLUX modeli yükleniyor...")
    start = time.time()

    from diffusers import FluxPipeline

    flux_pipe = FluxPipeline.from_pretrained(
        "black-forest-labs/FLUX.1-schnell",
        torch_dtype=torch.bfloat16,
        cache_dir=MODELS_DIR,
        token=os.getenv("HF_TOKEN")
    )

    # GPU VRAM kontrolü
    if torch.cuda.is_available():
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        if vram_gb >= 40:
            flux_pipe.to("cuda")
            print(f"⚡ FLUX direkt GPU ({vram_gb:.0f}GB VRAM)")
        else:
            flux_pipe.enable_model_cpu_offload()
            print(f"🔄 FLUX CPU offload ({vram_gb:.0f}GB VRAM)")
    else:
        print("⚠️ GPU yok, CPU modunda")

    elapsed = time.time() - start
    print(f"✅ FLUX hazır! ({elapsed:.1f}s)")
    return flux_pipe


# ============ Startup Warmup ============
@app.on_event("startup")
async def warmup():
    """API başlayınca modeli yükle ve test resmi üret"""
    print("\n🔥 WARMUP başlıyor...")
    try:
        pipe = load_flux()
        print("🎨 Warmup resmi üretiliyor...")
        start = time.time()
        image = pipe("test warmup", num_inference_steps=1, width=256, height=256).images[0]
        print(f"✅ Warmup tamamlandı! ({time.time() - start:.1f}s)")
        del image
        torch.cuda.empty_cache()
    except Exception as e:
        print(f"⚠️ Warmup hatası (devam ediliyor): {e}")


# ============ Endpoints ============
@app.get("/")
async def root():
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A"
    vram = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 1) if torch.cuda.is_available() else 0
    return {
        "service": "FLUX API",
        "version": "1.0.0",
        "gpu": gpu_name,
        "vram_gb": vram,
        "flux_loaded": flux_pipe is not None,
    }


@app.get("/health")
async def health():
    return {"status": "ok", "gpu": torch.cuda.is_available(), "flux_loaded": flux_pipe is not None}


@app.post("/generate-image", response_model=ImageResponse)
async def generate_image(req: ImageRequest):
    """FLUX ile resim üret ve CDN'e yükle"""
    try:
        print(f"\n🎨 ========== RESIM ÜRETİMİ ==========")
        print(f"📝 Prompt: {req.prompt[:80]}...")
        print(f"📐 Boyut: {req.width}x{req.height}")
        print(f"🔄 Steps: {req.num_inference_steps}")
        if req.project_id:
            print(f"📁 Proje: {req.project_id}, Sahne: {req.scene_number}")

        pipe = load_flux()

        # Seed
        generator = None
        if req.seed is not None:
            generator = torch.Generator("cuda").manual_seed(req.seed)

        # Resim üret
        start = time.time()
        image = pipe(
            req.prompt,
            num_inference_steps=req.num_inference_steps,
            width=req.width,
            height=req.height,
            generator=generator
        ).images[0]
        generation_time = round(time.time() - start, 2)

        # Dosya adı
        timestamp = int(time.time())
        unique_id = f"{timestamp}_{os.urandom(3).hex()}"

        if req.project_id and req.scene_number is not None:
            filename = f"{req.project_id}_scene_{str(req.scene_number).zfill(3)}_{unique_id}.png"
        else:
            filename = f"img_{unique_id}.png"

        # Kaydet - proje dizinine veya outputs'a
        if req.project_id and not req.upload_to_cdn:
            # Proje dizinine kaydet (video API ile paylaşımlı)
            save_dir = os.path.join(PROJECTS_DIR, str(req.project_id))
            os.makedirs(save_dir, exist_ok=True)
        else:
            save_dir = OUTPUTS_DIR
            os.makedirs(save_dir, exist_ok=True)

        filepath = os.path.join(save_dir, filename)
        image.save(filepath, "PNG")

        # CDN'e yükle veya lokal path döndür
        cdn_url = None
        local_path = None
        if req.upload_to_cdn and R2_ENDPOINT:
            key = f"images/{filename}"
            cdn_url = upload_to_r2(filepath, key, "image/png")
            os.remove(filepath)  # CDN'e yüklendi, sil
        else:
            local_path = filepath
            cdn_url = f"local://{filepath}"

        print(f"✅ Resim üretildi: {filename} ({generation_time}s)")
        print(f"🔗 CDN: {cdn_url}\n")

        return ImageResponse(
            success=True,
            cdn_url=cdn_url,
            local_path=local_path,
            filename=filename,
            generation_time=generation_time
        )

    except Exception as e:
        print(f"❌ Hata: {str(e)}")
        import traceback
        traceback.print_exc()
        return ImageResponse(success=False, error=str(e))
