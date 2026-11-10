"""在 Playwright 的 Chromium 實際載入擴充套件，從 popup 按「預覽」「取消勾選」驗證端對端流程。

後台網址以 page.route 攔截，回應 test/fixture.html，讓 host_permissions 與真實情境一致。
popup 以分頁開啟並帶 ?tabId=，因為自動化無法點工具列圖示。
執行：python3 -I test/test_install.py
"""
import hashlib, json, pathlib, sys, tempfile, time
from playwright.sync_api import sync_playwright

root = pathlib.Path(__file__).resolve().parent.parent
fixture = (root / "test" / "fixture.html").read_text(encoding="utf-8")
console_url = "https://play.google.com/console/u/0/developers/test/app/test/tracks/production/countries"
failures = []
extra = ["奧地利", "法國", "Spain", "瑞典", "留尼汪", "比利時", "荷蘭"]


def expect(label, actual, wanted):
    if actual != wanted:
        failures.append(f"{label}: got {actual!r}, want {wanted!r}")


def extension_id(profile):
    # 未封裝的套件 ID 由路徑決定；從設定檔讀，避免自己重算的編碼差異。
    for name in ("Secure Preferences", "Preferences"):
        path = pathlib.Path(profile) / "Default" / name
        if not path.exists():
            continue
        settings = json.loads(path.read_text(encoding="utf-8")).get("extensions", {}).get("settings", {})
        for ext_id, info in settings.items():
            if pathlib.Path(info.get("path", "")).resolve() == root:
                return ext_id
    digest = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:32]
    return "".join(chr(ord("a") + int(c, 16)) for c in digest)


def fixture_state(page):
    return page.evaluate("""() => ({
      rows: [...document.querySelectorAll('#rows tr')].map(tr => [tr.cells[1].textContent, tr.querySelector('input').checked]),
      custom: [...document.querySelectorAll('#custom div')].map(d => [d.textContent, d.firstElementChild.getAttribute('aria-checked')]),
      hidden: window.__hidden,
      europe: document.getElementById('all-europe').checked,
    })""")


with tempfile.TemporaryDirectory() as profile, sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        profile,
        channel="chromium",
        headless=True,
        args=[f"--disable-extensions-except={root}", f"--load-extension={root}"],
    )
    context.route("https://play.google.com/console/**", lambda route: route.fulfill(status=200, content_type="text/html; charset=utf-8", body=fixture))

    ext_id = None
    for _ in range(20):
        ext_id = extension_id(profile)
        probe = context.new_page()
        response = probe.goto(f"chrome-extension://{ext_id}/popup.html")
        ok = response is None or response.ok
        probe.close()
        if ok:
            break
        time.sleep(0.5)
    print("extension id:", ext_id)

    for mode, button in (("preview", "#preview"), ("uncheck", "#run")):
        target = context.new_page()
        target.goto(console_url)
        popup = context.new_page()
        popup.goto(f"chrome-extension://{ext_id}/popup.html")
        expect(f"{mode} popup title", popup.title(), "上架地區批次取消")
        expect(f"{mode} group count", popup.locator("#groups input").count(), 3)
        tab_id = popup.evaluate("async url => (await chrome.tabs.query({url})).at(-1).id", console_url)
        popup.goto(f"chrome-extension://{ext_id}/popup.html?tabId={tab_id}")
        # 預設群組有 32 國，fixture 只放幾國，其餘都會走搜尋等待；這裡只驗證套件串接，
        # 用「其他名稱」指定少數國家。群組別名的比對由 test_fixture.py 覆蓋。
        if mode == "preview":
            for box in popup.locator("#groups input").all():
                box.uncheck()
            popup.fill("#extra", "\n".join(extra))
        else:
            expect("settings persisted", popup.locator("#extra").input_value(), "\n".join(extra))
            expect("groups persisted", [b.is_checked() for b in popup.locator("#groups input").all()], [False, False, False])
        popup.click(button)
        popup.wait_for_function("() => !document.getElementById('out').textContent.includes('執行中')", timeout=60000)
        out = popup.locator("#out").inner_text()
        print(f"--- {mode}\n{out}")
        verb = "會取消" if mode == "preview" else "已取消"
        lines = out.splitlines()
        expect(f"{mode} report", lines[:3], [f"{verb}（5）：奧地利、法國、Spain、瑞典、留尼汪", "原本就沒勾（1）：比利時", "找不到（1）：荷蘭"])
        on = mode == "preview"
        state = fixture_state(target)
        expect(f"{mode} rows", state["rows"], [["奧地利", on], ["比利時", False], ["法國 (FR)", on], ["挪威", True], ["Netherlands Antilles", True], ["德國", True]])
        expect(f"{mode} custom", state["custom"], [["Spain", "true" if on else "false"], ["Liechtenstein", "true"]])
        expect(f"{mode} hidden", state["hidden"], {"瑞典": on, "留尼汪": on})
        expect(f"{mode} group checkbox untouched", state["europe"], True)
        target.close()
        popup.close()
    context.close()

if failures:
    print("\n".join(failures))
    sys.exit(1)
print("OK")
