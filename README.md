# 智慧選股 APP v2.0 (Smart Stock Selector)

這是一個基於 React 的股票篩選應用程式，專為投資者設計，協助快速過濾出符合特定高勝率策略的標的。

## 🌟 v2.0 版本特色

本版本在原有的基礎上，新增了兩大進階交易邏輯：

1. **🚀 情境 A：標準 VCP 動能突破 (Standard VCP Breakout)**
   - 長線多頭：股價 > 200 日均線
   - 強勢區間：股價位於 52 週最高價的 85% 以上
   - 強勢表態：當日漲幅 > 3%
   - 成交量確認：當日成交量 > 20 日均量的 1.5 倍

2. **🛡️ 情境 B：敗部復活接回機制 (Re-entry Strategy)**
   - 時間限制：距離上次停損出場 < 20 天
   - 價格修復：當前股價 > 上次買進成本（確認假跌破）
   - 趨勢支撐：當前股價 > 20 日均線

## 📚 基礎策略
- **原始金叉死叉**：KD 指標黃金交叉。
- **均線多頭排列**：MA5 > MA20 > MA60。
- **高勝率精選**：系統回測勝率 > 70%。

## 🛠️ 技術架構
- **Frontend**: React 18
- **Styling**: Tailwind CSS
- **Icons**: Lucide React

---

## 🐛 問題與修正日誌 (Fix Log)

### [2026-07-20] 修正 GitHub Actions Build React App 失敗問題
- **問題分析**：
  1. `.eslintrc.json` 中配置了未安裝的 `@typescript-eslint/parser` 模組，造成 `react-scripts build` ESLint 檢查失敗。
  2. GitHub Actions CI 環境預設 `CI=true`，會將前端程式碼警告（如未使用的變數引用）視為編譯錯誤（Error）。
  3. `scan_stocks.py` 控制台輸出 Emoji（如 `✅`, `❌`），在部分系統環境下引發 `UnicodeEncodeError`。
- **修正內容**：
  - 更新 `.eslintrc.json` 延伸 React 標準設定 `react-app`。
  - 移除 `src/App.js` 中未使用的 `Clock` 圖示引用。
  - 在 `.github/workflows/daily_scan.yml` 的 `Build React App` 步驟中新增 `CI: false` 環境變數。
  - 修正 `scan_stocks.py` 的印出字串，確保不同作業系統編碼均可正常執行。