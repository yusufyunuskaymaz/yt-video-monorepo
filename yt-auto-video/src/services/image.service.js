const { startTimer, endTimer } = require("../utils/timing");

// FLUX API URL (RunPod'daki ayrı servis)
const FLUX_API_URL = process.env.FLUX_API_URL || "http://localhost:8888";

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
 * FLUX API ile resim üretir (CDN upload Python tarafında yapılır)
 * @param {object} promptData - Prompt verisi (subject string veya obje)
 * @param {string} projectId - Proje ID (opsiyonel, dosya adı için)
 * @param {number} sceneNumber - Sahne numarası (opsiyonel, dosya adı için)
 * @returns {Promise<Object>} Üretilen resim bilgileri
 */
async function generateImage({ prompt: promptData, projectId, sceneNumber }) {
  console.log("🎨 Resim üretiliyor (FLUX)...");

  // Subject'i al ve sabit stil ile birleştir
  const subject =
    typeof promptData === "string"
      ? promptData
      : promptData.subject || promptData;
  const fullPrompt = buildPromptFromTemplate(subject);

  console.log("📝 Subject:", subject);
  console.log("🎨 Stil: THICK IMPASTO gouache painting");
  console.log("🔗 FLUX API:", FLUX_API_URL);

  try {
    const fluxTimer = startTimer("FLUX_IMAGE_GENERATION");

    const response = await fetch(`${FLUX_API_URL}/generate-image`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: fullPrompt,
        num_inference_steps: 4,
        width: 1920,
        height: 1080,
        upload_to_cdn: true,
        project_id: projectId ? String(projectId) : null,
        scene_number: sceneNumber || null,
      }),
    });

    const result = await response.json();
    endTimer(fluxTimer, { scene: sceneNumber, projectId: projectId });

    if (!result.success) {
      throw new Error(result.error || "FLUX API hatası");
    }

    console.log("✅ Resim başarıyla üretildi!");
    console.log(`⏱️ Süre: ${result.generation_time}s`);

    console.log("\n🎉 ========== CDN URL ==========");
    console.log("🔗", result.cdn_url);
    console.log("================================\n");

    return {
      cdnUrl: result.cdn_url,
      prompt: promptData,
      generationTime: result.generation_time,
      filename: result.filename,
    };
  } catch (error) {
    console.error("❌ FLUX API Hata:", error.message);
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
      id: "black-forest-labs/FLUX.1-schnell",
      name: "FLUX.1 Schnell",
      description: "Hızlı yüksek kaliteli resim üretimi",
    },
  ];
}

module.exports = {
  generateImage,
  getAvailableModels,
};
