const { fal } = require("@fal-ai/client");

// Fal.ai API yapılandırması
fal.config({
  credentials: process.env.FAL_AI_API_KEY,
});

module.exports = { fal };
