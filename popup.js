import { GROUPS, displayName } from "./countries.js";

const t = (key, subs) => chrome.i18n.getMessage(key, subs);
// 用訊息實際套用的語系；getUILanguage() 在 macOS 上可能和訊息語系不同，介面不支援的語言也會退回 default_locale。
const uiLanguage = t("localeCode").replace("_", "-");

for (const el of document.querySelectorAll("[data-i18n]")) el.textContent = t(el.dataset.i18n);
for (const el of document.querySelectorAll("[data-i18n-placeholder]")) el.placeholder = t(el.dataset.i18nPlaceholder);
document.documentElement.lang = uiLanguage;
document.title = t("extName");

const groupsBox = document.getElementById("groups");
const extraBox = document.getElementById("extra");
const useSearchBox = document.getElementById("useSearch");
const out = document.getElementById("out");

const saved = await chrome.storage.local.get(["groups", "extra", "useSearch"]).catch(() => ({}));

for (const group of GROUPS) {
  const label = document.createElement("label");
  const box = document.createElement("input");
  box.type = "checkbox";
  box.value = group.id;
  box.checked = saved.groups ? saved.groups.includes(group.id) : group.defaultOn;
  label.append(box, ` ${t(group.labelKey)}${t("countSuffix", [String(group.countries.length)])}`);
  groupsBox.append(label);
}
extraBox.value = saved.extra ?? "";
if (typeof saved.useSearch === "boolean") useSearchBox.checked = saved.useSearch;

function collectTargets() {
  const selected = [...groupsBox.querySelectorAll("input:checked")].map((b) => b.value);
  const targets = GROUPS.filter((g) => selected.includes(g.id)).flatMap((g) =>
    g.countries.map(([code, names]) => ({ code, names, label: `${displayName(names, uiLanguage)} (${code})` })),
  );
  for (const line of extraBox.value.split("\n").map((s) => s.trim()).filter(Boolean)) {
    targets.push({ code: line, names: [line], label: line });
  }
  chrome.storage.local.set({ groups: selected, extra: extraBox.value, useSearch: useSearchBox.checked });
  return targets;
}

function format(report, mode) {
  const sep = t("listSeparator");
  const line = (key, items) => t(key, [t("countSuffix", [String(items.length)]), items.join(sep)]);
  const lines = [];
  if (report.changed.length) lines.push(line(mode === "preview" ? "resultWillUncheck" : "resultUnchecked", report.changed));
  if (report.alreadyOff.length) lines.push(line("resultAlreadyOff", report.alreadyOff));
  if (report.failed.length) lines.push(line("resultFailed", report.failed));
  if (report.notFound.length) lines.push(line("resultNotFound", report.notFound));
  if (report.notes.length) lines.push("", ...report.notes.map((code) => t(code)));
  return lines.join("\n") || t("noResult");
}

async function run(mode) {
  out.textContent = t("running");
  const targets = collectTargets();
  // 安裝測試以分頁開啟 popup.html，用 ?tabId= 指定目標分頁；從工具列開啟時沒有這個參數。
  const forcedTabId = Number(new URLSearchParams(location.search).get("tabId"));
  const [tab] = forcedTabId
    ? [{ id: forcedTabId }]
    : await chrome.tabs.query({ active: true, currentWindow: true });
  try {
    await chrome.scripting.executeScript({ target: { tabId: tab.id, allFrames: true }, files: ["content.js"] });
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id, allFrames: true },
      func: (cfg) => globalThis.__regionUnchecker.run(cfg),
      args: [{ targets, mode, useSearch: useSearchBox.checked }],
    });
    // 多個 frame 各自回報；取命中最多的那個 frame（國家清單所在處）。
    const reports = results.map((r) => r.result).filter(Boolean);
    reports.sort((a, b) => b.matched - a.matched);
    out.textContent = reports.length ? format(reports[0], mode) : t("noResponse");
  } catch (error) {
    out.textContent = t("cannotRun", [error.message]);
  }
}

document.getElementById("preview").addEventListener("click", () => run("preview"));
document.getElementById("run").addEventListener("click", () => run("uncheck"));
