# 🧪 量化研究與回測

[← 回總覽](../README.md)

### `residual-edge-analyzer`

> **用途：檢查策略報酬有多少來自基準曝險、多少是殘差 alpha。** 以含截距的 OLS 迴歸，把自備的策略報酬序列（例如每日選股清單換算出的實現報酬）對事先宣告的基準報酬做拆解，輸出含 Newey-West（HAC）t 值、滾動穩定性、替代基準敏感度與情境分解的 JSON／Markdown 報告。

- 適用：手上已經有逐期報酬序列，想知道扣掉大盤、等權全體等基準之後還剩多少
- 不做：不抓資料、不連網、不需金鑰；腳本只用 Python 標準函式庫（Python 3.9 以上），讀一個 CSV 和一個 JSON 設定檔、寫出報告；報告的 `trade_authorization` 固定為 `NOT_AUTHORIZED`，並寫明不授權交易
- 輸入：CSV 每列一期，含 ISO 日期、策略報酬與每個基準的報酬，編碼須為 UTF-8；JSON 設定檔須為不帶 BOM 的 UTF-8
- 資料量：預設少於 60 期（或少於參數個數的 10 倍）時判定為 `INSUFFICIENT_EVIDENCE`；日頻的滾動穩定性檢查需要 74 期（視窗 63 期、至少 12 個視窗）；沒有提供替代基準模型時，判定會降為 `RESIDUAL_FRAGILE`
- ⚠️ 成熟度：上游把它標示為 `beta`、`research_only`；隨附的 25 個測試沒有任何一個檢查 HAC 標準誤或 t 值，第一次使用要用相同的落後期數另外核對一次
- ⚠️ 自填聲明：「基準事先宣告」「成本基礎一致」「樣本外」「時間點正確的股票池」都是寫在設定檔裡的聲明，腳本只檢查有沒有填，無法驗證真偽；`ELIGIBLE` 只代表證據齊備，不代表可以交易
- ⚠️ 適用範圍：自動落後期數為 floor(4·(n/100)^(2/9))（60 期為 3、252 期為 4、1,000 期為 6），不適用重疊的多日報酬（例如 63 日），那種情況要改用不重疊的序列或自訂 `hac_lags`；腳本不檢查交易日有沒有缺漏；日頻預設以 252 年化
- 報告語言：英文
- 安裝注意：上游只記載 Claude 的用法（把 `skills/residual-edge-analyzer/` 複製到 `~/.claude/skills/` 或專案的 `.claude/skills/`），沒有 Codex 的安裝說明，資料夾內附 `agents/openai.yaml`；`SKILL.md` 的交接段落提到同一個 repo 的 `backtest-expert`、`signal-postmortem`、`trade-performance-coach`，那只是文字指引、不是相依，不必連帶安裝
- 來源：[tradermonty/claude-trading-skills/skills/residual-edge-analyzer](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/residual-edge-analyzer)（入口 `SKILL.md`；MIT 授權）
- 查核版本：`163ceb4`（2026-11-08）；2026-11-13 上游 `main` 已到 `b4dc71f`，這個資料夾的內容沒有變
