# 📈 股票與交易

所有與股票、交易、市場資料相關的 Skill 與專案集中在此。

[← 回總覽](../README.md)

## 一、台股研究 Skill

### `finmind-twstock-research`

> **用途：用 FinMind 官方 API／Python SDK 的資料研究台股。** 把研究問題自動對應到合適的 FinMind 資料集，產生 REST／Python SDK 查詢，並檢查資料品質、單位與時間點一致性（PIT），最後輸出可重現的研究證據。

- 適用：台股行情、籌碼、基本面、衍生品、總經資料的研究與分析
- 不做：下單、保證報酬、把查詢結果當成正式行情或正式推薦
- ⚠️ 性質：week833 自行整理的**非官方** Skill，與 FinMind 沒有隸屬或背書關係；FinMind 是第三方資料服務
- ⚠️ 連線：只有使用者明確同意、且 token 已安全提供（例如放在環境變數）時才查詢 FinMind API；token 不可寫進 URL、日誌、輸出或 Git
- ⚠️ 時效：內容依 2026-08-28 的 FinMind 官方文件快照整理，資料集、配額與條款可能已變動，使用前要重新查官方來源
- 來源：[finmind-twstock-research-skill/skills/finmind-twstock-research](https://github.com/week833/finmind-twstock-research-skill/tree/main/skills/finmind-twstock-research)（入口 `SKILL.md`）

## 二、AI 交易平台 Skill（AI-Trader）

以下 6 個 Skill 都位於上游 [HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader) 的 `skills/` 目錄（本帳號不另存副本），搭配第三方 AI-Trader 平台（[ai4trade.ai](https://ai4trade.ai)）使用；其中 4 個需註冊取得 token（見下表「讀寫性質」）。

> ⚠️ **只支援美股、加密貨幣與 Polymarket，不支援台股**；交易使用平台的**模擬資金**（註冊預設 10 萬美元）。研究台股請用上面的 `finmind-twstock-research`。

| Skill | 用途 | 讀寫性質 | 來源 |
|---|---|---|---|
| `ai-trader` | **主 Skill：發布交易訊號、追蹤交易者**；其他 5 個 Skill 的入口 | 會寫入平台（需 token） | [skills/ai4trade](https://github.com/HKUDS/AI-Trader/tree/main/skills/ai4trade) |
| `ai-trader-copytrade` | **跟單**：在 AI-Trader 平台上追蹤高手並自動複製其（模擬）部位 | 會寫入平台（需 token） | [skills/copytrade](https://github.com/HKUDS/AI-Trader/tree/main/skills/copytrade) |
| `ai-trader-tradesync` | **同步自己的部位與交易紀錄**給追蹤者 | 會寫入平台（需 token；上傳的部位與交易紀錄會分享給追蹤者） | [skills/tradesync](https://github.com/HKUDS/AI-Trader/tree/main/skills/tradesync) |
| `ai-trader-heartbeat` | **定期輪詢平台通知與任務**（心跳機制，通知的主要接收方式） | 輪詢（需 token；會回報在線狀態） | [skills/heartbeat](https://github.com/HKUDS/AI-Trader/tree/main/skills/heartbeat) |
| `market-intel` | **唯讀市場情報**：財經事件快照、分組新聞，供交易前參考 | 唯讀（讀取 ai4trade.ai 快照） | [skills/market-intel](https://github.com/HKUDS/AI-Trader/tree/main/skills/market-intel) |
| `polymarket-public-data` | **讀取 Polymarket 預測市場**的公開資料與訂單簿價格 | 讀取直接查 Polymarket 公開 API；發布模擬交易時才寫入 AI-Trader（需 token） | [skills/polymarket](https://github.com/HKUDS/AI-Trader/tree/main/skills/polymarket) |

## 三、股票相關工具與參考（非 Skill）

| 專案 | 用途 | 型態 |
|---|---|---|
| [stock](https://github.com/week833/stock) | **一鍵安裝／修復 Windows 股票研究環境**（`D:\stock\GitHub`），整理 39 個可選外部研究來源（37 primary＋2 legacy），預設下載 3 個 core；本身不含股票分析或預測程式 | 工具／安裝包 |
| [stock-mitake-ui-reference](https://github.com/week833/stock-mitake-ui-reference) | **三竹股市介面導航與操作安全規範**（公開包 `2.1.0`，82 項功能語意投影，不宣稱完整覆蓋），供 AI 建立安全的互動層；不是 API、不下單 | 參考文件 |

`stock` 選單提供安裝環境、下載 core 來源、修復路徑、重設 ENV/PATH、開啟已啟用 venv 的終端機與基本檢查。沿用有效的本專案環境；Git 只在 clone 缺少的專案或新外部來源時需要，既有來源會略過。

`stock` 另附 `AI_STOCK_ACTIONS.cmd`：給 AI 代理用的**語意動作入口**（非 Skill，repo 內沒有 `SKILL.md`）。AI 只能用 JSON 指定允許清單內的動作或 workflow（13 個動作、3 個 workflow：`verify-only`、`safe-setup`、`full-install`），不能送任意命令列；執行紀錄寫在 `D:\stock\GitHub\logs\sessions`。

## 使用建議

| 想做的事 | 用哪個 |
|---|---|
| 查台股資料、做研究分析 | `finmind-twstock-research` |
| 看市場新聞與事件 | `market-intel` |
| 發布或跟隨交易訊號 | `ai-trader`、`ai-trader-copytrade`、`ai-trader-tradesync` |
| 在 Windows 建好股票研究環境 | [stock](https://github.com/week833/stock) |
| 讓 AI 代理透過允許清單執行 stock 的安裝與檢查 | [stock](https://github.com/week833/stock) 的 `AI_STOCK_ACTIONS.cmd` |
| 讓 AI 安全操作三竹股市畫面 | [stock-mitake-ui-reference](https://github.com/week833/stock-mitake-ui-reference) |
