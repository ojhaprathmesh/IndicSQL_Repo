#!/usr/bin/env bash
# ==============================================================================
# IndicSQL Studio: Mobile Release APK Build Pipeline
#
# Shrinks mobile distribution footprint from 1.6 GB intermediate objects /
# 95 MB fat debug APK down to optimized ~15-18 MB split-architecture release APKs.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
MOBILE_DIR="${ROOT_DIR}/mobile"

echo "=========================================================="
echo "🚀 IndicSQL Mobile: Production Release Optimization Build"
echo "=========================================================="

cd "${MOBILE_DIR}"

echo ""
echo "1. Cleaning previous intermediate build caches (reclaiming ~1.6 GB)..."
flutter clean

echo ""
echo "2. Fetching production dependencies..."
flutter pub get

echo ""
echo "3. Running static code analysis (strict lints)..."
flutter analyze

echo ""
echo "4. Running full automated mobile test suite..."
flutter test

echo ""
echo "5. Building optimized split-ABI release APKs with symbol obfuscation..."
flutter build apk \
  --release \
  --split-per-abi \
  --obfuscate \
  --split-debug-info=build/app/outputs/symbols/

echo ""
echo "=========================================================="
echo "✅ Production Release Build Complete!"
echo "=========================================================="
echo "Optimized APK artifacts generated in mobile/build/app/outputs/flutter-apk/:"
echo ""

ls -lh build/app/outputs/flutter-apk/*.apk 2>/dev/null || true

echo ""
echo "Tip: Install on physical device with:"
echo "  adb install -r build/app/outputs/flutter-apk/app-arm64-v8a-release.apk"
