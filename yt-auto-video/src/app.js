const express = require("express");
const cors = require("cors");
const path = require("path");

const routes = require("./routes");
const webhookRoutes = require("./routes/webhook.routes");

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Static files - Frontend
app.use(express.static(path.join(__dirname, "../public")));

// Webhook Routes (Python callback için)
app.use("/webhook", webhookRoutes);

// API Routes
app.use("/api", routes);

// Ana sayfa
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "../public", "index.html"));
});

// 404 Handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: "Endpoint bulunamadı",
  });
});

// Error Handler
app.use((err, req, res, next) => {
  console.error("❌ Server Error:", err);
  res.status(500).json({
    success: false,
    error: "Sunucu hatası",
    details: err.message,
  });
});

module.exports = app;
