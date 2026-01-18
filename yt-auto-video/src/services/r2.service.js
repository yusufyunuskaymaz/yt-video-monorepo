const { S3Client, PutObjectCommand } = require("@aws-sdk/client-s3");
const fs = require("fs");
const path = require("path");
const https = require("https");
const http = require("http");

// R2 Client
const client = new S3Client({
  region: "auto",
  endpoint: process.env.R2_ENDPOINT,
  credentials: {
    accessKeyId: process.env.R2_ACCESS_KEY_ID,
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
  },
});

const bucket = process.env.R2_BUCKET_NAME;
const publicUrl = process.env.R2_PUBLIC_URL;

/**
 * URL'den dosyayı indir
 * @param {string} url - İndirilecek URL
 * @param {string} dest - Hedef dosya yolu
 * @returns {Promise<void>}
 */
function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    const protocol = url.startsWith("https") ? https : http;

    protocol
      .get(url, (response) => {
        if (response.statusCode === 302 || response.statusCode === 301) {
          // Redirect
          downloadFile(response.headers.location, dest)
            .then(resolve)
            .catch(reject);
          return;
        }

        response.pipe(file);
        file.on("finish", () => {
          file.close();
          resolve();
        });
      })
      .on("error", (err) => {
        fs.unlink(dest, () => {});
        reject(err);
      });
  });
}

/**
 * Dosyayı R2'ye yükle
 * @param {string} filepath - Yerel dosya yolu
 * @param {string} key - R2 key (dosya adı)
 * @param {string} contentType - MIME type
 * @returns {Promise<string>} Public URL
 */
async function uploadFile(filepath, key, contentType = "image/jpeg") {
  console.log(`\n========== R2 UPLOAD ==========`);
  console.log(`📁 Dosya: ${filepath}`);
  console.log(`🔑 Key: ${key}`);
  console.log(`🪣 Bucket: ${bucket}`);

  if (!fs.existsSync(filepath)) {
    console.log(`❌ HATA: Dosya bulunamadı!`);
    throw new Error(`Dosya bulunamadı: ${filepath}`);
  }

  const fileBuffer = fs.readFileSync(filepath);
  const sizeMB = (fileBuffer.length / (1024 * 1024)).toFixed(2);
  console.log(`📦 Dosya boyutu: ${sizeMB} MB`);
  console.log(`☁️ R2'ye yükleniyor...`);

  try {
    await client.send(
      new PutObjectCommand({
        Bucket: bucket,
        Key: key,
        Body: fileBuffer,
        ContentType: contentType,
      })
    );

    const url = `${publicUrl}/${encodeURIComponent(key)}`;
    console.log(`✅ R2 BAŞARILI!`);
    console.log(`🔗 URL: ${url}`);
    console.log(`================================\n`);

    return url;
  } catch (error) {
    console.log(`❌ R2 HATA: ${error.message}`);
    console.log(`================================\n`);
    throw error;
  }
}

/**
 * Buffer'ı R2'ye yükle
 * @param {Buffer} buffer - Dosya içeriği
 * @param {string} key - R2 key
 * @param {string} contentType - MIME type
 * @returns {Promise<string>} Public URL
 */
async function uploadBuffer(buffer, key, contentType = "image/jpeg") {
  console.log(`\n========== R2 UPLOAD (Buffer) ==========`);
  console.log(`🔑 Key: ${key}`);
  console.log(`🪣 Bucket: ${bucket}`);
  console.log(`📦 Boyut: ${(buffer.length / 1024).toFixed(2)} KB`);
  console.log(`☁️ R2'ye yükleniyor...`);

  try {
    await client.send(
      new PutObjectCommand({
        Bucket: bucket,
        Key: key,
        Body: buffer,
        ContentType: contentType,
      })
    );

    const url = `${publicUrl}/${encodeURIComponent(key)}`;
    console.log(`✅ R2 BAŞARILI!`);
    console.log(`🔗 URL: ${url}`);
    console.log(`================================\n`);

    return url;
  } catch (error) {
    console.log(`❌ R2 HATA: ${error.message}`);
    console.log(`================================\n`);
    throw error;
  }
}

/**
 * URL'den dosyayı indir ve R2'ye yükle
 * @param {string} imageUrl - Kaynak URL
 * @param {string} key - R2 key
 * @param {string} contentType - MIME type
 * @returns {Promise<string>} Public URL
 */
async function uploadFromUrl(imageUrl, key, contentType = "image/jpeg") {
  console.log(`\n========== R2 UPLOAD FROM URL ==========`);
  console.log(`🌐 Kaynak: ${imageUrl}`);
  console.log(`🔑 Hedef Key: ${key}`);

  // Geçici dosya oluştur
  const tempDir = path.join(process.cwd(), "temp");
  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true });
  }

  const tempFile = path.join(tempDir, `temp_${Date.now()}.jpg`);

  try {
    // Dosyayı indir
    console.log(`⬇️ İndiriliyor...`);
    await downloadFile(imageUrl, tempFile);
    console.log(`✅ İndirildi!`);

    // R2'ye yükle
    const url = await uploadFile(tempFile, key, contentType);

    // Geçici dosyayı sil
    fs.unlinkSync(tempFile);

    return url;
  } catch (error) {
    // Hata durumunda geçici dosyayı sil
    if (fs.existsSync(tempFile)) {
      fs.unlinkSync(tempFile);
    }
    throw error;
  }
}

module.exports = {
  uploadFile,
  uploadBuffer,
  uploadFromUrl,
  downloadFile,
};
