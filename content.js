// 注入到後台頁面的比對與點擊邏輯。popup 先注入本檔，再呼叫 __regionUnchecker.run(cfg)。
// 不依賴後台的 class 名稱（Play Console 與 App Store Connect 都會改版、class 混淆），
// 只認標準的 checkbox（input[type=checkbox] 或 role=checkbox）與它所在那一列的文字。
(() => {
  if (globalThis.__regionUnchecker) return;

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const norm = (s) => (s || "").normalize("NFKC").replace(/\s+/g, " ").trim().toLowerCase();
  const ROW_SELECTOR = '[role="row"], tr, li, [role="listitem"], [role="option"], [role="treeitem"]';
  const SEARCH_HINT = /搜尋|搜索|search|篩選|filter/i;

  // 後台用了 Web Components 時，checkbox 可能在 open shadow root 裡。
  function allElements() {
    const result = [];
    const roots = [document];
    while (roots.length) {
      for (const el of roots.pop().querySelectorAll("*")) {
        result.push(el);
        if (el.shadowRoot) roots.push(el.shadowRoot);
      }
    }
    return result;
  }

  function findCheckboxes() {
    return allElements().filter((el) => {
      if (el.matches('input[type="checkbox"]')) return true;
      // 自訂 checkbox 包著原生 input 時只取原生 input，避免同一格點兩次。
      return el.getAttribute("role") === "checkbox" && !el.querySelector('input[type="checkbox"]');
    });
  }

  function isChecked(el) {
    if (el instanceof HTMLInputElement) return el.checked || el.indeterminate;
    const state = el.getAttribute("aria-checked");
    return state === "true" || state === "mixed";
  }

  const countCheckboxes = (el) =>
    el.querySelectorAll('input[type="checkbox"], [role="checkbox"]').length + (el.matches?.('[role="checkbox"]') ? 1 : 0);

  // 這個 checkbox 代表的文字：無障礙標籤、<label>、所在列。
  // 往上找容器時，容器內只能有這一個 checkbox，否則會吃到「全選歐洲」這類群組的文字。
  function labelLines(el) {
    const texts = [el.getAttribute("aria-label")];
    for (const id of (el.getAttribute("aria-labelledby") || "").split(/\s+/).filter(Boolean)) {
      texts.push(el.getRootNode().getElementById?.(id)?.textContent);
    }
    if (el.labels) for (const label of el.labels) texts.push(label.innerText);
    const row = el.closest(ROW_SELECTOR);
    if (row && countCheckboxes(row) === 1) texts.push(row.innerText);
    let node = el.parentElement;
    for (let depth = 0; node && depth < 5; depth += 1, node = node.parentElement) {
      if (countCheckboxes(node) > 1) break;
      texts.push(node.innerText);
    }
    const lines = new Set();
    for (const text of texts) {
      for (const line of (text || "").split(/[\n\t]/)) {
        const n = norm(line);
        if (!n) continue;
        lines.add(n);
        lines.add(norm(n.replace(/[（(][^）)]*[）)]/g, ""))); // 「法國 (FR)」也算法國
      }
    }
    return lines;
  }

  function scan(nameToCode) {
    const found = new Map();
    for (const el of findCheckboxes()) {
      for (const line of labelLines(el)) {
        const code = nameToCode.get(line);
        if (!code) continue;
        if (!found.has(code)) found.set(code, []);
        found.get(code).push(el);
        break;
      }
    }
    return found;
  }

  function findSearchInput() {
    const inputs = allElements().filter(
      (el) =>
        el instanceof HTMLInputElement &&
        ["search", "text", ""].includes(el.type) &&
        el.getClientRects().length > 0 &&
        SEARCH_HINT.test(`${el.getAttribute("aria-label") || ""} ${el.placeholder || ""} ${el.type}`),
    );
    // 開著對話框時，國家清單通常在對話框裡。
    return inputs.find((el) => el.closest('[role="dialog"]')) || inputs[0] || null;
  }

  // 直接設 value 不會觸發框架的綁定，要用原生 setter 再送 input 事件。
  function setSearch(input, value) {
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
    input.focus();
    setter.call(input, value);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
    input.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true, key: "Enter" }));
  }

  function highlight(el) {
    const target = el.closest(ROW_SELECTOR) || el.parentElement || el;
    target.style.outline = "3px solid #b3261e";
    target.style.outlineOffset = "-2px";
  }

  async function uncheck(el) {
    el.click();
    await sleep(80);
    if (!isChecked(el)) return true;
    // 有些元件只聽外層的點擊。
    const outer = el.closest('label, [role="checkbox"]');
    if (outer && outer !== el) {
      outer.click();
      await sleep(80);
    }
    return !isChecked(el);
  }

  // targets：[{ code, names, label }]；notes 回傳 _locales 的訊息 key，由 popup 翻成介面語言。
  async function run({ targets, mode, useSearch }) {
    const nameToCode = new Map();
    const display = new Map();
    for (const { code, names, label } of targets) {
      display.set(code, label ?? code);
      for (const name of names) nameToCode.set(norm(name), code);
    }
    const report = { changed: [], alreadyOff: [], failed: [], notFound: [], notes: [], matched: 0 };
    const done = new Set();

    async function handle(code, elements) {
      done.add(code);
      report.matched += 1;
      const checked = elements.filter(isChecked);
      if (!checked.length) return report.alreadyOff.push(display.get(code));
      if (mode === "preview") {
        checked.forEach(highlight);
        return report.changed.push(display.get(code));
      }
      let ok = true;
      for (const el of checked) ok = (await uncheck(el)) && ok;
      (ok ? report.changed : report.failed).push(display.get(code));
    }

    for (const [code, elements] of scan(nameToCode)) await handle(code, elements);

    const missing = targets.filter((t) => !done.has(t.code));
    const searchInput = useSearch && missing.length ? findSearchInput() : null;
    if (searchInput) {
      const original = searchInput.value;
      for (const { code, names } of missing) {
        const single = new Map(names.map((n) => [norm(n), code]));
        for (const name of names) {
          setSearch(searchInput, name);
          let hit = null;
          for (let waited = 0; waited < 2500 && !hit; waited += 250) {
            await sleep(250);
            hit = scan(single).get(code) || null;
          }
          if (hit) {
            await handle(code, hit);
            break;
          }
        }
      }
      setSearch(searchInput, original);
      if (mode === "preview") report.notes.push("noteSearchHighlightLost");
    } else if (useSearch && missing.length) {
      report.notes.push("noteNoSearchBox");
    }

    for (const { code } of targets) if (!done.has(code)) report.notFound.push(display.get(code));
    if (!findCheckboxes().length) report.notes.push("noteNoCheckbox");
    return report;
  }

  globalThis.__regionUnchecker = { run };
})();
