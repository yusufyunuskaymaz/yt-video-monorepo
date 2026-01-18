/**
 * Webhook Controller - Python'dan gelen callback'leri işle
 */
const projectService = require("../services/project.service");

/**
 * Video hazır olduğunda Python'dan gelen callback
 * POST /webhook/video-ready
 */
async function videoReady(req, res) {
  try {
    const { scene_id, status, video_url, error } = req.body;

    console.log(`\n📥 ========== VIDEO WEBHOOK ==========`);
    console.log(`   Scene ID: ${scene_id}`);
    console.log(`   Status: ${status}`);
    console.log(`   Video URL: ${video_url || "N/A"}`);
    if (error) console.log(`   Error: ${error}`);
    console.log(`======================================\n`);

    if (!scene_id) {
      return res
        .status(400)
        .json({ success: false, error: "scene_id gerekli" });
    }

    // Sahneyi güncelle
    if (status === "completed" && video_url) {
      await projectService.updateScene(scene_id, {
        videoUrl: video_url,
        status: "completed",
      });
      console.log(`✅ Sahne güncellendi: ${scene_id} -> completed`);

      // Projenin tüm sahnelerinin durumunu kontrol et
      await checkProjectCompletion(scene_id);
    } else if (status === "failed") {
      await projectService.updateScene(scene_id, {
        status: "video_failed",
      });
      console.log(`❌ Sahne video üretimi başarısız: ${scene_id}`);
    }

    res.json({ success: true, message: "Webhook alındı" });
  } catch (error) {
    console.error("❌ Webhook hatası:", error);
    res.status(500).json({ success: false, error: error.message });
  }
}

/**
 * Projenin tüm sahnelerinin tamamlanıp tamamlanmadığını kontrol et
 * @param {string} sceneId
 */
async function checkProjectCompletion(sceneId) {
  try {
    // Sahnenin projesini bul
    const scene = await projectService.getSceneById(sceneId);
    if (!scene) return;

    const projectId = scene.projectId;
    const stats = await projectService.getProjectStats(projectId);

    console.log(
      `📊 Proje durumu: ${stats.completed}/${stats.total} tamamlandı`
    );

    // Tüm sahneler tamamlandıysa projeyi güncelle
    if (stats.completed === stats.total) {
      await projectService.updateProjectStatus(projectId, "completed");
      console.log(`🎉 Proje tamamlandı: ${projectId}`);
    } else if (
      stats.failed > 0 &&
      stats.completed + stats.failed === stats.total
    ) {
      await projectService.updateProjectStatus(projectId, "partial");
      console.log(`⚠️ Proje kısmen tamamlandı: ${projectId}`);
    }
  } catch (error) {
    console.error("❌ Proje kontrol hatası:", error);
  }
}

module.exports = {
  videoReady,
};
