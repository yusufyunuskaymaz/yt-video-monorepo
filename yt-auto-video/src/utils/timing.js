/**
 * Performance Timing Logger
 * Tüm işlemlerin süresini dosyaya kaydeder
 */
const fs = require("fs");
const path = require("path");

const LOG_FILE = path.join(__dirname, "../../logs/performance.log");

// Log dizinini oluştur
const logDir = path.dirname(LOG_FILE);
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

/**
 * Süre ölçümü başlat
 * @param {string} operation - İşlem adı
 * @returns {object} Timer objesi
 */
function startTimer(operation) {
  return {
    operation,
    startTime: Date.now(),
    startHr: process.hrtime.bigint(),
  };
}

/**
 * Süre ölçümünü bitir ve logla
 * @param {object} timer - startTimer'dan dönen obje
 * @param {object} metadata - Ek bilgiler (opsiyonel)
 */
function endTimer(timer, metadata = {}) {
  const endTime = Date.now();
  const durationMs = endTime - timer.startTime;
  const durationSec = (durationMs / 1000).toFixed(2);

  const logEntry = {
    timestamp: new Date().toISOString(),
    operation: timer.operation,
    duration_ms: durationMs,
    duration_sec: parseFloat(durationSec),
    ...metadata,
  };

  // Console'a yaz
  console.log(`⏱️ [${timer.operation}] ${durationSec}s`);

  // Dosyaya yaz
  const logLine = JSON.stringify(logEntry) + "\n";
  fs.appendFileSync(LOG_FILE, logLine);

  return logEntry;
}

/**
 * Async fonksiyonu ölç ve logla
 * @param {string} operation - İşlem adı
 * @param {Function} asyncFn - Ölçülecek async fonksiyon
 * @param {object} metadata - Ek bilgiler
 * @returns {any} Fonksiyonun dönüş değeri
 */
async function measureAsync(operation, asyncFn, metadata = {}) {
  const timer = startTimer(operation);
  try {
    const result = await asyncFn();
    endTimer(timer, { ...metadata, status: "success" });
    return result;
  } catch (error) {
    endTimer(timer, { ...metadata, status: "error", error: error.message });
    throw error;
  }
}

/**
 * Log dosyasını temizle
 */
function clearLog() {
  fs.writeFileSync(LOG_FILE, "");
  console.log("📋 Performance log temizlendi");
}

/**
 * Log dosyasını oku ve özet çıkar
 * @returns {object} Özet istatistikler
 */
function getSummary() {
  if (!fs.existsSync(LOG_FILE)) {
    return { operations: [] };
  }

  const content = fs.readFileSync(LOG_FILE, "utf-8");
  const lines = content
    .trim()
    .split("\n")
    .filter((l) => l);
  const entries = lines.map((l) => JSON.parse(l));

  // İşlem bazlı gruplama
  const byOperation = {};
  entries.forEach((entry) => {
    if (!byOperation[entry.operation]) {
      byOperation[entry.operation] = {
        count: 0,
        total_ms: 0,
        min_ms: Infinity,
        max_ms: 0,
        avg_ms: 0,
      };
    }
    const op = byOperation[entry.operation];
    op.count++;
    op.total_ms += entry.duration_ms;
    op.min_ms = Math.min(op.min_ms, entry.duration_ms);
    op.max_ms = Math.max(op.max_ms, entry.duration_ms);
  });

  // Ortalama hesapla
  Object.values(byOperation).forEach((op) => {
    op.avg_ms = Math.round(op.total_ms / op.count);
    op.avg_sec = (op.avg_ms / 1000).toFixed(2);
    op.min_sec = (op.min_ms / 1000).toFixed(2);
    op.max_sec = (op.max_ms / 1000).toFixed(2);
  });

  return {
    total_entries: entries.length,
    operations: byOperation,
  };
}

module.exports = {
  startTimer,
  endTimer,
  measureAsync,
  clearLog,
  getSummary,
  LOG_FILE,
};
