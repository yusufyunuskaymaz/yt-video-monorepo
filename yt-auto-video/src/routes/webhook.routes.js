/**
 * Webhook Routes - Python'dan gelen callback'ler
 */
const express = require("express");
const router = express.Router();
const webhookController = require("../controllers/webhook.controller");

// POST /webhook/video-ready - Video hazır callback
router.post("/video-ready", webhookController.videoReady);

module.exports = router;
