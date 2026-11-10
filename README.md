# 上架地區批次取消

Chrome 擴充套件。在 Google Play Console 或 App Store Connect 的「國家／地區」編輯畫面，把指定國家（預設歐盟 27 國與法國海外省）一次取消勾選，取代逐一搜尋、取消的手動操作。

## 為什麼需要

- **App Store Connect**：上架地區有 API（`POST /v2/appAvailabilities`），App 專案用腳本設定即可，不必用本套件。
- **Google Play**：Publishing API 的國家可用性只能讀（`edits.countryavailability.get`），不能寫，只能在網頁操作。本套件主要為它而做。

## 安裝

1. Chrome 開 `chrome://extensions`，打開右上角「開發人員模式」。
2. 按「載入未封裝項目」，選本資料夾。

## 使用

1. 在後台打開國家／地區的編輯畫面（Play Console：發布軌道 →「國家／地區」→ 編輯）。
2. 按工具列的套件圖示，勾選要取消的群組；有後台譯名對不上的國家，在「其他名稱」補一行。
3. 先按「預覽」：會取消的國家在頁面上以紅框標示，結果列出「會取消／原本就沒勾／找不到」。
4. 確認後按「取消勾選」，再自行檢查並按後台的「儲存」。套件不會替你按儲存。

## 運作方式

- 只認標準的 checkbox（`input[type=checkbox]`、`role=checkbox`）與所在那一列的文字，不依賴後台的 class 名稱。
- 文字必須與某個別名**完全相同**才算命中（`法國 (FR)` 這類括號會先去掉），所以「挪威」「Netherlands Antilles」「全選歐洲」不會被誤點。
- 頁面上找不到的國家，若有搜尋框，會逐一輸入別名搜尋、等結果出現再取消，最後還原搜尋框。每個別名最多等 2.5 秒。
- 國家與別名在 `countries.js`；清單來源是各 App 專案的 `docs/app-release/eu-countries.md`。

## 限制

- 後台改版若不再用標準 checkbox 或無障礙標籤，比對會失效；結果的「找不到」會列出來，不會靜默略過。
- 搜尋時每個別名找不到要等滿 2.5 秒；後台譯名大量對不上時會很慢，可先關掉「用搜尋框逐一搜尋」看預覽結果，再補別名。
- 尚未在真實的 Play Console 頁面驗證。第一次使用請先預覽，並把對不上的譯名補進 `countries.js`。

## 測試

```bash
bash scripts/test.sh      # 語法檢查 + 兩組測試
bash scripts/package.sh   # 打包成 dist/region-unchecker-<版本>.zip
```

- `test/test_fixture.py`：以 `test/fixture.html` 模擬表格列、自訂 checkbox、群組全選與只在搜尋時渲染的清單，直接驗證 `content.js` 的預覽與取消。
- `test/test_install.py`：在 Playwright 的 Chromium 實際載入套件，後台網址攔截成 fixture，從 popup 按鈕走完整流程，並確認設定會保存。

需要 Python 版 Playwright。

## 上架 Chrome Web Store

- 上架表單要填的文字、素材對應、權限理由與隱私問卷答案：`store/LISTING.md`。
- 隱私權政策內容：`store/privacy-policy.md`（要放上網才有網址）。
- 介面文字在 `_locales/zh_TW`、`_locales/en`；改了文字、`store/icon.svg` 或 `store/showcase.html` 後跑 `bash scripts/render-assets.sh` 重建圖示與素材，再跑 `bash scripts/package.sh`。
- macOS 的 Chrome 介面語言跟系統語言走，`--lang` 無效；`render_assets.py` 用只留單一語系的暫時副本截圖。

## 網站

- 行銷頁、隱私權政策與 zip 下載：https://region-unchecker.jlab-app.cloud/ ，原始檔在 `site/`。
- 部署：`bash scripts/deploy-site.sh`（`--check` 只組站並檢查連結）。
