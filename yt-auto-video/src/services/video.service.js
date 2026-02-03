/**
 * Video Service - Python API ile iletişim
 */
const axios = require("axios");

// Python API URL (aynı sunucuda)
const PYTHON_API_URL = process.env.PYTHON_API_URL || "http://localhost:8000";
// Node.js callback URL
const NODE_CALLBACK_URL =
  process.env.NODE_CALLBACK_URL || "http://localhost:3000/webhook/video-ready";

/**
 * Python API'ye video üretim isteği gönder (async - callback ile)
 * @param {object} params - { imageUrl, sceneId, duration, panDirection, subtitles }
 * @returns {Promise<object>}
 */
async function requestVideoGeneration({
  imageUrl,
  sceneId,
  duration = 10,
  panDirection = "vertical",
  subtitles = null,
  projectId = null,
  sceneNumber = null,
}) {
  console.log(`\n🎬 Video üretim isteği gönderiliyor...`);
  console.log(`   Scene ID: ${sceneId}`);
  console.log(`   Image URL: ${imageUrl}`);
  console.log(`   Duration: ${duration}s`);
  console.log(`   Direction: ${panDirection}`);
  if (projectId) console.log(`   Project ID: ${projectId}`);

  try {
    const response = await axios.post(`${PYTHON_API_URL}/api/video/generate`, {
      image_url: imageUrl,
      scene_id: sceneId,
      duration: duration,
      pan_direction: panDirection,
      subtitles: subtitles,
      callback_url: `${NODE_CALLBACK_URL}`,
      project_id: projectId,
      scene_number: sceneNumber,
    });

    console.log(`✅ Video üretim isteği gönderildi!`);
    return {
      success: true,
      message: response.data.message,
      sceneId: sceneId,
    };
  } catch (error) {
    console.error(`❌ Video üretim isteği hatası:`, error.message);
    return {
      success: false,
      error: error.message,
      sceneId: sceneId,
    };
  }
}

/**
 * Python API'ye video üretim isteği gönder (sync - bekle ve döndür)
 * Test için kullanılır
 * @param {object} params
 * @returns {Promise<object>}
 */
async function generateVideoSync({
  imageUrl,
  sceneId,
  duration = 10,
  panDirection = "vertical",
  subtitles = null,
  projectId = null,
  sceneNumber = null,
}) {
  console.log(`\n🎬 Video üretimi başlatılıyor (sync)...`);

  try {
    const response = await axios.post(
      `${PYTHON_API_URL}/api/video/generate-sync`,
      {
        image_url: imageUrl,
        scene_id: sceneId,
        duration: duration,
        pan_direction: panDirection,
        subtitles: subtitles,
        project_id: projectId,
        scene_number: sceneNumber,
      },
      { timeout: 180000 } // 3 dakika timeout
    );

    console.log(`✅ Video üretildi: ${response.data.video_url}`);
    return {
      success: response.data.success,
      videoUrl: response.data.video_url,
      sceneId: response.data.scene_id,
      duration: response.data.duration,
    };
  } catch (error) {
    console.error(`❌ Video üretim hatası:`, error.message);
    return {
      success: false,
      error: error.message,
      sceneId: sceneId,
    };
  }
}

/**
 * Python API sağlık kontrolü
 * @returns {Promise<boolean>}
 */
async function checkPythonApiHealth() {
  try {
    const response = await axios.get(`${PYTHON_API_URL}/api/video/health`, {
      timeout: 5000,
    });
    return response.data.status === "ok";
  } catch (error) {
    console.error(`❌ Python API erişilemez:`, error.message);
    return false;
  }
}

/**
 * Video ve sesi birleştir
 * @param {object} params - { videoUrl, audioUrl, sceneId, narration }
 * @returns {Promise<object>}
 */
async function mergeVideoWithAudio({
  videoUrl,
  audioUrl,
  sceneId,
  narration = null,
  projectId = null,
  sceneNumber = null,
}) {
  console.log(`\n🔗 Video + Ses birleştirme isteği gönderiliyor...`);
  console.log(`   Scene ID: ${sceneId}`);
  console.log(`   Video URL: ${videoUrl}`);
  console.log(`   Audio URL: ${audioUrl}`);
  console.log(`   Altyazı: ${narration ? "Var" : "Yok"}`);

  try {
    const response = await axios.post(
      `${PYTHON_API_URL}/api/video/merge-video-audio`,
      {
        video_url: videoUrl,
        audio_url: audioUrl,
        scene_id: sceneId,
        narration: narration,
        project_id: projectId,
        scene_number: sceneNumber,
      },
      { timeout: 600000 } // 10 dakika timeout (altyazı ekleme uzun sürebilir)
    );

    if (response.data.success) {
      console.log(
        `✅ Birleştirme tamamlandı: ${response.data.merged_video_url}`
      );
      return {
        success: true,
        mergedVideoUrl: response.data.merged_video_url,
        sceneId: response.data.scene_id,
        duration: response.data.duration,
      };
    } else {
      console.error(`❌ Birleştirme başarısız:`, response.data.error);
      return {
        success: false,
        error: response.data.error,
        sceneId: sceneId,
      };
    }
  } catch (error) {
    console.error(`❌ Birleştirme hatası:`, error.message);
    return {
      success: false,
      error: error.message,
      sceneId: sceneId,
    };
  }
}

/**
 * Birden fazla videoyu tek videoya birleştir
 * @param {object} params - { videoUrls, projectId }
 * @returns {Promise<object>}
 */
async function concatenateVideos({ videoUrls, projectId }) {
  console.log(`\n🎬 Video birleştirme (concat) isteği gönderiliyor...`);
  console.log(`   Project ID: ${projectId}`);
  console.log(`   Video sayısı: ${videoUrls.length}`);

  try {
    const response = await axios.post(
      `${PYTHON_API_URL}/api/video/concatenate`,
      {
        video_urls: videoUrls,
        project_id: projectId,
      },
      { timeout: 900000 } // 15 dakika timeout (çok video olabilir)
    );

    if (response.data.success) {
      console.log(`✅ Concat tamamlandı: ${response.data.video_url}`);
      return {
        success: true,
        videoUrl: response.data.video_url,
        projectId: response.data.project_id,
      };
    } else {
      console.error(`❌ Concat başarısız:`, response.data.error);
      return {
        success: false,
        error: response.data.error,
        projectId: projectId,
      };
    }
  } catch (error) {
    console.error(`❌ Concat hatası:`, error.message);
    return {
      success: false,
      error: error.message,
      projectId: projectId,
    };
  }
}

/**
 * GPU Test - Hazır videoları birleştirip GPU performansını test et
 * @param {object} params - { videoUrls, targetDurationSeconds, testName }
 * @returns {Promise<object>}
 */
async function gpuTest({
  videoUrls,
  targetDurationSeconds = 900,
  testName = "gpu_test",
}) {
  console.log(`\n🧪 GPU Test isteği gönderiliyor...`);
  console.log(`   Video sayısı: ${videoUrls.length}`);
  console.log(
    `   Hedef süre: ${targetDurationSeconds}s (${
      targetDurationSeconds / 60
    } dk)`
  );
  console.log(`   Test adı: ${testName}`);

  try {
    const response = await axios.post(
      `${PYTHON_API_URL}/api/video/gpu-test`,
      {
        video_urls: videoUrls,
        target_duration_seconds: targetDurationSeconds,
        test_name: testName,
      },
      { timeout: 3600000 } // 1 saat timeout (uzun videolar için)
    );

    if (response.data.success) {
      console.log(`✅ GPU Test tamamlandı: ${response.data.video_url}`);
      console.log(
        `   📊 Metrics:`,
        JSON.stringify(response.data.metrics, null, 2)
      );
      return {
        success: true,
        video_url: response.data.video_url,
        test_name: response.data.test_name,
        metrics: response.data.metrics,
      };
    } else {
      console.error(`❌ GPU Test başarısız:`, response.data.error);
      return {
        success: false,
        error: response.data.error,
        metrics: response.data.metrics,
      };
    }
  } catch (error) {
    console.error(`❌ GPU Test hatası:`, error.message);
    return {
      success: false,
      error: error.message,
    };
  }
}

module.exports = {
  requestVideoGeneration,
  generateVideoSync,
  checkPythonApiHealth,
  mergeVideoWithAudio,
  concatenateVideos,
  gpuTest,
  PYTHON_API_URL,
  NODE_CALLBACK_URL,
};
