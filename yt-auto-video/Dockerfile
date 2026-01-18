FROM node:20-slim

# Çalışma dizini
WORKDIR /app

# OpenSSL kurulumu (Prisma için gerekli olabilir)
RUN apt-get update -y && apt-get install -y openssl

# Package dosyalarını kopyala
COPY package*.json ./
COPY prisma ./prisma/

# Bağımlılıkları yükle
RUN npm install

# Prisma client oluştur
RUN npx prisma generate

# Uygulama kodlarını kopyala
COPY . .

# Port
EXPOSE 3000

# Çalıştırma komutu: Önce DB tablolarını oluştur (push), sonra sunucuyu başlat
CMD ["/bin/sh", "-c", "npx prisma db push && npm start"]
