# 📈 股票與交易

所有與股票、交易、市場資料相關的 Skill 與專案集中在此。

[← 回總覽](../README.md)

## 一、台股研究 Skill

### `finmind-twstock-research`

> **用途：用 FinMind 官方資料研究台股。** 把研究問題自動對應到合適的 FinMind 資料集，產生 REST／Python SDK 查詢，並檢查資料品質、單位與時間點一致性（PIT），最後輸出可重現的研究證據。

- 適用：台股行情、籌碼、基本面、衍生品、總經資料的研究與分析
- 不做：下單、保證報酬、把查詢結果當成正式行情或正式推薦
- 來源：[finmind-twstock-research-skill/skills/finmind-twstock-research](https://github.com/week833/finmind-twstock-research-skill/tree/main/skills/finmind-twstock-research)（入口 `SKILL.md`）

## 二、AI 交易平台 Skill（AI-Trader）

以下 6 個 Skill 都位於上游 [HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader) 的 `skills/` 目錄（本帳號的 [ai-trader](https://github.com/week833/ai-trader) 只是未修改的副本），搭配第三方 AI-Trader 平台（[ai4trade.ai](https://ai4trade.ai)，需註冊取得 token）使用。

> ⚠️ **只支援美股、加密貨幣與 Polymarket，不支援台股**；交易使用平台的**模擬資金**（註冊預設 10 萬美元）。研究台股請用上面的 `finmind-twstock-research`。

| Skill | 用途 | 讀寫性質 | 來源 |
|---|---|---|---|
| `ai-trader` | **主 Skill：發布交易訊號、追蹤交易者**；其他 5 個 Skill 的入口 | 會寫入平台 | [skills/ai4trade](https://github.com/HKUDS/AI-Trader/tree/main/skills/ai4trade) |
| `ai-trader-copytrade` | **跟單**：在 AI-Trader 平台上追蹤高手並自動複製其（模擬）部位 | 會寫入平台 | [skills/copytrade](https://github.com/HKUDS/AI-Trader/tree/main/skills/copytrade) |
| `ai-trader-tradesync` | **同步自己的部位與交易紀錄**給追蹤者 | 會寫入平台 | [skills/tradesync](https://github.com/HKUDS/AI-Trader/tree/main/skills/tradesync) |
| `ai-trader-heartbeat` | **定期輪詢平台通知與任務**（心跳機制，通知的主要接收方式） | 輪詢（會回報在線狀態） | [skills/heartbeat](https://github.com/HKUDS/AI-Trader/tree/main/skills/heartbeat) |
| `market-intel` | **唯讀市場情報**：財經事件快照、分組新聞，供交易前參考 | 唯讀 | [skills/market-intel](https://github.com/HKUDS/AI-Trader/tree/main/skills/market-intel) |
| `polymarket-public-data` | **讀取 Polymarket 預測市場**的公開資料與訂單簿價格 | 唯讀 | [skills/polymarket](https://github.com/HKUDS/AI-Trader/tree/main/skills/polymarket) |

## 三、股票相關工具與參考（非 Skill）

| 專案 | 用途 | 型態 |
|---|---|---|
| [stock](https://github.com/week833/stock) | **一鍵安裝／修復 Windows 股票研究環境**（`D:\stock\GitHub`），並整理 36 個外部股票分析來源索引 | 工具／安裝包 |
| [stock-mitake-ui-reference](https://github.com/week833/stock-mitake-ui-reference) | **三竹股市介面導航與操作安全規範**，供 AI 建立安全的互動層；不是 API、不下單 | 參考文件 |
| [ai-trader](https://github.com/week833/ai-trader) | **AI-Trader 平台本體的副本**（與上游相同、未修改；6 個 Skill 的來源已改連上游） | Fork（上游 [HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader)） |

## 使用建議

| 想做的事 | 用哪個 |
|---|---|
| 查台股資料、做研究分析 | `finmind-twstock-research` |
| 看市場新聞與事件 | `market-intel` |
| 發布或跟隨交易訊號 | `ai-trader`、`ai-trader-copytrade`、`ai-trader-tradesync` |
| 在 Windows 建好股票研究環境 | [stock](https://github.com/week833/stock) |
| 讓 AI 安全操作三竹股市畫面 | [stock-mitake-ui-reference](https://github.com/week833/stock-mitake-ui-reference) |
