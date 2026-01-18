const projectService = require("../services/project.service");
const imageService = require("../services/image.service");
const videoService = require("../services/video.service");

/**
 * Yeni proje oluştur
 * POST /api/projects
 */
async function createProject(req, res) {
  try {
    const projectData = req.body;

    if (!projectData.title) {
      return res.status(400).json({ success: false, error: "Title gerekli" });
    }
    if (
      !projectData.scenes ||
      !Array.isArray(projectData.scenes) ||
      projectData.scenes.length === 0
    ) {
      return res
        .status(400)
        .json({ success: false, error: "Scenes array gerekli" });
    }

    for (const scene of projectData.scenes) {
      if (
        !scene.scene_number ||
        !scene.timestamp ||
        !scene.narration ||
        !scene.subject
      ) {
        return res.status(400).json({
          success: false,
          error:
            "Her sahne scene_number, timestamp, narration ve subject içermeli",
        });
      }
    }

    const project = await projectService.createProject(projectData);
    res.status(201).json({ success: true, project });
  } catch (error) {
    console.error("❌ Proje oluşturma hatası:", error);
    res.status(500).json({
      success: false,
      error: "Proje oluşturulurken hata oluştu",
      details: error.message,
    });
  }
}

/**
 * Tüm projeleri listele
 * GET /api/projects
 */
async function getAllProjects(req, res) {
  try {
    const projects = await projectService.getAllProjects();
    res.json({ success: true, projects });
  } catch (error) {
    console.error("❌ Proje listeleme hatası:", error);
    res
      .status(500)
      .json({ success: false, error: "Projeler listelenirken hata oluştu" });
  }
}

/**
 * Proje detaylarını getir
 * GET /api/projects/:id
 */
async function getProject(req, res) {
  try {
    const { id } = req.params;
    const project = await projectService.getProject(id);
    if (!project) {
      return res
        .status(404)
        .json({ success: false, error: "Proje bulunamadı" });
    }
    res.json({ success: true, project });
  } catch (error) {
    console.error("❌ Proje getirme hatası:", error);
    res
      .status(500)
      .json({ success: false, error: "Proje getirilirken hata oluştu" });
  }
}

/**
 * Proje istatistiklerini getir
 * GET /api/projects/:id/stats
 */
async function getProjectStats(req, res) {
  try {
    const { id } = req.params;
    const stats = await projectService.getProjectStats(id);
    res.json({ success: true, stats });
  } catch (error) {
    console.error("❌ İstatistik hatası:", error);
    res.status(500).json({
      success: false,
      error: "İstatistikler getirilirken hata oluştu",
    });
  }
}

/**
 * Projeyi sil
 * DELETE /api/projects/:id
 */
async function deleteProject(req, res) {
  try {
    const { id } = req.params;
    await projectService.deleteProject(id);
    res.json({ success: true, message: "Proje silindi" });
  } catch (error) {
    console.error("❌ Proje silme hatası:", error);
    res
      .status(500)
      .json({ success: false, error: "Proje silinirken hata oluştu" });
  }
}

/**
 * Tüm sahneler için görsel oluştur
 * POST /api/projects/:id/generate-all
 */
async function generateAllImages(req, res) {
  try {
    const { id } = req.params;
    const project = await projectService.getProject(id);

    if (!project) {
      return res
        .status(404)
        .json({ success: false, error: "Proje bulunamadı" });
    }

    // Proje durumunu güncelle
    await projectService.updateProjectStatus(id, "processing");

    // Pending sahneleri al
    const pendingScenes = project.scenes.filter((s) => s.status === "pending");

    if (pendingScenes.length === 0) {
      return res.json({
        success: true,
        message: "İşlenecek sahne yok",
        processed: 0,
      });
    }

    console.log(`\n🎬 ========== BATCH IMAGE GENERATION ==========`);
    console.log(`📁 Proje: ${project.title}`);
    console.log(`🎬 İşlenecek sahne: ${pendingScenes.length}`);
    console.log(`================================================\n`);

    let processed = 0;
    let failed = 0;

    // Sahneleri sırayla işle
    for (const scene of pendingScenes) {
      console.log(
        `\n📍 Sahne ${scene.sceneNumber}/${project.scenes.length} işleniyor...`
      );

      try {
        // Sahne durumunu güncelle
        await projectService.updateScene(scene.id, {
          status: "image_processing",
        });

        // Görsel oluştur - subject'i prompt olarak kullan
        const result = await imageService.generateImage({
          prompt: scene.subject,
          projectId: id,
          sceneNumber: scene.sceneNumber,
        });

        // Sahneyi güncelle
        await projectService.updateScene(scene.id, {
          status: "image_done",
          imageUrl: result.cdnUrl,
        });

        processed++;
        console.log(`✅ Sahne ${scene.sceneNumber} tamamlandı!`);
      } catch (error) {
        console.error(
          `❌ Sahne ${scene.sceneNumber} başarısız:`,
          error.message
        );
        await projectService.updateScene(scene.id, { status: "failed" });
        failed++;
      }
    }

    // Proje durumunu güncelle
    const finalStatus =
      failed === 0
        ? "completed"
        : failed === pendingScenes.length
        ? "failed"
        : "partial";
    await projectService.updateProjectStatus(id, finalStatus);

    console.log(`\n🎉 ========== BATCH TAMAMLANDI ==========`);
    console.log(`✅ Başarılı: ${processed}`);
    console.log(`❌ Başarısız: ${failed}`);
    console.log(`==========================================\n`);

    res.json({
      success: true,
      message: "Görsel oluşturma tamamlandı",
      processed,
      failed,
      total: pendingScenes.length,
    });
  } catch (error) {
    console.error("❌ Batch işlem hatası:", error);
    res.status(500).json({
      success: false,
      error: "Görsel oluşturma sırasında hata oluştu",
      details: error.message,
    });
  }
}

/**
 * Tüm sahneler için video oluştur (async - callback ile)
 * POST /api/projects/:id/generate-videos
 */
async function generateAllVideos(req, res) {
  try {
    const { id } = req.params;
    const { sync = false } = req.query; // ?sync=true ile senkron çalıştırılabilir

    const project = await projectService.getProject(id);

    if (!project) {
      return res
        .status(404)
        .json({ success: false, error: "Proje bulunamadı" });
    }

    // image_done durumundaki sahneleri al (resmi hazır, videosu yok)
    const readyScenes = project.scenes.filter(
      (s) => s.status === "image_done" && s.imageUrl && !s.videoUrl
    );

    if (readyScenes.length === 0) {
      return res.json({
        success: true,
        message: "Video üretilecek sahne yok (resmi hazır olanlar işlenecek)",
        processed: 0,
      });
    }

    console.log(`\n🎬 ========== VIDEO GENERATION ==========`);
    console.log(`📁 Proje: ${project.title}`);
    console.log(`🎬 İşlenecek sahne: ${readyScenes.length}`);
    console.log(`==========================================\n`);

    // Video service'i import et
    const videoService = require("../services/video.service");

    // Python API sağlık kontrolü
    const isHealthy = await videoService.checkPythonApiHealth();
    if (!isHealthy) {
      return res.status(503).json({
        success: false,
        error:
          "Python Video API erişilemez. Lütfen API'nin çalıştığından emin olun.",
      });
    }

    // Proje durumunu güncelle
    await projectService.updateProjectStatus(id, "video_processing");

    if (sync) {
      // Senkron mod - tüm videoları sırayla üret ve bekle
      let processed = 0;
      let failed = 0;

      for (const scene of readyScenes) {
        console.log(`\n📍 Sahne ${scene.sceneNumber} video üretiliyor...`);

        await projectService.updateScene(scene.id, {
          status: "video_processing",
        });

        const result = await videoService.generateVideoSync({
          imageUrl: scene.imageUrl,
          sceneId: scene.id,
          duration: 10,
          panDirection: "vertical",
          projectId: id,
          sceneNumber: scene.sceneNumber,
        });

        if (result.success) {
          await projectService.updateScene(scene.id, {
            videoUrl: result.videoUrl,
            status: "completed",
          });
          processed++;
          console.log(`✅ Sahne ${scene.sceneNumber} tamamlandı!`);
        } else {
          await projectService.updateScene(scene.id, {
            status: "video_failed",
          });
          failed++;
          console.log(`❌ Sahne ${scene.sceneNumber} başarısız!`);
        }
      }

      // Proje durumunu güncelle
      const finalStatus =
        failed === 0
          ? "completed"
          : failed === readyScenes.length
          ? "failed"
          : "partial";
      await projectService.updateProjectStatus(id, finalStatus);

      return res.json({
        success: true,
        message: "Video üretimi tamamlandı",
        processed,
        failed,
        total: readyScenes.length,
      });
    } else {
      // Async mod - istekleri gönder, callback bekle
      for (const scene of readyScenes) {
        await projectService.updateScene(scene.id, {
          status: "video_processing",
        });

        await videoService.requestVideoGeneration({
          imageUrl: scene.imageUrl,
          sceneId: scene.id,
          duration: 10,
          panDirection: "vertical",
          projectId: id,
          sceneNumber: scene.sceneNumber,
        });
      }

      return res.status(202).json({
        success: true,
        message: `${readyScenes.length} video üretimi başlatıldı. Tamamlandığında webhook ile bildirilecek.`,
        scenesProcessing: readyScenes.length,
      });
    }
  } catch (error) {
    console.error("❌ Video üretim hatası:", error);
    res.status(500).json({
      success: false,
      error: "Video üretimi sırasında hata oluştu",
      details: error.message,
    });
  }
}

/**
 * Tüm sahneler için ses oluştur
 * POST /api/projects/:id/generate-audio
 */
async function generateAllAudio(req, res) {
  try {
    const { id } = req.params;
    const { voice = "walter", temperature = 0.8 } = req.body;

    const project = await projectService.getProject(id);

    if (!project) {
      return res
        .status(404)
        .json({ success: false, error: "Proje bulunamadı" });
    }

    // Sesi olmayan sahneleri al
    const pendingScenes = project.scenes.filter(
      (s) => !s.audioUrl && s.narration
    );

    if (pendingScenes.length === 0) {
      return res.json({
        success: true,
        message: "Ses üretilecek sahne yok",
        processed: 0,
      });
    }

    console.log(`\n🎙️ ========== BATCH AUDIO GENERATION ==========`);
    console.log(`📁 Proje: ${project.title}`);
    console.log(`🎬 İşlenecek sahne: ${pendingScenes.length}`);
    console.log(`🎤 Voice: ${voice}`);
    console.log(`🌡️ Temperature: ${temperature}`);
    console.log(`================================================\n`);

    // Audio service
    const audioService = require("../services/audio.service");

    let processed = 0;
    let failed = 0;

    for (const scene of pendingScenes) {
      console.log(`\n📍 Sahne ${scene.sceneNumber} ses üretiliyor...`);

      try {
        // Sahne durumunu güncelle
        await projectService.updateScene(scene.id, {
          status: "audio_processing",
        });

        // Ses üret
        const result = await audioService.generateAudio({
          text: scene.narration,
          sceneId: scene.id,
          voice: voice,
          temperature: temperature,
          projectId: id,
          sceneNumber: scene.sceneNumber,
        });

        if (result.success) {
          // Sahneyi güncelle
          await projectService.updateScene(scene.id, {
            audioUrl: result.audioUrl,
            audioDuration: result.duration,
            audioVoice: voice,
            audioTemperature: temperature,
            status: "audio_done",
          });
          processed++;
          console.log(`✅ Sahne ${scene.sceneNumber} ses tamamlandı!`);
        } else {
          await projectService.updateScene(scene.id, {
            status: "audio_failed",
          });
          failed++;
          console.log(`❌ Sahne ${scene.sceneNumber} ses başarısız!`);
        }
      } catch (error) {
        console.error(`❌ Sahne ${scene.sceneNumber} hata:`, error.message);
        await projectService.updateScene(scene.id, { status: "audio_failed" });
        failed++;
      }
    }

    console.log(`\n🎉 ========== AUDIO BATCH TAMAMLANDI ==========`);
    console.log(`✅ Başarılı: ${processed}`);
    console.log(`❌ Başarısız: ${failed}`);
    console.log(`================================================\n`);

    res.json({
      success: true,
      message: "Ses üretimi tamamlandı",
      processed,
      failed,
      total: pendingScenes.length,
      voice,
      temperature,
    });
  } catch (error) {
    console.error("❌ Audio üretim hatası:", error);
    res.status(500).json({
      success: false,
      error: "Ses üretimi sırasında hata oluştu",
      details: error.message,
    });
  }
}

/**
 * Tüm sahneler için video + ses birleştir
 * POST /api/projects/:id/merge-videos
 */
async function mergeAllVideos(req, res) {
  try {
    const { id } = req.params;

    const project = await projectService.getProject(id);

    if (!project) {
      return res
        .status(404)
        .json({ success: false, error: "Proje bulunamadı" });
    }

    // Video ve sesi olan ama birleştirilmemiş sahneleri al
    const readyScenes = project.scenes.filter(
      (s) => s.videoUrl && s.audioUrl && !s.mergedVideoUrl
    );

    if (readyScenes.length === 0) {
      return res.json({
        success: true,
        message: "Birleştirilecek sahne yok (video ve ses gerekli)",
        processed: 0,
      });
    }

    console.log(`\n🔗 ========== VIDEO + SES BİRLEŞTİRME ==========`);
    console.log(`📁 Proje: ${project.title}`);
    console.log(`🎬 İşlenecek sahne: ${readyScenes.length}`);
    console.log(`================================================\n`);

    // Video service
    const videoService = require("../services/video.service");

    // Python API sağlık kontrolü
    const isHealthy = await videoService.checkPythonApiHealth();
    if (!isHealthy) {
      return res.status(503).json({
        success: false,
        error:
          "Python Video API erişilemez. Lütfen API'nin çalıştığından emin olun.",
      });
    }

    // Proje durumunu güncelle
    await projectService.updateProjectStatus(id, "merging");

    let processed = 0;
    let failed = 0;

    for (const scene of readyScenes) {
      console.log(`\n📍 Sahne ${scene.sceneNumber} birleştiriliyor...`);

      try {
        await projectService.updateScene(scene.id, {
          status: "merging",
        });

        const result = await videoService.mergeVideoWithAudio({
          videoUrl: scene.videoUrl,
          audioUrl: scene.audioUrl,
          sceneId: scene.id,
          narration: scene.narration, // Altyazı için metin
          projectId: id,
          sceneNumber: scene.sceneNumber,
        });

        if (result.success) {
          await projectService.updateScene(scene.id, {
            mergedVideoUrl: result.mergedVideoUrl,
            status: "merged",
          });
          processed++;
          console.log(`✅ Sahne ${scene.sceneNumber} birleştirildi!`);
        } else {
          await projectService.updateScene(scene.id, {
            status: "merge_failed",
          });
          failed++;
          console.log(`❌ Sahne ${scene.sceneNumber} birleştirme başarısız!`);
        }
      } catch (error) {
        console.error(`❌ Sahne ${scene.sceneNumber} hata:`, error.message);
        await projectService.updateScene(scene.id, { status: "merge_failed" });
        failed++;
      }
    }

    // Proje durumunu güncelle
    const finalStatus =
      failed === 0
        ? "completed"
        : failed === readyScenes.length
        ? "failed"
        : "partial";
    await projectService.updateProjectStatus(id, finalStatus);

    console.log(`\n🎉 ========== BİRLEŞTİRME TAMAMLANDI ==========`);
    console.log(`✅ Başarılı: ${processed}`);
    console.log(`❌ Başarısız: ${failed}`);
    console.log(`================================================\n`);

    res.json({
      success: true,
      message: "Video + Ses birleştirme tamamlandı",
      processed,
      failed,
      total: readyScenes.length,
    });
  } catch (error) {
    console.error("❌ Birleştirme hatası:", error);
    res.status(500).json({
      success: false,
      error: "Birleştirme sırasında hata oluştu",
      details: error.message,
    });
  }
}

/**
 * Tam pipeline - Resim → Ses → Video → Birleştirme
 * POST /api/projects/:id/generate-pipeline
 */
async function generateFullPipeline(req, res) {
  try {
    const { id } = req.params;
    const { voice = "walter", temperature = 0.8 } = req.body;

    const project = await projectService.getProject(id);

    if (!project) {
      return res
        .status(404)
        .json({ success: false, error: "Proje bulunamadı" });
    }

    console.log(`\n🚀 ========== TAM PIPELINE BAŞLATILIYOR ==========`);
    console.log(`📁 Proje: ${project.title}`);
    console.log(`🎬 Toplam sahne: ${project.scenes.length}`);
    console.log(`===================================================\n`);

    // Proje durumunu güncelle
    await projectService.updateProjectStatus(id, "pipeline_running");

    const results = {
      images: { processed: 0, failed: 0 },
      audio: { processed: 0, failed: 0 },
      videos: { processed: 0, failed: 0 },
      merge: { processed: 0, failed: 0 },
    };

    // ============ ADIM 1: GÖRSELLER ============
    console.log(`\n📍 ADIM 1/4: Görseller oluşturuluyor...`);
    const imageService = require("../services/image.service");
    const r2Service = require("../services/r2.service");

    const pendingImages = project.scenes.filter((s) => !s.imageUrl);
    for (const scene of pendingImages) {
      try {
        await projectService.updateScene(scene.id, { status: "processing" });
        const imageResult = await imageService.generateImage({
          prompt: scene.subject,
          projectId: id,
          sceneNumber: scene.sceneNumber,
        });

        if (imageResult && imageResult.cdnUrl) {
          await projectService.updateScene(scene.id, {
            imageUrl: imageResult.cdnUrl,
            status: "image_done",
          });
          results.images.processed++;
          console.log(`   ✅ Sahne ${scene.sceneNumber} görsel tamamlandı`);
        }
      } catch (error) {
        await projectService.updateScene(scene.id, { status: "failed" });
        results.images.failed++;
        console.log(`   ❌ Sahne ${scene.sceneNumber} görsel başarısız`);
      }
    }
    console.log(`✅ ADIM 1 TAMAMLANDI: ${results.images.processed} görsel`);

    // ============ ADIM 2: SESLER ============
    console.log(`\n📍 ADIM 2/4: Sesler oluşturuluyor...`);
    const audioService = require("../services/audio.service");

    // Güncel projeyi al
    const projectAfterImages = await projectService.getProject(id);
    const pendingAudio = projectAfterImages.scenes.filter(
      (s) => !s.audioUrl && s.narration
    );

    for (const scene of pendingAudio) {
      try {
        await projectService.updateScene(scene.id, {
          status: "audio_processing",
        });
        const audioResult = await audioService.generateAudio({
          text: scene.narration,
          sceneId: scene.id,
          voice,
          temperature,
          projectId: id,
          sceneNumber: scene.sceneNumber,
        });
        if (audioResult && audioResult.audioUrl) {
          await projectService.updateScene(scene.id, {
            audioUrl: audioResult.audioUrl,
            audioDuration: audioResult.duration,
            audioVoice: voice,
            audioTemperature: temperature,
            status: "audio_done",
          });
          results.audio.processed++;
          console.log(`   ✅ Sahne ${scene.sceneNumber} ses tamamlandı`);
        }
      } catch (error) {
        await projectService.updateScene(scene.id, { status: "audio_failed" });
        results.audio.failed++;
        console.log(`   ❌ Sahne ${scene.sceneNumber} ses başarısız`);
      }
    }
    console.log(`✅ ADIM 2 TAMAMLANDI: ${results.audio.processed} ses`);

    // ============ ADIM 3: VİDEOLAR ============
    console.log(`\n📍 ADIM 3/4: Videolar oluşturuluyor...`);
    const videoService = require("../services/video.service");

    // Python API kontrolü
    const isHealthy = await videoService.checkPythonApiHealth();
    if (!isHealthy) {
      console.log(`   ⚠️ Python API erişilemez, video adımı atlanıyor`);
    } else {
      const projectAfterAudio = await projectService.getProject(id);
      const pendingVideos = projectAfterAudio.scenes.filter(
        (s) => s.imageUrl && !s.videoUrl
      );

      for (const scene of pendingVideos) {
        try {
          await projectService.updateScene(scene.id, {
            status: "video_processing",
          });
          const videoResult = await videoService.generateVideoSync({
            imageUrl: scene.imageUrl,
            sceneId: scene.id,
            // Ses süresine göre video süresi (ses yoksa 10 saniye)
            duration: Math.ceil(scene.audioDuration) || 10,
            // Alternatif pan yönü: Tek sahneler yukarı, çift sahneler aşağı
            panDirection:
              scene.sceneNumber % 2 === 1 ? "vertical" : "vertical_reverse",
            projectId: id,
            sceneNumber: scene.sceneNumber,
          });
          if (videoResult.success) {
            await projectService.updateScene(scene.id, {
              videoUrl: videoResult.videoUrl,
              status: "video_done",
            });
            results.videos.processed++;
            console.log(`   ✅ Sahne ${scene.sceneNumber} video tamamlandı`);
          }
        } catch (error) {
          await projectService.updateScene(scene.id, {
            status: "video_failed",
          });
          results.videos.failed++;
          console.log(`   ❌ Sahne ${scene.sceneNumber} video başarısız`);
        }
      }
    }
    console.log(`✅ ADIM 3 TAMAMLANDI: ${results.videos.processed} video`);

    // ============ ADIM 4: BİRLEŞTİRME ============
    console.log(`\n📍 ADIM 4/4: Birleştirme yapılıyor...`);

    if (isHealthy) {
      const projectAfterVideos = await projectService.getProject(id);
      const pendingMerge = projectAfterVideos.scenes.filter(
        (s) => s.videoUrl && s.audioUrl && !s.mergedVideoUrl
      );

      for (const scene of pendingMerge) {
        try {
          await projectService.updateScene(scene.id, { status: "merging" });
          const mergeResult = await videoService.mergeVideoWithAudio({
            videoUrl: scene.videoUrl,
            audioUrl: scene.audioUrl,
            sceneId: scene.id,
            narration: scene.narration,
            projectId: id,
            sceneNumber: scene.sceneNumber,
          });
          if (mergeResult.success) {
            await projectService.updateScene(scene.id, {
              mergedVideoUrl: mergeResult.mergedVideoUrl,
              status: "completed",
            });
            results.merge.processed++;
            console.log(
              `   ✅ Sahne ${scene.sceneNumber} birleştirme tamamlandı`
            );
          }
        } catch (error) {
          await projectService.updateScene(scene.id, {
            status: "merge_failed",
          });
          results.merge.failed++;
          console.log(`   ❌ Sahne ${scene.sceneNumber} birleştirme başarısız`);
        }
      }
    }
    console.log(`✅ ADIM 4 TAMAMLANDI: ${results.merge.processed} birleştirme`);

    // ============ ADIM 5: FINAL VİDEO (TÜM SAHNELERİ BİRLEŞTİR) ============
    console.log(`\n📍 ADIM 5/5: Final video oluşturuluyor...`);

    // Güncel projeyi al
    const projectAfterMerge = await projectService.getProject(id);

    // Tüm mergedVideoUrl'leri sahne sırasına göre al
    const allMergedVideos = projectAfterMerge.scenes
      .filter((s) => s.mergedVideoUrl)
      .sort((a, b) => a.sceneNumber - b.sceneNumber)
      .map((s) => s.mergedVideoUrl);

    if (allMergedVideos.length > 0) {
      try {
        console.log(`   📦 ${allMergedVideos.length} video birleştirilecek`);

        const concatResult = await videoService.concatenateVideos({
          videoUrls: allMergedVideos,
          projectId: id,
        });

        if (concatResult.success) {
          // Proje'ye final video URL'sini kaydet
          await projectService.updateProject(id, {
            finalVideoUrl: concatResult.videoUrl,
          });
          console.log(
            `   ✅ Final video oluşturuldu: ${concatResult.videoUrl}`
          );
        } else {
          console.log(
            `   ⚠️ Final video oluşturulamadı: ${concatResult.error}`
          );
        }
      } catch (error) {
        console.log(`   ❌ Final video hatası: ${error.message}`);
      }
    } else {
      console.log(`   ⚠️ Birleştirilecek video yok, final video atlanıyor`);
    }

    console.log(`✅ ADIM 5 TAMAMLANDI`);

    // Proje durumunu güncelle
    await projectService.updateProjectStatus(id, "completed");

    console.log(`\n🎉 ========== PIPELINE TAMAMLANDI ==========`);
    console.log(
      `📊 Görseller: ${results.images.processed} başarılı, ${results.images.failed} başarısız`
    );
    console.log(
      `📊 Sesler: ${results.audio.processed} başarılı, ${results.audio.failed} başarısız`
    );
    console.log(
      `📊 Videolar: ${results.videos.processed} başarılı, ${results.videos.failed} başarısız`
    );
    console.log(
      `📊 Birleştirme: ${results.merge.processed} başarılı, ${results.merge.failed} başarısız`
    );
    console.log(`=============================================\n`);

    res.json({
      success: true,
      message: "Pipeline tamamlandı",
      results,
    });
  } catch (error) {
    console.error("❌ Pipeline hatası:", error);
    res.status(500).json({
      success: false,
      error: "Pipeline sırasında hata oluştu",
      details: error.message,
    });
  }
}

/**
 * Sadece Final Video Birleştirme (mevcut mergedVideoUrl'leri birleştir)
 * POST /api/projects/:id/concatenate-final
 */
async function concatenateFinalVideo(req, res) {
  try {
    const { id } = req.params;

    const project = await projectService.getProject(id);

    if (!project) {
      return res
        .status(404)
        .json({ success: false, error: "Proje bulunamadı" });
    }

    console.log(`\n🎬 ========== FINAL VIDEO BİRLEŞTİRME ==========`);
    console.log(`📁 Proje: ${project.title}`);
    console.log(`🎬 Toplam sahne: ${project.scenes.length}`);
    console.log(`================================================\n`);

    // Tüm mergedVideoUrl'leri sahne sırasına göre al
    const allMergedVideos = project.scenes
      .filter((s) => s.mergedVideoUrl)
      .sort((a, b) => a.sceneNumber - b.sceneNumber)
      .map((s) => s.mergedVideoUrl);

    if (allMergedVideos.length === 0) {
      return res.status(400).json({
        success: false,
        error: "Birleştirilecek video bulunamadı. Önce sahneleri birleştirin.",
      });
    }

    console.log(`📦 ${allMergedVideos.length} video birleştirilecek`);

    const concatResult = await videoService.concatenateVideos({
      videoUrls: allMergedVideos,
      projectId: id,
    });

    if (concatResult.success) {
      await projectService.updateProject(id, {
        finalVideoUrl: concatResult.videoUrl,
      });

      console.log(`✅ Final video oluşturuldu: ${concatResult.videoUrl}`);

      return res.json({
        success: true,
        message: "Final video başarıyla oluşturuldu",
        finalVideoUrl: concatResult.videoUrl,
      });
    } else {
      return res.status(500).json({
        success: false,
        error: concatResult.error || "Final video oluşturulamadı",
      });
    }
  } catch (error) {
    console.error("❌ Concat hatası:", error);
    res.status(500).json({
      success: false,
      error: "Final video birleştirme sırasında hata oluştu",
      details: error.message,
    });
  }
}

module.exports = {
  createProject,
  getAllProjects,
  getProject,
  getProjectStats,
  deleteProject,
  generateAllImages,
  generateAllVideos,
  generateAllAudio,
  mergeAllVideos,
  generateFullPipeline,
  concatenateFinalVideo,
};
