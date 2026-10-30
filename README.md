# week833 Skill 與專案分類索引

依**功能**整理 week833 的所有 GitHub 儲存庫，以及會用到的 Skill（含外部上游的 Skill）。股票相關集中在 [`stock/`](stock/README.md)，其餘依功能各自分類。

> 本儲存庫只做**分類索引**，不複製 Skill 原始檔；每個 Skill 都連回唯一來源，避免多份副本內容不同步。

## 分類一覽

| 分類 | 收錄內容 | 說明頁 |
|---|---|---|
| 📈 股票與交易 | 7 個 Skill（1 個自有、6 個來自外部上游 HKUDS/AI-Trader）＋2 個非 Skill 儲存庫（台股分析程式、三竹介面參考） | [stock/README.md](stock/README.md) |
| 📊 簡報製作 | 1 個 Skill | [presentation/README.md](presentation/README.md) |
| 🖥️ Windows 桌面自動化 | 1 個工具專案（非 Skill） | [desktop-automation/README.md](desktop-automation/README.md) |
| 🗂️ 索引 | 本儲存庫（原 `week833/week833`） | 本頁 |

## 全部 Skill 速查

| Skill | 一句話用途 | 注意 | 分類 | 來源 |
|---|---|---|---|---|
| `finmind-twstock-research` | **用 FinMind 資料研究台股**：選資料集、規劃查詢、檢查資料品質與時間點一致性 | 非 FinMind 官方；只供研究、不下單；連網前需使用者同意並安全提供 token | 📈 股票與交易 | [finmind-twstock-research-skill](https://github.com/week833/finmind-twstock-research-skill/tree/main/skills/finmind-twstock-research) |
| `ai-trader` | **AI-Trader 平台主 Skill**：發布交易訊號、追蹤交易者、參加挑戰賽 | 需 token；模擬資金；不支援台股 | 📈 股票與交易 | [HKUDS/AI-Trader/skills/ai4trade](https://github.com/HKUDS/AI-Trader/tree/main/skills/ai4trade) |
| `ai-trader-copytrade` | **跟單**：追蹤高手並自動複製其（模擬）部位 | 需 token；模擬資金；不支援台股 | 📈 股票與交易 | [HKUDS/AI-Trader/skills/copytrade](https://github.com/HKUDS/AI-Trader/tree/main/skills/copytrade) |
| `ai-trader-tradesync` | **同步自己的部位與交易紀錄**給平台上的追蹤者 | 需 token；模擬資金；不支援台股；上傳的資料會分享給追蹤者 | 📈 股票與交易 | [HKUDS/AI-Trader/skills/tradesync](https://github.com/HKUDS/AI-Trader/tree/main/skills/tradesync) |
| `ai-trader-heartbeat` | **定期輪詢平台通知與任務**（心跳機制） | 需 token；不支援台股；會回報在線狀態 | 📈 股票與交易 | [HKUDS/AI-Trader/skills/heartbeat](https://github.com/HKUDS/AI-Trader/tree/main/skills/heartbeat) |
| `market-intel` | **唯讀市場情報**：財經事件看板、分組新聞、總經訊號與個股分析快照 | 不需 token；內容是 ai4trade.ai 產生的快照 | 📈 股票與交易 | [HKUDS/AI-Trader/skills/market-intel](https://github.com/HKUDS/AI-Trader/tree/main/skills/market-intel) |
| `polymarket-public-data` | **讀取 Polymarket 公開市場資料**與訂單簿價格 | 讀取不需 token、直接查 Polymarket；發布模擬交易時才經 AI-Trader（需 token） | 📈 股票與交易 | [HKUDS/AI-Trader/skills/polymarket](https://github.com/HKUDS/AI-Trader/tree/main/skills/polymarket) |
| `ppt-master` | **生成可編輯 PPTX 簡報**，也能套範本、重建與美化既有簡報，或加旁白／動畫、做成旁白自動播放影片 | Fork，沒有自有修改；需先 `pip install` 相依套件；檔案約 1.3 萬個 | 📊 簡報製作 | [week833/ppt-master/skills/ppt-master](https://github.com/week833/ppt-master/tree/main/skills/ppt-master) |

> ⚠️ **AI-Trader 的 6 個 Skill** 來自第三方專案 [HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader)，配合第三方平台 [ai4trade.ai](https://ai4trade.ai) 使用：**只支援美股、加密貨幣與 Polymarket，不支援台股**；交易使用平台的**模擬資金**（預設 10 萬美元）。需要註冊取得 token 的是 `ai-trader`、`ai-trader-copytrade`、`ai-trader-tradesync`、`ai-trader-heartbeat`；`market-intel` 只唯讀讀取平台快照，不需 token；`polymarket-public-data` 讀取時直接查 Polymarket 公開 API，只有要把模擬交易發布到 AI-Trader 時才需要 token。本帳號原有的 ai-trader Fork 已刪除，6 個 Skill 的來源一律連到上游。

> ⚠️ `finmind-twstock-research` 是 week833 自行整理的**非官方** Skill，與 FinMind 沒有隸屬或背書關係；要連 FinMind API 必須先經使用者明確同意並安全提供 token；**只供研究，不下單**。

> `ppt-master` 的來源是本帳號的 Fork，沒有自有修改；2026-10-30 查核時，`main` 與 `v6` 兩個分支都和上游 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 的 `6.8.0`（`5e8856b`）相同，見 [presentation/README.md](presentation/README.md)。

## 全部儲存庫歸類

| 儲存庫 | 用途 | 型態 | 分類 |
|---|---|---|---|
| [stock](https://github.com/week833/stock) | **台股分析與研究程式**（Windows 本機 `D:\stock` 工作區）：單股收盤估計、次日 Top10、Telegram 報告傳送、資料驗證與環境設定；行情資料與全市場分析在 repo 外 | 程式（非 Skill） | 📈 股票與交易 |
| [finmind-twstock-research-skill](https://github.com/week833/finmind-twstock-research-skill) | **FinMind 台股研究 Skill**（非 FinMind 官方） | Skill | 📈 股票與交易 |
| [stock-mitake-ui-reference](https://github.com/week833/stock-mitake-ui-reference) | **三竹股市介面**導航與操作安全參考（公開包 `2.1.0`，82 項） | 參考文件 | 📈 股票與交易 |
| [ppt-master](https://github.com/week833/ppt-master) | **AI 簡報生成** Skill 工具包（與上游 `6.8.0` 相同，沒有自有修改） | Fork（上游 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)） | 📊 簡報製作 |
| [windows-local-action-recorder](https://github.com/week833/windows-local-action-recorder) | **Windows 本機操作錄製與受控重播** | 工具（非 Skill） | 🖥️ Windows 桌面自動化 |
| [skills-index](https://github.com/week833/skills-index) | **全部 Skill 與儲存庫的功能分類索引**（本儲存庫，原 `week833/week833`） | 文件 | 🗂️ 索引 |

外部上游（不屬於本帳號，不列入上表）：[HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader) 是 6 個 AI-Trader Skill 的來源；[hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 是 ppt-master Fork 的上游。本帳號原有的 ai-trader Fork 已刪除，2026-10-30 查核時已不存在。

核對版本：stock `2eb3278`、finmind-twstock-research-skill `5a8432c`、stock-mitake-ui-reference `4caf213`、ppt-master `5e8856b`（`main` 與 `v6`）、windows-local-action-recorder `f4694d2`；上游 HKUDS/AI-Trader `d03ff6c`、hugohe3/ppt-master `5e8856b`。

查核日期：2026-10-30（核對上述 6 個儲存庫，以及上游 HKUDS/AI-Trader、hugohe3/ppt-master 在 GitHub 上的公開內容）。
