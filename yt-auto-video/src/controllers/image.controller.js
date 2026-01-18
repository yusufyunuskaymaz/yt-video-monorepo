const imageService = require("../services/image.service");

/**
 * Resim üretme endpoint'i
 * POST /api/generate
 */
async function generate(req, res) {
  try {
    const { prompt, width, height, model } = req.body;

    if (!prompt) {
      return res.status(400).json({
        success: false,
        error: "Prompt gerekli!",
      });
    }

    const result = await imageService.generateImage({
      prompt,
      width: width || 1024,
      height: height || 1024,
    });

    res.json({
      success: true,
      ...result,
    });
  } catch (error) {
    console.error("❌ Hata:", error);
    res.status(500).json({
      success: false,
      error: "Resim üretilirken hata oluştu",
      details: error.message,
    });
  }
}

/**
 * Mevcut modelleri listele
 * GET /api/models
 */
function getModels(req, res) {
  const models = imageService.getAvailableModels();
  res.json({
    success: true,
    models,
  });
}

module.exports = {
  generate,
  getModels,
};
