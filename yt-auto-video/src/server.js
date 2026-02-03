require("dotenv").config();

const app = require("./app");

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log("🚀 ================================");
  console.log(`🚀 Sunucu http://localhost:${PORT} adresinde çalışıyor`);
  console.log("🚀 ================================");
  console.log("");
  console.log("📝 API Endpoints:");
  console.log(`   POST /api/generate - Resim üret`);
  console.log(`   GET  /api/models   - Modelleri listele`);
  console.log("");
});