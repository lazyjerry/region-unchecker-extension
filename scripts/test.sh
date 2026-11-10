#!/usr/bin/env bash
# 跑全部測試：語法檢查、content.js 邏輯測試、在 Chromium 實際安裝套件的端對端測試。
# 用法：bash scripts/test.sh
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${root}"
python3 -I -m json.tool manifest.json >/dev/null
node --check content.js
node --input-type=module --check < countries.js
node --input-type=module --check < popup.js
echo "語法檢查通過"
python3 -I test/test_fixture.py
python3 -I test/test_install.py
