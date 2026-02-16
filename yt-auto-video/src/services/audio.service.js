/**
 * Audio Service - Fal.ai Chatterbox Multilingual TTS ile ses üretimi
 * Türkçe dahil 23 dil destekler
 */
const { fal } = require("../config/fal.config");
const r2Service = require("./r2.service");
const { startTimer, endTimer } = require("../utils/timing");

const PYTHON_API_URL = process.env.PYTHON_API_URL || "http://localhost:8000";

/**
 * Benzersiz ID oluştur
 */
function generateId() {
  return `${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
}

/**
 * Fal.ai Chatterbox Multilingual TTS ile ses üret
 *
 * @param {object} params
 * @param {string} params.text - Seslendirme metni (max 300 karakter)
 * @param {string} params.voice - Dil (default: turkish)
 * @param {number} params.temperature - Temperature (default: 0.8)
 * @returns {Promise<object>}
 */
async function generateAudio({
  text,
  sceneId,
  voice = "turkish",
  temperature = 0.8,
  projectId = null,
  sceneNumber = null,
}) {
  const language = voice;

  console.log(`\n🎙️ ========== TTS GENERATION (Multilingual) ==========`);
  console.log(`📝 Text: ${text.substring(0, 80)}...`);
  console.log(`🌍 Dil: ${language}`);
  console.log(`🌡️ Temperature: ${temperature}`);
  console.log(`======================================================\n`);

  try {
    const ttsTimer = startTimer("FAL_TTS_GENERATION");

    const result = await fal.subscribe(
      "fal-ai/chatterbox/text-to-speech/multilingual",
      {
        input: {
          text: text,
          voice: language,
          temperature: temperature,
          exaggeration: 0.5,
          cfg_scale: 0.5,
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

    const falAudioUrl = result.data.audio?.url || result.data.audio_url;
    console.log("🔊 Fal.ai Audio URL:", falAudioUrl);

    // Eğer projectId varsa, RunPod'a indir (lokal path)
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
            filename: `audio_scene_${String(sceneNumber).padStart(3, "0")}.wav`,
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
          duration: null,
          voice: language,
          temperature: temperature,
          text: text,
        };
      }
    }

    // Fallback: R2'ye yükle (projectId yoksa)
    const audioId = generateId();
    const fileName = `audio/${sceneId}_${audioId}.wav`;

    console.log("☁️ R2 CDN'e yükleniyor...");
    const r2Timer = startTimer("R2_AUDIO_UPLOAD");
    const cdnUrl = await r2Service.uploadFromUrl(
      falAudioUrl,
      fileName,
      "audio/wav"
    );
    endTimer(r2Timer, { scene: sceneNumber, projectId: projectId });

    console.log("\n🎉 ========== AUDIO CDN URL ==========");
    console.log("🔗", cdnUrl);
    console.log("======================================\n");

    return {
      success: true,
      audioUrl: cdnUrl,
      falUrl: falAudioUrl,
      duration: null,
      voice: language,
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
 * Desteklenen dilleri döndür
 */
function getAvailableVoices() {
  return [
    { id: "turkish", name: "Türkçe", description: "Türkçe seslendirme" },
    { id: "english", name: "English", description: "İngilizce seslendirme" },
    { id: "german", name: "Deutsch", description: "Almanca seslendirme" },
    { id: "french", name: "Français", description: "Fransızca seslendirme" },
    { id: "spanish", name: "Español", description: "İspanyolca seslendirme" },
    { id: "arabic", name: "العربية", description: "Arapça seslendirme" },
  ];
}

module.exports = {
  generateAudio,
  getAvailableVoices,
};
