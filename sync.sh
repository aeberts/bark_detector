#!/usr/bin/env bash
LOCAL_DIR="${1:-.}"
REMOTE_DIR="${2:-/home/pi/dev/bark_detector}"
REMOTE_HOST="pi@catflap.local"

echo "Syncing '$LOCAL_DIR' → ${REMOTE_HOST}:${REMOTE_DIR}"

rsync -avz --delete \
  --exclude='.venv' \
  --exclude='*.pyc' \
  --exclude='__pycache__/' \
  --exclude='.gitignore' \
  --exclude='sync.sh' \
  "${LOCAL_DIR%/}/" "${REMOTE_HOST}:${REMOTE_DIR}"

echo "Done."