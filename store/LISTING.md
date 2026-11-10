# Chrome Web Store 上架資料

後台：<https://chrome.google.com/webstore/devconsole>

上傳檔：`bash scripts/package.sh` 產出的 `dist/region-unchecker-<版本>.zip`。素材：`bash scripts/render-assets.sh` 產出的 `store/assets/`。

## 商店資訊（Store listing）

名稱與簡短說明取自 `_locales/*/messages.json` 的 `extName`、`extDescription`，上傳後自動帶入，不在後台另填。

| 欄位 | 值 |
|---|---|
| 類別 | 開發人員工具（Developer Tools） |
| 語言 | 中文（台灣）為預設，另加英文 |
| 商店圖示 | `icons/icon-128.png` |
| 螢幕截圖 | `store/assets/screenshot-1280x800-zh_TW.png`（中文）、`store/assets/screenshot-1280x800-en.png`（英文） |
| 小型宣傳圖塊 | `store/assets/promo-440x280-zh_TW.png`（中文）、`store/assets/promo-440x280-en.png`（英文） |
| 官方網址 | 留空（要先在 Google Search Console 驗證網域擁有權才能選） |
| 首頁網址 | https://region-unchecker.jlab-app.cloud/ |
| 支援網址 | https://region-unchecker.jlab-app.cloud/#faq |

### 詳細說明（中文）

```text
在 App 發布後台的「國家／地區」清單中，一次取消勾選指定國家，不必逐一搜尋、取消。

適用情境：還沒申報歐盟《數位服務法》（DSA）交易者身分時，App 的上架地區要排除歐盟 27 國。後台沒有「排除歐盟」的選項，只能一國一國取消。本套件在 Google Play Console 與 App Store Connect 的國家／地區編輯畫面上，依清單找出這些國家並取消勾選。

功能
・內建歐盟 27 國、法國海外省、中國大陸三組清單，可自行勾選
・可補充其他國家名稱，一行一個
・先「預覽」以紅框標示會取消的國家，確認後再「取消勾選」
・清單上看不到的國家，自動用頁面的搜尋框逐一搜尋
・結果列出已取消、原本就沒勾、找不到的國家，不會靜默略過
・不會替你按「儲存」，送出前可以自行檢查

隱私
・不連網、不收集任何資料，設定只存在你的瀏覽器
・只在你按下按鈕時，對目前分頁執行

本套件與 Google、Apple 無關，也未經其認可。Google Play 與 App Store Connect 為各自所有者的商標。
```

### Detailed description (English)

```text
Uncheck a set of countries on an app publishing console's "Countries / regions" list in one go, instead of searching and unchecking them one by one.

Typical use: until you have declared your trader status under the EU Digital Services Act (DSA), your app's availability must exclude the 27 EU member states. Consoles offer no "exclude EU" option, so each country has to be unchecked by hand. This extension finds those countries on the country/region editor of Google Play Console and App Store Connect and unchecks them.

Features
• Built-in lists: EU member states (27), French overseas regions, Mainland China
• Add more country names, one per line
• Preview first: countries to be unchecked are outlined in red; then click Uncheck
• Countries not visible on the page are looked up through the page's search box
• The result lists what was unchecked, what was already unchecked and what was not found
• Never clicks Save for you, so you can review before submitting

Privacy
• No network access and no data collection; settings stay in your browser
• Runs on the current tab only when you click a button

This extension is not affiliated with or endorsed by Google or Apple. Google Play and App Store Connect are trademarks of their respective owners.
```

## 隱私權做法（Privacy practices）

### 單一用途說明

```text
在 App 發布後台的國家／地區清單中，依使用者選擇的國家清單批次取消勾選。
Bulk-unchecks user-selected countries on the country/region list of app publishing consoles.
```

### 權限理由

| 權限 | 理由 |
|---|---|
| `activeTab` | Runs only on the tab the user is viewing, and only after the user clicks Preview or Uncheck in the popup. |
| `scripting` | Injects the script that finds the listed countries' checkboxes on the current page and unchecks them. |
| `storage` | Saves the user's selected country groups and extra names locally (chrome.storage.local) so they are kept next time. Nothing is synced or sent anywhere. |
| 主機權限 `https://play.google.com/console/*`、`https://appstoreconnect.apple.com/*` | The country/region editors are on these two consoles. The script must run in every frame of the page, because the editor may be inside an iframe, which activeTab alone does not cover. |

### 遠端程式碼

選「否，我沒有使用遠端程式碼」。所有程式都在套件內。

### 資料使用

- 收集的使用者資料類型：全部不勾。
- 三項聲明全部勾選：不出售或轉讓給第三方、不用於與單一用途無關的目的、不用於判斷信用或放貸。

### 隱私權政策網址

https://region-unchecker.jlab-app.cloud/privacy/（內容與 `store/privacy-policy.md` 一致）

## 發布（Distribution）

| 欄位 | 值 |
|---|---|
| 公開範圍 | 先選「不公開」（Unlisted），在真實後台驗證後再改公開 |
| 地區 | 所有地區 |
| 付款 | 免費 |
