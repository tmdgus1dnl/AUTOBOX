#!/bin/bash

# cURL로 base64 이미지를 FastAPI에 전송하는 예시

# =====================
# 1. 파일을 base64로 인코딩하여 전송
# =====================
echo "📦 Base64 이미지 전송 예시 (cURL)"
echo ""

# 이미지 파일 경로
IMAGE_PATH="./img/test.png"

# API URL (외부 서버라면 해당 IP:Port로 변경)
API_URL="http://localhost:8000"

# 이미지를 base64로 인코딩
IMAGE_BASE64=$(base64 -i "$IMAGE_PATH")

# API 요청
echo "🔄 API 요청 중..."
curl -X POST "${API_URL}/predict/base64" \
  -H "Content-Type: application/json" \
  -d "{\"image_base64\": \"${IMAGE_BASE64}\"}"

echo ""
echo "✅ 완료!"

# =====================
# 2. 한 줄로 실행 (Mac/Linux)
# =====================
# curl -X POST "http://localhost:8000/predict/base64" \
#   -H "Content-Type: application/json" \
#   -d "{\"image_base64\": \"$(base64 -i ./img/test.png)\"}"

# =====================
# 3. Windows PowerShell 예시
# =====================
# $imageBytes = [System.IO.File]::ReadAllBytes("./img/test.png")
# $imageBase64 = [System.Convert]::ToBase64String($imageBytes)
# $body = @{image_base64=$imageBase64} | ConvertTo-Json
# Invoke-RestMethod -Uri "http://localhost:8000/predict/base64" -Method Post -Body $body -ContentType "application/json"
