# week833 Skill 與專案分類索引

依**功能**整理 week833 帳號下所有 GitHub Skill 與專案。股票相關集中在 [`stock/`](stock/README.md)，其餘依功能各自分類。

> 本儲存庫只做**分類索引**，不複製 Skill 原始檔；每個 Skill 都連回唯一來源，避免多份副本內容不同步。

## 分類一覽

| 分類 | 收錄內容 | 說明頁 |
|---|---|---|
| 📈 股票與交易 | 7 個 Skill＋3 個工具／參考專案 | [stock/README.md](stock/README.md) |
| 📊 簡報製作 | 1 個 Skill | [presentation/README.md](presentation/README.md) |
| 🖥️ Windows 桌面自動化 | 1 個工具專案（非 Skill） | [desktop-automation/README.md](desktop-automation/README.md) |
| 🗂️ 索引 | 本儲存庫（原 `week833/week833`） | 本頁 |

## 全部 Skill 速查

| Skill | 一句話用途 | 分類 | 來源 |
|---|---|---|---|
| `finmind-twstock-research` | **用 FinMind 資料研究台股**：選資料集、規劃查詢、檢查資料品質與時間點一致性（非 FinMind 官方 Skill，只供研究） | 📈 股票與交易 | [finmind-twstock-research-skill](https://github.com/week833/finmind-twstock-research-skill/tree/main/skills/finmind-twstock-research) |
| `ai-trader` | **交易訊號平台主 Skill**：發布交易訊號、追蹤交易者 | 📈 股票與交易 | [HKUDS/AI-Trader/skills/ai4trade](https://github.com/HKUDS/AI-Trader/tree/main/skills/ai4trade) |
| `ai-trader-copytrade` | **跟單**：追蹤高手並自動複製其（模擬）部位 | 📈 股票與交易 | [HKUDS/AI-Trader/skills/copytrade](https://github.com/HKUDS/AI-Trader/tree/main/skills/copytrade) |
| `ai-trader-tradesync` | **同步自己的部位與交易紀錄**到跟單平台 | 📈 股票與交易 | [HKUDS/AI-Trader/skills/tradesync](https://github.com/HKUDS/AI-Trader/tree/main/skills/tradesync) |
| `ai-trader-heartbeat` | **定期輪詢平台通知與任務**（心跳機制） | 📈 股票與交易 | [HKUDS/AI-Trader/skills/heartbeat](https://github.com/HKUDS/AI-Trader/tree/main/skills/heartbeat) |
| `market-intel` | **唯讀市場情報**：讀取財經事件快照與分組新聞 | 📈 股票與交易 | [HKUDS/AI-Trader/skills/market-intel](https://github.com/HKUDS/AI-Trader/tree/main/skills/market-intel) |
| `polymarket-public-data` | **讀取 Polymarket 公開市場資料**與訂單簿價格（直接查 Polymarket；發布模擬交易時才經 AI-Trader） | 📈 股票與交易 | [HKUDS/AI-Trader/skills/polymarket](https://github.com/HKUDS/AI-Trader/tree/main/skills/polymarket) |
| `ppt-master` | **生成可編輯 PPTX 簡報**，並支援範本填入、重建與美化既有簡報 | 📊 簡報製作 | [week833/ppt-master/skills/ppt-master](https://github.com/week833/ppt-master/tree/main/skills/ppt-master) |

> ⚠️ 6 個 AI-Trader Skill 來自第三方專案 HKUDS/AI-Trader，配合第三方平台 [ai4trade.ai](https://ai4trade.ai) 使用：**只支援美股、加密貨幣與 Polymarket，不支援台股**，交易使用平台的**模擬資金**。其中 `ai-trader`、`ai-trader-copytrade`、`ai-trader-tradesync`、`ai-trader-heartbeat` 需註冊取得 token；`market-intel` 只唯讀讀取平台快照；`polymarket-public-data` 直接讀 Polymarket 公開 API，只有要把模擬交易發布到 AI-Trader 時才會用到平台。`ai-trader-tradesync` 上傳的部位與交易紀錄會分享給平台上的追蹤者。

> ⚠️ `finmind-twstock-research` 是 week833 自行整理的**非官方** Skill，與 FinMind 沒有隸屬或背書關係；要連 FinMind API 必須先經使用者明確同意並安全提供 token；**只供研究，不下單**。

> `ppt-master` 的來源是本帳號的 Fork，沒有自有修改、停在上游 `5.1.0`；最新版在上游 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)（2026-10-21 為 `6.7.2`），見 [presentation/README.md](presentation/README.md)。

## 全部儲存庫歸類

| 儲存庫 | 用途 | 型態 | 分類 |
|---|---|---|---|
| [stock](https://github.com/week833/stock) | **股票研究環境**的安裝、設定、修復與外部來源索引（另附 AI 語意動作入口） | 工具／安裝包 | 📈 股票與交易 |
| [finmind-twstock-research-skill](https://github.com/week833/finmind-twstock-research-skill) | **FinMind 台股研究 Skill**（非 FinMind 官方） | Skill | 📈 股票與交易 |
| [ai-trader](https://github.com/week833/ai-trader) | **AI 代理交易平台**（內含 6 個交易 Skill；美股／加密貨幣／Polymarket 模擬交易；與上游相同、未修改） | Fork（上游 [HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader)） | 📈 股票與交易 |
| [stock-mitake-ui-reference](https://github.com/week833/stock-mitake-ui-reference) | **三竹股市介面**導航與操作安全參考（公開包 `2.1.0`，82 項） | 參考文件 | 📈 股票與交易 |
| [ppt-master](https://github.com/week833/ppt-master) | **AI 簡報生成** Skill 工具包（停在上游 `5.1.0`，沒有自有修改） | Fork（上游 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)） | 📊 簡報製作 |
| [windows-local-action-recorder](https://github.com/week833/windows-local-action-recorder) | **Windows 本機操作錄製與受控重播** | 工具（非 Skill） | 🖥️ Windows 桌面自動化 |
| [skills-index](https://github.com/week833/skills-index) | **全部 Skill 與儲存庫的功能分類索引**（本儲存庫，原 `week833/week833`） | 文件 | 🗂️ 索引 |

本機配置同步日期：2026-10-07（本次核對的配置與索引）。

查核日期：2026-10-21（核對上述 7 個儲存庫，以及上游 HKUDS/AI-Trader、hugohe3/ppt-master 在 GitHub 上的公開內容）。
