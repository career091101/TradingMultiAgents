#!/bin/bash
# Chrome起動スクリプト - 2048×1280解像度 (デバッグポート付き)

# Chrome for MCP - 2048×1280解像度で起動
open -a "Google Chrome" \
  --args \
  --window-size=2048,1280 \
  --window-position=0,0 \
  --force-device-scale-factor=1 \
  --disable-features=DevToolsOpenAtStart \
  --remote-debugging-port=9222 \
  http://localhost:8501

echo "Chrome opened with 2048×1280 resolution and debugging port 9222"