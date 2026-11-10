#!/usr/bin/env bash
# 重建套件圖示與商店素材（宣傳圖、截圖）。改了 store/icon.svg、store/showcase.html、介面文字後執行。
# 用法：bash scripts/render-assets.sh
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 -I "${root}/scripts/render_assets.py"
