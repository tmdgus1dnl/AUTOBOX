#!/bin/bash
# Manually send MQTT signal to Raspberry Pi

if [ -z "$1" ]; then
  echo "Usage: ./manual_signal.sh <SIGNAL>"
  echo "Example: ./manual_signal.sh B"
  echo "Signals: B=Seoul, F=Daegu, D=Daejeon, C=Gwangju, E=Busan"
  exit 1
fi

echo "Sending signal '$1'..."
docker exec autobox-backend python3 /app/data/send_signal.py "$1"
