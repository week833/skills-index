# 📈 股票與交易

所有與股票、交易、市場資料相關的 Skill 與儲存庫集中在此。

[← 回總覽](../README.md)

| 節 | 收錄 | 市場 | 型態 |
|---|---|---|---|
| [一](#一台股研究-skill) | `finmind-twstock-research` | 台股 | Skill（自有） |
| [二](#二ai-交易平台-skillai-trader外部上游) | AI-Trader 的 6 個 Skill | 美股、加密貨幣、Polymarket（**不支援台股**） | Skill（外部上游） |
| [三](#三股票相關程式與參考非-skill) | `stock`、`stock-mitake-ui-reference` | 台股 | 程式／參考文件（非 Skill） |

## 一、台股研究 Skill

### `finmind-twstock-research`

> **用途：用 FinMind 官方 API／Python SDK 的資料研究台股。** 把研究問題自動對應到合適的 FinMind 資料集，產生 REST／Python SDK 查詢，並檢查資料品質、單位與時間點一致性（PIT），最後輸出可重現的研究證據。

- 適用：台股行情、籌碼、基本面、衍生品、總經資料的研究與分析
- 不做：下單、保證報酬、把查詢結果當成正式行情或正式推薦
- ⚠️ 性質：week833 自行整理的**非官方** Skill，與 FinMind 沒有隸屬或背書關係；FinMind 是第三方資料服務
- ⚠️ 連線：只有使用者明確同意、且 token 已安全提供（例如放在環境變數）時才查詢 FinMind API；token 不可寫進 URL、日誌、輸出或 Git
- ⚠️ 時效：內容依 2026-08-28 的 FinMind 官方文件快照整理，資料集、配額與條款可能已變動，使用前要重新查官方來源。Skill 內的 D:\stock 邊界說明（`references/dstock-boundary.md`）也是 2026-08-28 版，仍以 `dstock_daily` 報告 manifest 作為正式報告依據；`stock` 現行文件則寫明全市場正式分析由外部的 `D:\MIX All` 負責
- 觸發方式：附 Codex 介面設定 `agents/openai.yaml`，允許隱式觸發（使用者提到台股研究時可能自動套用）
- 來源：[finmind-twstock-research-skill/skills/finmind-twstock-research](https://github.com/week833/finmind-twstock-research-skill/tree/main/skills/finmind-twstock-research)（入口 `SKILL.md`）

## 二、AI 交易平台 Skill（AI-Trader，外部上游）

以下 6 個 Skill 都位於上游 [HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader) 的 `skills/` 目錄，搭配第三方平台 [ai4trade.ai](https://ai4trade.ai) 使用。本帳號原有的 ai-trader Fork 已刪除，現在不存副本，來源一律連到上游。

> ⚠️ **只支援美股、加密貨幣與 Polymarket，不支援台股**；交易使用平台的**模擬資金**（預設 10 萬美元）。研究台股請用上面的 `finmind-twstock-research`。

### 會寫入平台（需 token）

| Skill | 用途 | 注意 | 來源 |
|---|---|---|---|
| `ai-trader` | **主 Skill：發布交易訊號、追蹤交易者、參加挑戰賽（個人／團隊）**；也是其他 5 個 Skill 的入口 | 安裝說明是從 ai4trade.ai 下載各 Skill 的 `SKILL.md` 到 `~/.openclaw/skills/clawtrader/` | [skills/ai4trade](https://github.com/HKUDS/AI-Trader/tree/main/skills/ai4trade) |
| `ai-trader-copytrade` | **跟單**：在 AI-Trader 平台上追蹤高手並自動複製其（模擬）部位 | 複製的是平台上的模擬部位 | [skills/copytrade](https://github.com/HKUDS/AI-Trader/tree/main/skills/copytrade) |
| `ai-trader-tradesync` | **同步自己的部位與交易紀錄**給追蹤者 | 上傳的部位與交易紀錄會分享給追蹤者 | [skills/tradesync](https://github.com/HKUDS/AI-Trader/tree/main/skills/tradesync) |
| `ai-trader-heartbeat` | **定期輪詢平台通知與任務**（心跳機制，通知的主要接收方式） | 會回報在線狀態 | [skills/heartbeat](https://github.com/HKUDS/AI-Trader/tree/main/skills/heartbeat) |

### 唯讀（讀取不需 token）

| Skill | 用途 | 注意 | 來源 |
|---|---|---|---|
| `market-intel` | **唯讀市場情報**：財經事件看板、分組新聞、總經訊號、比特幣 ETF 估計資金流與個股分析快照，供交易前參考 | 內容是 ai4trade.ai 後端產生的快照 | [skills/market-intel](https://github.com/HKUDS/AI-Trader/tree/main/skills/market-intel) |
| `polymarket-public-data` | **讀取 Polymarket 預測市場**的公開資料與訂單簿價格 | 讀取直接查 Polymarket 公開 API；只有發布模擬交易時才寫入 AI-Trader（需 token） | [skills/polymarket](https://github.com/HKUDS/AI-Trader/tree/main/skills/polymarket) |

## 三、股票相關程式與參考（非 Skill）

| 儲存庫 | 用途 | 型態 |
|---|---|---|
| [stock](https://github.com/week833/stock) | **台股分析與研究程式**（Windows 本機 `D:\stock` 工作區）：單股收盤估計、次日 Top10、Telegram 報告傳送、資料驗證與環境設定；組成見下表 | 程式（非 Skill） |
| [stock-mitake-ui-reference](https://github.com/week833/stock-mitake-ui-reference) | **三竹股市介面導航與操作安全規範**（公開包 `2.1.0`，82 項功能語意投影，不宣稱完整覆蓋），供 AI 建立安全的互動層；不是 API、不下單 | 參考文件 |

### `stock` 的程式組成

| 組成 | 用途 | 主要入口 |
|---|---|---|
| 統一選單 | **一般使用者的單一起點**：次日 Top10、單股估計、Telegram、唯讀驗證、測試與環境選單，也轉呼叫外部的 MIX 全市場分析與中央資料更新 | [`programs\STOCK_TOOLS.cmd`](https://github.com/week833/stock/blob/main/programs/STOCK_TOOLS.cmd) |
| 單股分析 | **個股 C0 收盤估計報告**：H1（訊號收盤到下一交易日收盤）與 H63（到第 63 個交易日收盤），輸出 PDF／JSON；不連網，只讀中央已發布資料 | [`programs\single_stock_analysis`](https://github.com/week833/stock/tree/main/programs/single_stock_analysis) 的 `1_執行個股分析與產生報告.cmd` |
| 次日 Top10 | **次日 H1 收盤方向與報酬的 Top10 報告**：TWSE／TPEx 官方普通股池，優先用開盤前版模型，不可用時改用 C0；輸出 JSON、CSV、Excel、HTML | 根目錄 `一鍵次日Top10.cmd` → [`TWNextDayTop10`](https://github.com/week833/stock/tree/main/TWNextDayTop10) 的 `RUN_TOP10.cmd` |
| 共用模型與讀取層 | **單股、Top10、MIX、Telegram 共用的資料讀取與 C0 模型**（收盤到收盤的基準模型），以及與 C0 並行、納入前一晚美股的開盤前版 H1 模型 | [`programs\shared`](https://github.com/week833/stock/tree/main/programs/shared)（開盤前版每日入口 `RUN_PREOPEN_DAILY.cmd`） |
| Telegram 傳送 | **個股查詢 Bot 與 MIX 正式報告傳送**（一則摘要＋`MIX_C0.xlsx`）；只傳已驗證的成品，不改分析結果 | [`programs\telegram_report_delivery`](https://github.com/week833/stock/tree/main/programs/telegram_report_delivery) 的 `RUN_COMMAND_BOT.cmd`、`RUN_SEND_MIX_REPORT.cmd` |
| 資料驗證與驗收 | **檢查**中央資料 receipt、共用資料路徑、行情品質（預設不修復）、固定程式路徑與跨系統驗收狀態；都不修改行情資料，但 `RUN_ACCEPTANCE_CHECKS.cmd` 預設會更新驗收快照 `D:\TWStockData\services\acceptance\latest.json`（加 `--structure-only` 則不寫檔） | [`shared_data_management`](https://github.com/week833/stock/tree/main/programs/shared_data_management) 的 `VERIFY_SHARED_DATA_RECEIPT.cmd`；`programs` 下的 `VERIFY_RUNTIME_DATA_PATHS.cmd`、`VALIDATE_MARKET_DATA_QUALITY.cmd`、`VERIFY_STABLE_PROGRAM_PATHS.cmd`；[`cross_system_validation`](https://github.com/week833/stock/tree/main/programs/cross_system_validation) 的 `RUN_ACCEPTANCE_CHECKS.cmd` |
| 環境設定 | **安裝／修復與驗證根目錄 `D:\stock\.venv` 的 Python 套件**（次日 Top10 用自己的 `TWNextDayTop10\.venv`，由 `TWNextDayTop10\SETUP_ENV.cmd` 另外建立），也可設定 Windows 使用者環境變數；另附 36 個外部研究來源的分類說明（5 類，每個來源一份 README，只供方法研究；已發布的 repo 內沒有下載這些來源的程式） | [`programs\environment_setup`](https://github.com/week833/stock/tree/main/programs/environment_setup) 的 `STOCK_SETUP_MANAGER.cmd` |
| 維護 | **受控清理**：先產生預覽清單，明確確認後才套用 | [`programs\maintenance`](https://github.com/week833/stock/tree/main/programs/maintenance) 的 `PLAN_CLEANUP.ps1`、`APPLY_CLEANUP.ps1` |

- ⚠️ 不能單獨執行：程式讀取 `D:\TWStockData` 的中央已發布行情，報告也寫回那裡；全市場正式分析在外部的 `D:\MIX All`，中央資料更新在 `D:\TWStockData\services\market_update`。這些都不在 repo 內
- ⚠️ 不下單：repo 內沒有券商下單程式；Top10 報告寫明命中率只代表收盤方向，以隔日開盤買進 Top10 的平均報酬約為零或為負；單股報告寫明不構成買賣建議
- ⚠️ 憑證：Telegram 的 Token 與 Chat ID 只放在被 Git 忽略的 `.ENV`；個股 Bot 只回應 `.ENV` 設定的私人 Chat ID
- 需求：Windows；根目錄 `D:\stock\.venv` 與 `TWNextDayTop10` 各自的 `.venv`；Top10 的 Excel 匯出另需 Codex runtime 快取中的 Node（`~/.cache/codex-runtimes/…/node.exe`）與專案本地的 `TWNextDayTop10\node_modules\@oai\artifact-tool`（兩者都不在 repo 內）
- AI 代理相關檔案（都不是 Skill，repo 內沒有 `SKILL.md`）：`AGENTS.md` 是給 Codex 等代理在 `D:\stock` 工作的規則（語言、先分析後修改、開工讀取順序、固定入口、不可破壞的契約）；`docs/CODEX_QUICK_REQUESTS.md` 是一行需求範本；`config/mitake_*.json` 是供代理查詢的三竹介面參考目錄（reference-only），與 `stock-mitake-ui-reference` 同屬三竹介面觀察資料

## 使用建議

| 想做的事 | 用哪個 |
|---|---|
| 查台股資料、做研究分析 | `finmind-twstock-research` |
| 產生次日 Top10 報告 | [stock](https://github.com/week833/stock) 的 `一鍵次日Top10.cmd` |
| 產生個股收盤估計報告（H1／H63） | [stock](https://github.com/week833/stock) 的 `programs\single_stock_analysis` |
| 用 Telegram 查個股或傳送 MIX 報告 | [stock](https://github.com/week833/stock) 的 `programs\telegram_report_delivery` |
| 在 Windows 建好或檢查 stock 的 Python 環境 | [stock](https://github.com/week833/stock) 的 `programs\environment_setup\STOCK_SETUP_MANAGER.cmd` |
| 讓 AI 安全操作三竹股市畫面 | [stock-mitake-ui-reference](https://github.com/week833/stock-mitake-ui-reference) |
| 看財經新聞、總經訊號與市場事件（AI-Trader 平台快照） | `market-intel` |
| 查 Polymarket 預測市場資料 | `polymarket-public-data` |
| 在 AI-Trader 發布或跟隨（模擬）交易訊號 | `ai-trader`、`ai-trader-copytrade`、`ai-trader-tradesync` |
