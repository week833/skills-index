---
name: doc-drift-check
description: "Find Markdown documents that need re-auditing because the code they describe changed after the commit they were verified against. Documents carry one-line doc-fingerprint HTML comments (repository, verified commit, watched paths); a read-only standard-library Python script compares that commit with HEAD through git and lists staged, unstaged and untracked changes separately. The script only signals drift and never judges whether a statement is true; the agent then re-audits drifted documents against the current code. Use when the user asks which documents are stale or must be re-checked after code changes, or asks to record or update a document's verified commit after re-auditing it. 觸發語：哪些文件過期了、文件需要重新查核嗎、程式改了文件還對嗎、檢查文件漂移、更新文件的核對版本。"
---

# 文件漂移檢查

## 目的

找出「所描述的程式在核對之後又變動過」、需要重新查核的 Markdown 文件。每份文件用一行或多行 doc-fingerprint 註解記下「這份文件曾對照哪個儲存庫的哪個 commit、哪些路徑查核過」；檢查程式以唯讀的 git 指令比對該 commit 與 HEAD，另外列出未提交的變更；它只提示漂移，不判斷內容對錯，已漂移的文件由 agent 對照目前的程式重新查核。格式、範例、選項、結束代碼、JSON 欄位與限制見 [fingerprint-format.md](references/fingerprint-format.md)。

## 何時使用、何時不用

- 使用：使用者問哪些文件過期、程式改了之後哪些文件要重新查核；或在重新查核完成後，要求記錄或更新文件的指紋。
- 不用：與程式變動無關的一般文件查核；查數字或引文的出處；沒人要求就替文件加指紋或整理文件。

## 最小工作流

1. 先讀專案的 AGENTS.md。在儲存庫頂層執行唯讀檢查，完整呈現輸出與結束代碼；`--docs` 一律明確列出，不用預設的整個資料夾。`<SKILL_DIR>` 換成本 skill 資料夾的完整路徑，`docs`、`README.md` 為例：
   `python -B "<SKILL_DIR>\scripts\check_doc_drift.py" --docs docs README.md`
   文件描述其他儲存庫時加 `--repo 名稱=路徑`（例：`--repo stock=D:\stock`）。結束代碼 0 表示全部未漂移、1 有漂移且沒有錯誤、2 有錯誤；摘要行寫「沒有找到任何指紋」時，代表什麼都沒比對。在 Linux 把 `\` 換成 `/`。
2. 逐一處理「已漂移」的文件：先列出輸出中的變動檔案（已提交、暫存區、未暫存、未追蹤分開列），再對照目前的程式、測試與 receipt，逐句重新查核文件的敘述。讀程式本身，不以 commit 訊息代替。已提交的差異用 `git -C <儲存庫> diff <commit> HEAD -- <路徑>` 看（`<儲存庫>` 取輸出的「儲存庫」行；改名時新舊路徑都列），未提交的部分直接讀檔案，不用和工作目錄比較的 `git diff`（參考文件第 6 節）。重新查核只讀檔案，不為查核而執行程式、測試、資料更新或傳送；要執行才能確認的敘述先問使用者，沒執行就列為未查核。不讀 `.ENV` 等存放 token 的檔案。
3. 「錯誤」逐項照實回報原因，不猜測修正；git 拒絕讀取儲存庫時，也不改 git 設定、檔案權限或擁有者（例如 git 提示的 safe.directory 例外），由使用者決定。
4. 指紋代表一項聲明：「這份文件已對照這個 commit 查核過」。只在本次工作階段確實完成查核後才寫：更新既有指紋要使用者要求更新這份文件，新增指紋要使用者明確要求記錄指紋；監看路徑有未提交的變更，或受影響的敘述還有未查核的部分時不更新，改為回報。commit 與 verified 的取法見參考文件第 1 節。更新文件時只寫已對照程式、測試或 receipt 核對過的事實，不寫計畫或推測。絕不為了讓檢查通過而改動指紋（更新 commit、刪減監看路徑、刪除指紋行、把指紋移進程式碼區塊）或用 `--exclude` 略過文件。改完重跑步驟 1 的指令並附上輸出（這份文件的指紋應為未漂移），再用 `git -C <儲存庫> --no-optional-locks status --short` 確認只改了授權的檔案。
5. 說明限制：「未漂移」不代表正確，文件可能在記指紋時就寫錯，或依賴沒有監看的路徑、儲存庫外的資料；檢查不讀數字或引文；淺層 clone 可能沒有那個 commit；程式碼區塊內的標記行視為範例，只列出不檢查；`--list-unfingerprinted` 列出沒有指紋的文件。

## 回覆契約

先給結果，再列出：

- 實際執行的指令、結束代碼與摘要行；已漂移與錯誤的項目逐一列出。
- 每份已漂移文件：變動的檔案、已重新查核的敘述與結論（附依據的檔案與行號）、尚未查核的部分。
- 修改的檔案與修改後的驗證指令和輸出（只在使用者要求更新文件時才有）；沒做的事與原因。

## 界線

- 專案的 AGENTS.md 與使用者的直接指示優先於本 skill；有衝突時停下來問使用者。
- 檢查程式本身不寫入任何檔案，只執行唯讀的 git 子指令；`git status` 仍會執行儲存庫設定的 filter（參考文件第 10 節）。本 skill 不修改程式、測試或設定，也不以改文件來改變程式行為。
- 不搬移、改名或刪除文件（過期的也一樣），不建立備份或日期化副本；保留使用者未提交的變更。不 commit、push 或開 PR，除非使用者要求。
- 不 fetch、pull 或 clone，不連網；淺層 clone 缺 commit 時回報，不自行補抓。不安裝套件，不改動任何虛擬環境。
- 不印出或記錄環境變數、token 或含 token 的 URL。
- 不下單、不給買賣建議；重新查核時不把「未漂移」或測試通過寫成模型有效或策略可獲利。
- 本 skill 未在 Windows 或 Codex 內執行過；驗證範圍見 [NOTICE.md](NOTICE.md)。
