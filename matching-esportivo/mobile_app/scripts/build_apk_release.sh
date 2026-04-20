#!/usr/bin/env bash
set -euo pipefail

FLAVOR="${1:-prod}"
DEV_BASE_URL="${2:-https://api-dev.matching-esportivo.local/v1}"
PROD_BASE_URL="${3:-https://api.matching-esportivo.com/v1}"
DEBUG_INFO_DIR="${4:-build/app/outputs/symbols}"

echo "==> Flutter clean"
flutter clean

echo "==> Flutter pub get"
flutter pub get

echo "==> Flutter analyze"
flutter analyze

echo "==> Build APK release (obfuscate + split-debug-info)"
flutter build apk --release \
  --obfuscate \
  --split-debug-info="$DEBUG_INFO_DIR" \
  --dart-define=APP_FLAVOR="$FLAVOR" \
  --dart-define=API_BASE_URL_DEV="$DEV_BASE_URL" \
  --dart-define=API_BASE_URL_PROD="$PROD_BASE_URL" \
  --dart-define=ENABLE_DEBUG_NETWORK_LOGS=false \
  --dart-define=ENABLE_SSL_PINNING=true

echo "Build concluído com sucesso."