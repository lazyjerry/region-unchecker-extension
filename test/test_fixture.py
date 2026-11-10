"""用 test/fixture.html 驗證 content.js 的比對與點擊。執行：python3 -I test/test_fixture.py"""
import json, pathlib, sys
from playwright.sync_api import sync_playwright

root = pathlib.Path(__file__).resolve().parent.parent
targets = [
    {"code": "AT", "names": ["奧地利", "Austria"]},
    {"code": "BE", "names": ["比利時", "Belgium"]},
    {"code": "FR", "names": ["法國", "France"]},
    {"code": "DE", "names": ["德國", "Germany"]},
    {"code": "ES", "names": ["西班牙", "Spain"]},
    {"code": "SE", "names": ["瑞典", "Sweden"]},
    {"code": "RE", "names": ["留尼旺", "留尼汪", "Réunion"]},
    {"code": "NL", "names": ["荷蘭", "Netherlands"]},
]
for t in targets:
    t["label"] = f"{t['names'][0]}({t['code']})"
failures = []
def expect(label, actual, wanted):
    if actual != wanted:
        failures.append(f"{label}: got {actual!r}, want {wanted!r}")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    for mode in ("preview", "uncheck"):
        page.goto((root / "test" / "fixture.html").as_uri())
        page.add_script_tag(path=str(root / "content.js"))
        report = page.evaluate("cfg => globalThis.__regionUnchecker.run(cfg)", {"targets": targets, "mode": mode, "useSearch": True})
        print(mode, json.dumps(report, ensure_ascii=False))
        expect(f"{mode} changed", sorted(report["changed"]), sorted(["奧地利(AT)", "法國(FR)", "德國(DE)", "西班牙(ES)", "瑞典(SE)", "留尼旺(RE)"]))
        expect(f"{mode} alreadyOff", report["alreadyOff"], ["比利時(BE)"])
        expect(f"{mode} notFound", report["notFound"], ["荷蘭(NL)"])
        state = page.evaluate("""() => ({
          rows: [...document.querySelectorAll('#rows tr')].map(tr => [tr.cells[1].textContent, tr.querySelector('input').checked]),
          custom: [...document.querySelectorAll('#custom div')].map(d => [d.textContent, d.firstElementChild.getAttribute('aria-checked')]),
          hidden: window.__hidden,
          europe: document.getElementById('all-europe').checked,
          search: document.getElementById('search').value,
        })""")
        on = mode == "preview"
        expect(f"{mode} rows", state["rows"], [["奧地利", on], ["比利時", False], ["法國 (FR)", on], ["挪威", True], ["Netherlands Antilles", True], ["德國", on]])
        expect(f"{mode} custom", state["custom"], [["Spain", "true" if on else "false"], ["Liechtenstein", "true"]])
        expect(f"{mode} hidden", state["hidden"], {"瑞典": on, "留尼汪": on})
        expect(f"{mode} group checkbox untouched", state["europe"], True)
        expect(f"{mode} search restored", state["search"], "")
    browser.close()

if failures:
    print("\n".join(failures)); sys.exit(1)
print("OK")
