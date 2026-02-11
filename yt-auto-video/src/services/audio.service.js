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
  projectId = null,
  sceneNumber = null,
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
    endTimer(ttsTimer, { scene: sceneNumber, projectId: projectId });

    console.log("✅ Ses başarıyla üretildi!");

    // Fal.ai'den gelen audio URL
    const falAudioUrl = result.data.audio_url || result.data.audio?.url;
    console.log("🔊 Fal.ai Audio URL:", falAudioUrl);

    // Ses süresini al (varsa)
    const duration =
      result.data.duration || result.data.audio?.duration || null;

    // Eğer projectId varsa, RunPod'daki /tmp/projects/{id}/ dizinine indir
    const PYTHON_API_URL =
      process.env.PYTHON_API_URL || "http://localhost:8000";
    if (projectId) {
      console.log("📥 Audio RunPod'a indiriliyor...");
      const downloadTimer = startTimer("AUDIO_DOWNLOAD_TO_RUNPOD");

      const dlResponse = await fetch(
        `${PYTHON_API_URL}/api/video/download-to-local`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url: falAudioUrl,
            project_id: String(projectId),
            filename: `audio_scene_${String(sceneNumber).padStart(3, "0")}.mp3`,
          }),
        }
      );

      const dlResult = await dlResponse.json();
      endTimer(downloadTimer, { scene: sceneNumber, projectId: projectId });

      if (dlResult.success) {
        console.log("📂 Lokal:", dlResult.local_path);
        return {
          success: true,
          audioUrl: dlResult.local_path,
          localPath: dlResult.local_path,
          falUrl: falAudioUrl,
          duration: duration,
          voice: voice,
          temperature: temperature,
          text: text,
        };
      }
    }

    // Fallback: R2'ye yükle (projectId yoksa)
    const audioId = generateId();
    const fileName = `audio/${sceneId}_${audioId}.mp3`;

    console.log("☁️ R2 CDN'e yükleniyor...");
    const r2Timer = startTimer("R2_AUDIO_UPLOAD");
    const cdnUrl = await r2Service.uploadFromUrl(
      falAudioUrl,
      fileName,
      "audio/mpeg"
    );
    endTimer(r2Timer, { scene: sceneNumber, projectId: projectId });

    console.log("\n🎉 ========== AUDIO CDN URL ==========");
    console.log("🔗", cdnUrl);
    console.log("======================================\n");

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
