const express = require("express");
const router = express.Router();
const imageController = require("../controllers/image.controller");

// POST /api/generate - Resim üret
router.post("/generate", imageController.generate);

// GET /api/models - Modelleri listele
router.get("/models", imageController.getModels);

module.exports = router;
