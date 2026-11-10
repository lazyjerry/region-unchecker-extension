// 國家清單與後台可能顯示的名稱。
// 來源：各 App 專案的 docs/app-release/eu-countries.md（歐盟 27 國、法國海外省、中國大陸）。
// 後台介面語言不同、或繁中譯名有台灣／香港兩種寫法，所以每國列多個別名；比對時取完全相同的那一行。

export const GROUPS = [
  {
    id: "eu27",
    labelKey: "groupEu27",
    defaultOn: true,
    countries: [
      ["AT", ["奧地利", "Austria"]],
      ["BE", ["比利時", "Belgium"]],
      ["BG", ["保加利亞", "Bulgaria"]],
      ["HR", ["克羅埃西亞", "克羅地亞", "Croatia"]],
      ["CY", ["賽普勒斯", "塞浦路斯", "Cyprus"]],
      ["CZ", ["捷克", "捷克共和國", "Czechia", "Czech Republic"]],
      ["DK", ["丹麥", "Denmark"]],
      ["EE", ["愛沙尼亞", "Estonia"]],
      ["FI", ["芬蘭", "Finland"]],
      ["FR", ["法國", "France"]],
      ["DE", ["德國", "Germany"]],
      ["GR", ["希臘", "Greece"]],
      ["HU", ["匈牙利", "Hungary"]],
      ["IE", ["愛爾蘭", "Ireland"]],
      ["IT", ["義大利", "意大利", "Italy"]],
      ["LV", ["拉脫維亞", "Latvia"]],
      ["LT", ["立陶宛", "Lithuania"]],
      ["LU", ["盧森堡", "Luxembourg"]],
      ["MT", ["馬爾他", "馬耳他", "Malta"]],
      ["NL", ["荷蘭", "Netherlands", "The Netherlands"]],
      ["PL", ["波蘭", "Poland"]],
      ["PT", ["葡萄牙", "Portugal"]],
      ["RO", ["羅馬尼亞", "Romania"]],
      ["SK", ["斯洛伐克", "Slovakia"]],
      ["SI", ["斯洛維尼亞", "斯洛文尼亞", "Slovenia"]],
      ["ES", ["西班牙", "Spain"]],
      ["SE", ["瑞典", "Sweden"]],
    ],
  },
  {
    id: "fr-overseas",
    labelKey: "groupFrOverseas",
    defaultOn: true,
    countries: [
      ["GF", ["法屬圭亞那", "French Guiana"]],
      ["GP", ["瓜地洛普", "瓜德羅普", "Guadeloupe"]],
      ["MQ", ["馬丁尼克", "馬提尼克", "Martinique"]],
      ["RE", ["留尼旺", "留尼汪", "Réunion", "Reunion"]],
      ["YT", ["馬約特", "Mayotte"]],
    ],
  },
  {
    id: "cn",
    labelKey: "groupCn",
    defaultOn: false,
    countries: [["CN", ["中國大陸", "中國", "China", "China mainland", "Mainland China"]]],
  },
];

// 結果清單顯示的名稱：中文介面取第一個別名（台灣譯名），其他語言取第一個拉丁字母開頭的別名。
export function displayName(names, uiLanguage) {
  if (uiLanguage.startsWith("zh")) return names[0];
  return names.find((name) => /^[A-Za-z\u00C0-\u024F]/.test(name)) ?? names[0];
}
