#!/bin/bash
# Manually retry OCR for the latest image file

echo "Retrying OCR for latest image..."
docker exec autobox-backend python3 /app/data/retry_ocr.py
