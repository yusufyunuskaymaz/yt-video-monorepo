const { fal } = require("../config/fal.config");
const r2Service = require("./r2.service");
const { startTimer, endTimer } = require("../utils/timing");

/**
 * Benzersiz ID oluştur (timestamp + random)
 */
function generateId() {
  return `${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
}

/**
 * Sabit stil şablonu - Tüm görseller bu stilde üretilecek
 */
const STYLE_TEMPLATE = {
  technique: "THICK IMPASTO gouache painting",
  brushwork:
    "HEAVY VISIBLE BRUSHSTROKES, chunky paint application, textured canvas with paint ridges, bold loose brushwork, palette knife technique",
  texture:
    "authentic paint texture NOT smooth, rough painted surface, expressive brush marks",
  colors: "bright warm Mediterranean colors with reds yellows ochre blues",
  medium: "traditional gouache medium with thick layers, NOT digital rendering",
  detail_level:
    "detailed facial features, sharp focus, clear facial expressions, portrait-quality faces, close-up perspective, high detail on figures",
};

/**
 * Stil şablonundan tam prompt oluştur
 * @param {string} subject - Sahne konusu
 * @returns {string} Tam prompt
 */
function buildPromptFromTemplate(subject) {
  return `${subject}, ${STYLE_TEMPLATE.technique}, ${STYLE_TEMPLATE.brushwork}, ${STYLE_TEMPLATE.texture}, ${STYLE_TEMPLATE.colors}, ${STYLE_TEMPLATE.medium}, ${STYLE_TEMPLATE.detail_level}`;
}

/**
 * Fal.ai Stable Diffusion XL ile resim üretir ve R2'ye yükler
 * @param {object} promptData - Prompt verisi (subject string veya obje)
 * @param {string} projectId - Proje ID (opsiyonel, dosya adı için)
 * @param {number} sceneNumber - Sahne numarası (opsiyonel, dosya adı için)
 * @returns {Promise<Object>} Üretilen resim bilgileri
 */
async function generateImage({ prompt: promptData, projectId, sceneNumber }) {
  console.log("🎨 Resim üretiliyor...");

  // Subject'i al ve sabit stil ile birleştir
  const subject =
    typeof promptData === "string"
      ? promptData
      : promptData.subject || promptData;
  const fullPrompt = buildPromptFromTemplate(subject);

  console.log("📝 Subject:", subject);
  console.log("🎨 Stil: THICK IMPASTO gouache painting");

  try {
    // Fal.ai API çağrısını ölç
    const falTimer = startTimer("FAL_IMAGE_GENERATION");
    const result = await fal.subscribe("fal-ai/lora", {
      input: {
        model_name: "stabilityai/stable-diffusion-xl-base-1.0",
        prompt: fullPrompt,
        negative_prompt:
          "cartoon, painting, illustration, worst quality, low quality, normal quality",
        prompt_weighting: true,
        loras: [],
        embeddings: [],
        controlnets: [],
        ip_adapter: [],
        image_encoder_weight_name: "pytorch_model.bin",
        image_size: "landscape_16_9",
        num_inference_steps: 30,
        guidance_scale: 7.5,
        timesteps: {
          method: "default",
          array: [],
        },
        sigmas: {
          method: "default",
          array: [],
        },
        prediction_type: "epsilon",
        image_format: "jpeg",
        num_images: 1,
        tile_width: 4096,
        tile_height: 4096,
        tile_stride_width: 2048,
        tile_stride_height: 2048,
        enable_safety_checker: true,
      },
      logs: true,
      onQueueUpdate: (update) => {
        if (update.status === "IN_PROGRESS") {
          if (update.logs && update.logs.length > 0) {
            update.logs.map((log) => log.message).forEach(console.log);
          }
          console.log("⏳ İşleniyor...");
        }
      },
    });
    endTimer(falTimer, { scene: sceneNumber, projectId: projectId });

    console.log("✅ Resim başarıyla üretildi!");

    // Fal.ai'den gelen resim URL'ini al
    const falImageUrl = result.data.images[0].url;
    console.log("🖼️ Fal.ai URL:", falImageUrl);

    // R2'ye yükle - süreyi ölç
    const imageId = generateId();
    const fileName = projectId
      ? `${projectId}_scene_${String(sceneNumber).padStart(
          3,
          "0"
        )}_${imageId}.jpg`
      : `${imageId}.jpg`;

    console.log("☁️ R2 CDN'e yükleniyor...");
    const r2Timer = startTimer("R2_IMAGE_UPLOAD");
    const cdnUrl = await r2Service.uploadFromUrl(
      falImageUrl,
      fileName,
      "image/jpeg"
    );
    endTimer(r2Timer, { scene: sceneNumber, projectId: projectId });

    console.log("\n🎉 ========== CDN URL ==========");
    console.log("🔗", cdnUrl);
    console.log("================================\n");

    return {
      images: result.data.images,
      falUrl: falImageUrl,
      cdnUrl: cdnUrl,
      prompt: promptData,
      requestId: result.requestId,
    };
  } catch (error) {
    console.error("❌ Fal.ai Hata Detayı:", error.message);
    console.error("❌ Hata Body:", error.body);
    throw error;
  }
}

/**
 * Mevcut modelleri döndürür
 * @returns {Array} Model listesi
 */
function getAvailableModels() {
  return [
    {
      id: "stabilityai/stable-diffusion-xl-base-1.0",
      name: "Stable Diffusion XL",
      description: "SDXL Base 1.0 - Yüksek kaliteli resim üretimi",
    },
  ];
}

module.exports = {
  generateImage,
  getAvailableModels,
};
