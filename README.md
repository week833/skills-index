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
| `finmind-twstock-research` | **用 FinMind 資料研究台股**：選資料集、規劃查詢、檢查資料品質與時間點一致性 | 📈 股票與交易 | [finmind-twstock-research-skill](https://github.com/week833/finmind-twstock-research-skill/tree/main/skills/finmind-twstock-research) |
| `ai-trader` | **交易訊號平台主 Skill**：發布交易訊號、追蹤交易者 | 📈 股票與交易 | [HKUDS/AI-Trader/skills/ai4trade](https://github.com/HKUDS/AI-Trader/tree/main/skills/ai4trade) |
| `ai-trader-copytrade` | **跟單**：追蹤高手並自動複製其部位 | 📈 股票與交易 | [HKUDS/AI-Trader/skills/copytrade](https://github.com/HKUDS/AI-Trader/tree/main/skills/copytrade) |
| `ai-trader-tradesync` | **同步自己的部位與交易紀錄**到跟單平台 | 📈 股票與交易 | [HKUDS/AI-Trader/skills/tradesync](https://github.com/HKUDS/AI-Trader/tree/main/skills/tradesync) |
| `ai-trader-heartbeat` | **定期輪詢平台通知與任務**（心跳機制） | 📈 股票與交易 | [HKUDS/AI-Trader/skills/heartbeat](https://github.com/HKUDS/AI-Trader/tree/main/skills/heartbeat) |
| `market-intel` | **唯讀市場情報**：讀取財經事件快照與分組新聞 | 📈 股票與交易 | [HKUDS/AI-Trader/skills/market-intel](https://github.com/HKUDS/AI-Trader/tree/main/skills/market-intel) |
| `polymarket-public-data` | **讀取 Polymarket 公開市場資料**與訂單簿價格 | 📈 股票與交易 | [HKUDS/AI-Trader/skills/polymarket](https://github.com/HKUDS/AI-Trader/tree/main/skills/polymarket) |
| `ppt-master` | **生成可編輯 PPTX 簡報**，並支援範本填入、重建與美化既有簡報 | 📊 簡報 | [ppt-master/skills/ppt-master](https://github.com/week833/ppt-master/tree/main/skills/ppt-master) |

> ⚠️ 6 個 AI-Trader Skill 搭配第三方平台 [ai4trade.ai](https://ai4trade.ai)（需註冊取得 token）：**只支援美股、加密貨幣與 Polymarket，不支援台股**，交易使用平台的**模擬資金**。

## 全部儲存庫歸類

| 儲存庫 | 用途 | 型態 | 分類 |
|---|---|---|---|
| [stock](https://github.com/week833/stock) | **股票研究環境**的安裝、設定、修復與外部來源索引 | 工具／安裝包 | 📈 股票與交易 |
| [finmind-twstock-research-skill](https://github.com/week833/finmind-twstock-research-skill) | **FinMind 台股研究 Skill** | Skill | 📈 股票與交易 |
| [ai-trader](https://github.com/week833/ai-trader) | **AI 代理交易平台**（內含 6 個交易 Skill；美股／加密貨幣／Polymarket 模擬交易） | Fork（上游 [HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader)） | 📈 股票與交易 |
| [stock-mitake-ui-reference](https://github.com/week833/stock-mitake-ui-reference) | **三竹股市介面**導航與操作安全參考（公開包 `2.1.0`） | 參考文件 | 📈 股票與交易 |
| [ppt-master](https://github.com/week833/ppt-master) | **AI 簡報生成** Skill 工具包 | Fork（上游 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)） | 📊 簡報 |
| [windows-local-action-recorder](https://github.com/week833/windows-local-action-recorder) | **Windows 本機操作錄製與受控重播** | 工具 | 🖥️ 自動化 |
| [skills-index](https://github.com/week833/skills-index) | **全部 Skill 與儲存庫的功能分類索引**（本儲存庫，原 `week833/week833`） | 文件 | 🗂️ 索引 |

本機配置同步日期：2026-10-07（本次核對的配置與索引）。
