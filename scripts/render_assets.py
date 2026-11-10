"""由 store/icon.svg 與 store/showcase.html 產生套件圖示與商店素材。

產出：
  icons/icon-{16,32,48,128}.png        套件圖示
  store/assets/promo-440x280-{zh_TW,en}.png   小型宣傳圖
  store/assets/screenshot-1280x800-{zh_TW,en}.png  商店截圖：示意後台 + 預覽結果 + popup
執行：python3 -I scripts/render_assets.py（或 bash scripts/render-assets.sh）
"""
import base64, json, pathlib, re, shutil, sys, tempfile, time
from playwright.sync_api import sync_playwright

root = pathlib.Path(__file__).resolve().parent.parent
svg = (root / "store" / "icon.svg").read_text(encoding="utf-8")
showcase = (root / "store" / "showcase.html").read_text(encoding="utf-8")
assets = root / "store" / "assets"
assets.mkdir(parents=True, exist_ok=True)
(root / "icons").mkdir(exist_ok=True)
console_url = "https://play.google.com/console/u/0/showcase"
LOCALES = {"zh_TW": "zh-TW", "en": "en-US"}


def svg_sized(size, crop):
    body = re.sub(r"<!--.*?-->", "", svg, flags=re.S)
    if crop:
        body = body.replace('viewBox="0 0 128 128"', 'viewBox="16 16 96 96"')
    return body.replace("<svg ", f'<svg width="{size}" height="{size}" ', 1)


def messages(locale):
    data = json.loads((root / "_locales" / locale / "messages.json").read_text(encoding="utf-8"))
    return {k: v["message"] for k, v in data.items()}


def render_icons(browser):
    page = browser.new_page()
    for size in (16, 32, 48, 128):
        # 16–48 px 裁掉透明邊，讓工具列上的圖示夠大；128 px 保留 Chrome 規範的邊界。
        page.set_viewport_size({"width": size, "height": size})
        page.set_content(f'<html><body style="margin:0;background:transparent">{svg_sized(size, size < 128)}</body></html>')
        page.screenshot(path=str(root / "icons" / f"icon-{size}.png"), omit_background=True)
    page.close()


def render_promo(browser):
    page = browser.new_page(viewport={"width": 440, "height": 280})
    taglines = {"zh_TW": "一鍵取消歐盟等上架地區", "en": "Uncheck EU countries in one click"}
    for locale in LOCALES:
        m = messages(locale)
        page.set_content(f"""<html><body style="margin:0;width:440px;height:280px;display:flex;align-items:center;gap:20px;
          padding:0 32px;box-sizing:border-box;background:#fbf3f2;font-family:system-ui,sans-serif;color:#2d2d2d">
          {svg_sized(120, False)}
          <div><div style="font-size:26px;font-weight:700;line-height:1.2">{m['extName']}</div>
          <div style="font-size:16px;margin-top:10px;color:#b3261e">{taglines[locale]}</div></div></body></html>""")
        page.screenshot(path=str(assets / f"promo-440x280-{locale}.png"))
    page.close()


def render_screenshots(p):
    for locale, lang in LOCALES.items():
        with tempfile.TemporaryDirectory() as profile, tempfile.TemporaryDirectory() as tmp:
            ext_dir = locale_only_copy(locale, pathlib.Path(tmp))
            context = p.chromium.launch_persistent_context(
                profile, channel="chromium", headless=True, locale=lang,
                args=[f"--lang={lang}", f"--disable-extensions-except={ext_dir}", f"--load-extension={ext_dir}"],
            )
            context.route("https://play.google.com/console/**", lambda route: route.fulfill(status=200, content_type="text/html; charset=utf-8", body=showcase))
            target = context.new_page()
            target.set_viewport_size({"width": 1280, "height": 800})
            target.goto(f"{console_url}?lang={'en' if locale == 'en' else 'zh'}")
            ext_id = find_extension_id(profile, ext_dir)
            popup = context.new_page()
            popup.set_viewport_size({"width": 364, "height": 600})
            popup.goto(f"chrome-extension://{ext_id}/popup.html")
            tab_id = popup.evaluate("async url => (await chrome.tabs.query({url: url + '*'})).at(-1).id", console_url)
            ui = popup.evaluate("() => chrome.i18n.getMessage('localeCode')")
            popup.goto(f"chrome-extension://{ext_id}/popup.html?tabId={tab_id}")
            popup.click("#preview")
            popup.wait_for_function("t => !document.getElementById('out').textContent.includes(t)", arg=messages(locale)["running"], timeout=120000)
            shot = popup.screenshot(full_page=True)
            print(locale, "ui language:", ui)
            print(popup.locator("#out").inner_text())
            data = base64.b64encode(shot).decode()
            target.evaluate("""data => {
              const img = document.createElement('img');
              img.src = 'data:image/png;base64,' + data;
              img.style.cssText = 'position:fixed;top:56px;right:24px;width:364px;border:1px solid #999;box-shadow:0 8px 28px rgba(0,0,0,.28);background:#fff';
              document.body.append(img);
              return new Promise(r => img.onload = r);
            }""", data)
            target.screenshot(path=str(assets / f"screenshot-1280x800-{locale}.png"))
            context.close()


def locale_only_copy(locale, tmp):
    # macOS 的 Chrome 訊息語系跟系統語言走，--lang 無效；複製一份只留目標語系的套件，確保截圖語言正確。
    ext_dir = tmp / "ext"
    shutil.copytree(root, ext_dir, ignore=shutil.ignore_patterns("dist", "store", "test", "scripts", ".git", "*.md"))
    for other in (ext_dir / "_locales").iterdir():
        if other.name != locale:
            shutil.rmtree(other)
    manifest = json.loads((ext_dir / "manifest.json").read_text(encoding="utf-8"))
    manifest["default_locale"] = locale
    (ext_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return ext_dir.resolve()


def find_extension_id(profile, ext_dir):
    # 設定檔是延遲寫入的，等它出現。
    for _ in range(40):
        for name in ("Secure Preferences", "Preferences"):
            path = pathlib.Path(profile) / "Default" / name
            if path.exists():
                settings = json.loads(path.read_text(encoding="utf-8")).get("extensions", {}).get("settings", {})
                for ext_id, info in settings.items():
                    if pathlib.Path(info.get("path", "")).resolve() == ext_dir:
                        return ext_id
        time.sleep(0.25)
    sys.exit("找不到套件 ID")


with sync_playwright() as p:
    browser = p.chromium.launch()
    render_icons(browser)
    render_promo(browser)
    browser.close()
    render_screenshots(p)
print("OK")
