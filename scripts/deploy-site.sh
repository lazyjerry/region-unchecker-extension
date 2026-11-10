#!/usr/bin/env bash
# 組出行銷網站（site/ + 圖示、截圖、套件 zip）並部署到 Cloudflare Pages。
# 用法：bash scripts/deploy-site.sh [--check]
#   --check：只組站並檢查站內連結，不部署。
# 部署屬於發佈，只在使用者明確要求後執行；需先 npx wrangler login。
# 產出在 build/site/（不進版控）。正式網址 https://region-unchecker.jlab-app.cloud/（Pages 自訂網域 + 代理的 CNAME 指向 region-unchecker.pages.dev，
# 已用 cf pages domains create 與 cf dns records create 建好，部署不需重做）。
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
pages_project="region-unchecker"
out="${root}/build/site"

check_only=false
if [[ $# -eq 1 && "$1" == "--check" ]]; then
  check_only=true
elif [[ $# -gt 0 ]]; then
  echo "Usage: $0 [--check]" >&2
  exit 2
fi

zip_path="$(bash "${root}/scripts/package.sh")"

rm -rf "${out}"
mkdir -p "${out}"
cp -R "${root}/site/." "${out}/"
mkdir -p "${out}/assets" "${out}/download"
cp "${root}/icons/icon-48.png" "${root}/icons/icon-128.png" "${out}/assets/"
cp "${root}/store/assets/screenshot-1280x800-zh_TW.png" "${out}/assets/screenshot-zh_TW.png"
cp "${root}/store/assets/screenshot-1280x800-en.png" "${out}/assets/screenshot-en.png"
cp "${zip_path}" "${out}/download/region-unchecker.zip"

# 站內的 href/src 都要指到 build/site 裡存在的檔案；不載入外部資源。
python3 -I - "${out}" <<'PY'
import pathlib, re, sys
from urllib.parse import urlparse

out = pathlib.Path(sys.argv[1])
errors = []
for page in sorted(out.rglob("*.html")):
    html = page.read_text(encoding="utf-8")
    for attr, url in re.findall(r'\b(href|src)="([^"]*)"', html):
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https"):
            if attr == "src" or 'rel="stylesheet"' in html and url.endswith(".css"):
                errors.append(f"{page.relative_to(out)} 載入外部資源：{url}")
            continue
        if parsed.scheme or not parsed.path:
            continue  # mailto:、#anchor
        target = (page.parent / parsed.path).resolve()
        if target.is_dir():
            target = target / "index.html"
        if not target.exists():
            errors.append(f"{page.relative_to(out)} 連到不存在的檔案：{url}")
    for anchor in re.findall(r'href="#([^"]+)"', html):
        if f'id="{anchor}"' not in html:
            errors.append(f"{page.relative_to(out)} 錨點不存在：#{anchor}")
if errors:
    sys.exit("\n".join(errors))
print(f"站內連結檢查通過：{sum(1 for _ in out.rglob('*.html'))} 頁")
PY

if [[ "${check_only}" == true ]]; then
  echo "${out}"
  exit 0
fi

cd "${root}"
# 新版 Wrangler 的 pages deploy 不會自動建立專案；第一次部署先建立。
# --force：建立傳統 Pages 專案，不轉成併入 Workers 的新版 Pages，才能沿用 pages deploy。
if ! npx --yes wrangler pages project list 2>/dev/null | grep -qE "[│|] ${pages_project} +[│|]"; then
  npx --yes wrangler pages project create "${pages_project}" --production-branch main --force
fi
npx --yes wrangler pages deploy "${out}" --project-name "${pages_project}" --branch main --commit-dirty=true
