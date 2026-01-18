/**
 * Audio Service - Fal.ai TTS ile ses üretimi
 */
const { fal } = require("../config/fal.config");
const r2Service = require("./r2.service");
const { startTimer, endTimer } = require("../utils/timing");

/**
 * Benzersiz ID oluştur
 */
function generateId() {
  return `${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
}

/**
 * Fal.ai Chatterbox TTS ile ses üret ve R2'ye yükle
 * @param {object} params
 * @param {string} params.text - Seslendirme metni
 * @param {string} params.sceneId - Sahne ID
 * @param {string} params.voice - Ses tipi (default: walter)
 * @param {number} params.temperature - Temperature (default: 0.8)
 * @returns {Promise<object>}
 */
async function generateAudio({
  text,
  sceneId,
  voice = "walter",
  temperature = 0.8,
}) {
  console.log(`\n🎙️ ========== TTS GENERATION ==========`);
  console.log(`📝 Text: ${text.substring(0, 50)}...`);
  console.log(`🎤 Voice: ${voice}`);
  console.log(`🌡️ Temperature: ${temperature}`);
  console.log(`==========================================\n`);

  try {
    // Fal.ai TTS API çağrısını ölç
    const ttsTimer = startTimer("FAL_TTS_GENERATION");
    const result = await fal.subscribe(
      "fal-ai/chatterbox/text-to-speech/turbo",
      {
        input: {
          text: text,
          voice: voice,
          temperature: temperature,
        },
        logs: true,
        onQueueUpdate: (update) => {
          if (update.status === "IN_PROGRESS") {
            console.log("⏳ TTS işleniyor...");
          }
        },
      }
    );
    endTimer(ttsTimer, { scene: sceneId });

    console.log("✅ Ses başarıyla üretildi!");

    // Fal.ai'den gelen audio URL
    const falAudioUrl = result.data.audio_url || result.data.audio?.url;
    console.log("🔊 Fal.ai Audio URL:", falAudioUrl);

    // R2'ye yükle - süreyi ölç
    const audioId = generateId();
    const fileName = `audio/${sceneId}_${audioId}.mp3`;

    console.log("☁️ R2 CDN'e yükleniyor...");
    const r2Timer = startTimer("R2_AUDIO_UPLOAD");
    const cdnUrl = await r2Service.uploadFromUrl(
      falAudioUrl,
      fileName,
      "audio/mpeg"
    );
    endTimer(r2Timer, { scene: sceneId });

    console.log("\n🎉 ========== AUDIO CDN URL ==========");
    console.log("🔗", cdnUrl);
    console.log("======================================\n");

    // Ses süresini al (varsa)
    const duration =
      result.data.duration || result.data.audio?.duration || null;

    return {
      success: true,
      audioUrl: cdnUrl,
      falUrl: falAudioUrl,
      duration: duration,
      voice: voice,
      temperature: temperature,
      text: text,
    };
  } catch (error) {
    console.error("❌ TTS Hata:", error.message);
    console.error("❌ Hata Detay:", error.body);
    return {
      success: false,
      error: error.message,
    };
  }
}

/**
 * Mevcut ses seçeneklerini döndür
 */
function getAvailableVoices() {
  return [
    { id: "walter", name: "Walter", description: "Default erkek ses" },
    // Diğer sesler eklenebilir
  ];
}

module.exports = {
  generateAudio,
  getAvailableVoices,
};
