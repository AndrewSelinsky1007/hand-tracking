#!/usr/bin/env bash
set -e

# 1. Build Demo / Sandbox (with Console)
pyinstaller --noconfirm --onedir --console \
  --collect-all mediapipe \
  --osx-bundle-identifier "com.game.handsandbox" \
  --info-plist "Info.plist" \
  main.py

# 2. Build Flappy Bird (with Console)
pyinstaller --noconfirm --onedir --console \
  --collect-all mediapipe \
  --add-data "flappybirdbg.png:." \
  --add-data "flappybird.png:." \
  --add-data "toppipe.png:." \
  --add-data "bottompipe.png:." \
  --osx-bundle-identifier "com.game.flappybird" \
  --info-plist "Info.plist" \
  flappybird.py

# 3. Build Tetris (with Console)
pyinstaller --noconfirm --onedir --console \
  --collect-all mediapipe \
  --osx-bundle-identifier "com.game.tetris" \
  --info-plist "Info.plist" \
  tetris.py