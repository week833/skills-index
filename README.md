# week833 Skill 與專案分類索引

依**功能**整理 week833 的所有 GitHub 儲存庫，以及會用到的 Skill（含外部上游的 Skill，以及依 week833 規則改寫的 Skill）。股票相關集中在 [`stock/`](stock/README.md)，其餘依功能各自分類。

> 外部 Skill 不複製原始檔，一律連回唯一來源，避免多份副本內容不同步。依 week833 規則改寫的 Skill 放在本儲存庫的 [`skills/`](skills) 目錄，本儲存庫就是它們的唯一來源；每個改寫版都附 `NOTICE.md`，記錄出處、與上游的差異，以及哪些已驗證、哪些沒有。

## 分類一覽

| 分類 | 收錄內容 | 說明頁 |
|---|---|---|
| 📈 股票與交易 | 7 個 Skill（1 個自有、6 個來自外部上游 HKUDS/AI-Trader）＋2 個非 Skill 儲存庫（台股分析程式、三竹介面參考） | [stock/README.md](stock/README.md) |
| 🧪 量化研究與回測 | 1 個 Skill（外部上游 tradermonty/claude-trading-skills） | [quant-research/README.md](quant-research/README.md) |
| 🛠️ 開發流程與程式品質 | 4 個 Skill（2 個外部上游 obra/superpowers、2 個自有改寫） | [dev-workflow/README.md](dev-workflow/README.md) |
| 🧩 Skill 製作與評估 | 1 個 Skill（外部上游 kouko/monkey-skills） | [skill-authoring/README.md](skill-authoring/README.md) |
| 📝 文件維護與查核 | 2 個 Skill（1 個自有改寫、1 個自有原創） | [docs-audit/README.md](docs-audit/README.md) |
| 🔬 資料分析與統計建模 | 1 個 Skill（自有改寫） | [data-analysis/README.md](data-analysis/README.md) |
| 📊 簡報製作 | 1 個 Skill | [presentation/README.md](presentation/README.md) |
| 🖥️ Windows 桌面自動化 | 1 個工具專案（非 Skill） | [desktop-automation/README.md](desktop-automation/README.md) |
| 🗂️ 索引 | 本儲存庫（原 `week833/week833`），也放自有改寫的 Skill | 本頁 |

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
| `residual-edge-analyzer` | **把策略報酬拆成基準曝險與殘差 alpha**：對自備的報酬序列做迴歸，輸出含 Newey-West t 值與滾動穩定性的報告 | 不抓資料、不連網、不授權交易；上游標示 beta，測試沒有驗 HAC 標準誤；不適用重疊的多日報酬 | 🧪 量化研究與回測 | [tradermonty/claude-trading-skills/skills/residual-edge-analyzer](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/residual-edge-analyzer) |
| `systematic-debugging` | **出錯時先找根因再修**：重現、比對近期變更、一次只驗證一個假設，連續三次修不好就停下來討論 | 只取單一資料夾、不要整包安裝；參考檔建議把環境變數寫進除錯輸出，須明訂不得印出 token；全英文 | 🛠️ 開發流程與程式品質 | [obra/superpowers/skills/systematic-debugging](https://github.com/obra/superpowers/tree/main/skills/systematic-debugging) |
| `verification-before-completion` | **宣稱完成前先拿出證據**：重跑能證明的指令並讀完輸出，才能說完成、已修正或測試通過 | 只取單一資料夾、不要整包安裝；每次都要完整重跑驗證指令，須先指定可以安全重跑的指令；全英文 | 🛠️ 開發流程與程式品質 | [obra/superpowers/skills/verification-before-completion](https://github.com/obra/superpowers/tree/main/skills/verification-before-completion) |
| `skill-consistency-check` | **找出 Skill 資料夾內互相矛盾的規則**：產出附檔名行號與原文引用的報告，只讀不改 | 需要子代理；上游只在 Claude Sonnet 驗證過；上游只記載一次裝入 6 個 Skill 的整包安裝 | 🧩 Skill 製作與評估 | [kouko/monkey-skills/skill-dev-toolkit/skills/skill-consistency-check](https://github.com/kouko/monkey-skills/tree/main/skill-dev-toolkit/skills/skill-consistency-check) |
| `change-review` | **接受變更前做唯讀、附證據的審查**：預設看尚未提交的修改，對照需求、專案規則與八項研究程式檢核表，最後給出判定 | 自有改寫（上游 obra/superpowers 的 requesting-code-review）；只在明確要求時使用、不修正任何東西；獨立審查需要子代理；未在 Windows 或 Codex 實測 | 🛠️ 開發流程與程式品質 | [skills/change-review](skills/change-review) |
| `trustworthy-tests` | **撰寫看得到失敗的研究程式測試**：先看到測試因斷言失敗再讓它通過，預期值獨立推導，並附 8 種前視（時點正確性）測試樣式與可執行範例 | 自有改寫（上游 obra/superpowers 的 test-driven-development）；不刪除既有程式；突變檢查要先經使用者同意；未在 Windows 或 Codex 實測 | 🛠️ 開發流程與程式品質 | [skills/trustworthy-tests](skills/trustworthy-tests) |
| `doc-drift-check` | **唯讀找出需要重新查核的文件**：依文件內的指紋（核對 commit 與監看路徑）用 git 列出之後的程式變動 | 自有改寫（上游 wshobson/agents 的 grounded-vault）；只提示漂移、不判斷對錯；指紋只在查核完成且使用者要求時更新；未在 Windows 或 Codex 實測 | 📝 文件維護與查核 | [skills/doc-drift-check](skills/doc-drift-check) |
| `handoff-reader-test` | **測試交接文件能否讓只看過它的讀者接手**：先寫好題目與參考答案，再讓不帶對話內容的讀者只憑文件作答，回報缺漏、含糊、矛盾與過期之處 | 自有原創；只在明確要求時使用、預設唯讀；需要子代理，否則改由使用者另開工作階段；讀者提示詞尚未實際跑過 | 📝 文件維護與查核 | [skills/handoff-reader-test](skills/handoff-reader-test) |
| `shap-model-audit` | **稽核已訓練模型用了哪些特徵與特徵組**：以 SHAP 在樣本外期間解釋 scikit-learn 模型，檢查可加性並以 permutation importance 交叉比對 | 自有改寫（上游 K-Dense-AI/scientific-agent-skills 的 shap）；須經同意在 repository 外另建裝有 shap 的環境；只描述模型行為，不是因果或交易證據；只用合成資料驗證過 | 🔬 資料分析與統計建模 | [skills/shap-model-audit](skills/shap-model-audit) |
| `ppt-master` | **生成可編輯 PPTX 簡報**，也能套範本、重建與美化既有簡報，或加旁白／動畫、做成旁白自動播放影片 | Fork，沒有自有修改；需先 `pip install` 相依套件；檔案約 1.3 萬個 | 📊 簡報製作 | [week833/ppt-master/skills/ppt-master](https://github.com/week833/ppt-master/tree/main/skills/ppt-master) |

> ⚠️ **AI-Trader 的 6 個 Skill** 來自第三方專案 [HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader)，配合第三方平台 [ai4trade.ai](https://ai4trade.ai) 使用：**只支援美股、加密貨幣與 Polymarket，不支援台股**；交易使用平台的**模擬資金**（預設 10 萬美元）。需要註冊取得 token 的是 `ai-trader`、`ai-trader-copytrade`、`ai-trader-tradesync`、`ai-trader-heartbeat`；`market-intel` 只唯讀讀取平台快照，不需 token；`polymarket-public-data` 讀取時直接查 Polymarket 公開 API，只有要把模擬交易發布到 AI-Trader 時才需要 token。本帳號原有的 ai-trader Fork 已刪除，6 個 Skill 的來源一律連到上游。

> ⚠️ `finmind-twstock-research` 是 week833 自行整理的**非官方** Skill，與 FinMind 沒有隸屬或背書關係；要連 FinMind API 必須先經使用者明確同意並安全提供 token；**只供研究，不下單**。

> ⚠️ `systematic-debugging` 與 `verification-before-completion` 來自第三方專案 [obra/superpowers](https://github.com/obra/superpowers)：**只取這兩個資料夾，不要整包安裝**。整包會一次裝入 15 個 Skill，在 Claude Code 上還會加一個每次開啟工作階段就注入規則的 hook，見 [dev-workflow/README.md](dev-workflow/README.md)。

> `residual-edge-analyzer`、`systematic-debugging`、`verification-before-completion`、`skill-consistency-check` 都是外部上游的 Skill，本帳號不存副本；各自的限制與安裝注意寫在所屬的分類頁。

> `trustworthy-tests`、`change-review`、`doc-drift-check`、`handoff-reader-test`、`shap-model-audit` 是 week833 依自己的規則（繁體中文、只供研究不下單、token 只放 `.ENV`、先分析後修改、未驗證的事不寫成事實）寫成的 Skill，放在本儲存庫的 [`skills/`](skills)。每一個都經過兩位獨立審查者（規則與安全、技術正確性）查核並修正；都只在 Linux 上驗證過，沒有在 Windows 或 Codex 實際執行過；各自的 `NOTICE.md` 列出已驗證與未驗證的項目。

> `ppt-master` 的來源是本帳號的 Fork，沒有自有修改；2026-10-30 查核時，`main` 與 `v6` 兩個分支都和上游 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 的 `6.8.0`（`5e8856b`）相同，見 [presentation/README.md](presentation/README.md)。

## 全部儲存庫歸類

| 儲存庫 | 用途 | 型態 | 分類 |
|---|---|---|---|
| [stock](https://github.com/week833/stock) | **台股分析與研究程式**（Windows 本機 `D:\stock` 工作區）：單股收盤估計、次日 Top10、Telegram 報告傳送、資料驗證與環境設定；行情資料與全市場分析在 repo 外 | 程式（非 Skill） | 📈 股票與交易 |
| [finmind-twstock-research-skill](https://github.com/week833/finmind-twstock-research-skill) | **FinMind 台股研究 Skill**（非 FinMind 官方） | Skill | 📈 股票與交易 |
| [stock-mitake-ui-reference](https://github.com/week833/stock-mitake-ui-reference) | **三竹股市介面**導航與操作安全參考（公開包 `2.1.0`，82 項） | 參考文件 | 📈 股票與交易 |
| [ppt-master](https://github.com/week833/ppt-master) | **AI 簡報生成** Skill 工具包（與上游 `6.8.0` 相同，沒有自有修改） | Fork（上游 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)） | 📊 簡報製作 |
| [windows-local-action-recorder](https://github.com/week833/windows-local-action-recorder) | **Windows 本機操作錄製與受控重播** | 工具（非 Skill） | 🖥️ Windows 桌面自動化 |
| [skills-index](https://github.com/week833/skills-index) | **全部 Skill 與儲存庫的功能分類索引**（本儲存庫，原 `week833/week833`）；`skills/` 放自有改寫的 Skill | 文件＋Skill | 🗂️ 索引 |

外部上游（不屬於本帳號，不列入上表）：[HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader) 是 6 個 AI-Trader Skill 的來源；[hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 是 ppt-master Fork 的上游；[tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills) 是 `residual-edge-analyzer` 的來源；[obra/superpowers](https://github.com/obra/superpowers) 是 `systematic-debugging` 與 `verification-before-completion` 的來源；[kouko/monkey-skills](https://github.com/kouko/monkey-skills) 是 `skill-consistency-check` 的來源。本帳號原有的 ai-trader Fork 已刪除，2026-10-30 查核時已不存在。

核對版本：stock `a74eb97`、finmind-twstock-research-skill `5a8432c`、stock-mitake-ui-reference `4caf213`、ppt-master `5e8856b`（`main` 與 `v6`）、windows-local-action-recorder `f4694d2`；上游 HKUDS/AI-Trader `d03ff6c`、hugohe3/ppt-master `5e8856b`。2026-11-13 新增的 4 個外部 Skill：tradermonty/claude-trading-skills `163ceb4`、obra/superpowers `22f0b46`（v7.0.2）、kouko/monkey-skills `693cee8`。

查核日期：2026-10-30（核對上述 6 個儲存庫，以及上游 HKUDS/AI-Trader、hugohe3/ppt-master 在 GitHub 上的公開內容）。2026-11-13 新增 4 個外部 Skill 時，查核的是 tradermonty/claude-trading-skills、obra/superpowers、kouko/monkey-skills 這三個上游的對應資料夾；stock 另於 2026-11-13 依 `a74eb97` 重新核對；`skills/` 內 5 個自有改寫 Skill 依據的上游版本（obra/superpowers `22f0b46`、wshobson/agents `9c61ab2`、K-Dense-AI/scientific-agent-skills `2d2065f`）與驗證範圍，記在各自的 `NOTICE.md`；其餘內容沿用 2026-10-30 的查核結果。
