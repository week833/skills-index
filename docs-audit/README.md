# 📝 文件維護與查核

[← 回總覽](../README.md)

兩個都放在本儲存庫的 [`skills/`](../skills)：`doc-drift-check` 改寫自外部上游，`handoff-reader-test` 是原創。

### `doc-drift-check`

> **用途：唯讀找出需要重新查核的文件。** 文件內放一行指紋註解，記下這份文件曾對照哪個儲存庫的哪個 commit、哪些路徑查核過；`scripts/check_doc_drift.py` 以唯讀的 git 子指令比對那個 commit 與目前的 HEAD，把之後已提交的變動，以及暫存區、未暫存、未追蹤的變動分開列出。

- 指紋格式：見下方範例，一行一個，一份文件可以有多行；文件描述其他儲存庫時 `repo` 寫儲存庫名稱，執行時以 `--repo 名稱=路徑` 對應到本機的 clone
- 適用：程式改版後，找出哪些說明文件要重新查核；也能檢查像本索引這樣描述多個儲存庫的文件
- 結束代碼：0 全部未漂移、1 有漂移、2 有錯誤（找不到 commit、監看路徑在 commit 與 HEAD 都不存在、指紋寫錯等）；可加 `--json`
- 不做：不判斷內容對錯（「未漂移」不代表文件正確），不讀數字或引文；檢查程式不寫入任何檔案、不 fetch、不連網；只用 Python 3.9 以上的標準函式庫
- 規則：漂移的文件由 agent 讀程式本身逐句重新查核；指紋只在本次確實查核完成、而且使用者要求時才新增或更新，絕不為了讓檢查通過而改指紋
- ⚠️ 限制：淺層或部分 clone 可能缺少那個 commit 而回報錯誤；`git status` 仍會執行儲存庫設定的 filter（例如 Git LFS）
- 驗證狀態：62 個測試在 Linux 的 git 2.43.0、Python 3.9、3.11、3.12、3.13 上全部通過，另以 `strace` 確認檢查時沒有寫入；沒有在 Windows、PowerShell 或 Codex 執行過
- 來源：本儲存庫 [skills/doc-drift-check](../skills/doc-drift-check)（入口 `SKILL.md`；MIT 授權）
- 改寫自：[wshobson/agents 的 grounded-vault](https://github.com/wshobson/agents/tree/main/plugins/documentation-standards/skills/grounded-vault)（`9c61ab2`；MIT），只沿用「文件記下核對 commit 與監看路徑，用 git 比對」的構想。拿掉 raw／wiki／archive 目錄結構、數字與引文檢查器、搬移過期頁面與 pre-commit hook；檢查程式與測試重新撰寫，修正上游範例「監看路徑寫錯時當成未漂移」「看不到未提交的變更」「讀檔沒有指定 UTF-8」等問題，詳見 [NOTICE.md](../skills/doc-drift-check/NOTICE.md)

指紋範例（放在程式碼區塊內的這一行只是範例，檢查程式不會把它當成指紋）：

```text
<!-- doc-fingerprint: repo=. commit=a74eb97 paths=programs/single_stock_analysis verified=2026-11-13 -->
```

### `handoff-reader-test`

> **用途：測試交接文件能否讓只看過它的讀者接手。** 主代理先依查證過的來源寫好 5 到 8 題與參考答案，再交給一位不帶對話內容的讀者一次作答；讀者只憑文件回答並照抄依據的原句，找不到就寫「文件沒寫」。比對後把缺口分成缺漏、含糊、矛盾、過期回報，並附建議文字。

- 適用：`docs\HANDOFF.md`、ADR，或寫給下一個工作階段的 README
- 不做：預設唯讀、只提建議；使用者明確要求時才修改文件，而且只寫入查證過的事實。不讀取或輸出 `.ENV`，不執行文件裡寫的指令或「下一步」
- 觸發：只在明確要求時使用（`allow_implicit_invocation: false`）
- ⚠️ 需要子代理：Codex 是否提供不帶對話內容的子代理未能確認；沒有時由使用者另開工作階段擔任讀者，或在報告標示「未做獨立讀者測試」，主代理不得自己作答充當讀者
- ⚠️ 先掃描憑證：交給讀者之前先檢查 token、金鑰、密碼與帶憑證的網址，分不清時當成真的處理，停下來等使用者確認後才繼續
- 驗證狀態：只在 Linux 做過結構與文字檢查；讀者提示詞沒有實際交給子代理跑過，也沒有在 Windows 或 Codex 上執行過
- 來源：本儲存庫 [skills/handoff-reader-test](../skills/handoff-reader-test)（入口 `SKILL.md`；MIT 授權）
- 性質：week833 的原創 Skill。構想來自 [anthropics/skills](https://github.com/anthropics/skills) 的 `doc-coauthoring` 其中的讀者測試階段；該資料夾沒有授權聲明，所以沒有使用它的任何文字，詳見 [NOTICE.md](../skills/handoff-reader-test/NOTICE.md)
