#!/usr/bin/env bash
# 打包擴充套件成 zip（Chrome 載入未封裝項目用資料夾即可；zip 給 Chrome Web Store 上傳或分享）。
# 用法：bash scripts/package.sh
# 產出：dist/region-unchecker-<manifest version>.zip，只含執行時需要的檔案。
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
files=(manifest.json popup.html popup.js countries.js content.js
  _locales/zh_TW/messages.json _locales/en/messages.json
  icons/icon-16.png icons/icon-32.png icons/icon-48.png icons/icon-128.png)
version="$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "${root}/manifest.json")"
out="${root}/dist/region-unchecker-${version}.zip"

for f in "${files[@]}"; do
  [[ -f "${root}/${f}" ]] || { echo "缺少檔案：${f}" >&2; exit 1; }
done
mkdir -p "${root}/dist"
rm -f "${out}"
(cd "${root}" && zip -q -X "${out}" "${files[@]}")
echo "${out}"
