#!/bin/bash
echo "🎨 FLUX API başlatılıyor..."
cd /app
python3 -c "import uvicorn; uvicorn.run('api:app', host='0.0.0.0', port=8888)"
