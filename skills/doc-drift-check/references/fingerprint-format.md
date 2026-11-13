# doc-fingerprint 格式與檢查程式

本頁說明指紋格式，以及 `scripts/check_doc_drift.py` 的選項、輸出與限制。檢查程式只用 Python 標準函式庫與 git，目標是 Python 3.9 以上；實測過的版本見第 10 節。

## 1. 格式

一行一個 HTML 註解，鍵的順序固定：

```text
<!-- doc-fingerprint: repo=NAME commit=SHA paths=P1,P2,... verified=YYYY-MM-DD -->
```

| 鍵 | 規則 |
|---|---|
| `repo` | `.` 代表文件所在的儲存庫（從文件的資料夾往上找到的 git 頂層）。其他名稱在執行時用 `--repo 名稱=路徑` 對應到本機 clone；名稱只能用英數字、`.`、`_`、`-`，第一個字元須是英數字。 |
| `commit` | 查核時的 commit，7 到 40 位十六進位字元。新增或更新指紋時，用查核當下執行 `git -C <儲存庫> rev-parse --short=12 HEAD` 的輸出。 |
| `paths` | 逗號分隔、相對於儲存庫頂層的檔案或資料夾。`/` 與 `\` 都可以，一律換成 `/`；可含空白與中文；不能含逗號；每項前後的空白會去掉；不能是絕對路徑、不能以磁碟代號開頭、不能含 `..`；`.` 代表整個儲存庫。 |
| `verified` | 可省略。查核日期（新增或更新指紋時寫當天），須是有效的 YYYY-MM-DD，否則是格式錯誤；只供參考，不影響判斷。 |

- 一份文件可以有任意多行指紋，各自檢查。
- 整行只能是這個註解（前後可有空白），標記只能寫成小寫的 `doc-fingerprint` 緊接半形冒號。
- 標記文字的判定比正確寫法寬：`doc-fingerprint` 後面接冒號（半形或全形，中間可有空白），或跟在 `<!--` 後面（中間可有空白），大小寫不分。在程式碼區塊外，含標記文字卻無法解析的行就是格式錯誤，報告附行號；所以全形冒號、大寫或少了冒號的寫法會回報錯誤，不會被當成沒有指紋。行文中提到這個名稱時，後面不要接冒號。
- 以三個以上反引號或波浪號開頭的圍欄程式碼區塊內的行是範例，不檢查，但含標記文字的行號會列在輸出（「程式碼區塊內的標記行」），結束代碼不受影響；說明格式時把範例放進這種區塊。區塊到文件結尾都沒有結束、而區塊內有標記文字時，回報文件錯誤。
- 文件可以有 UTF-8 BOM 與 CRLF 換行。不是 UTF-8 文字的文件（例如 UTF-16 或 Big5）：位元組中出現 `doc-fingerprint`（不分大小寫，也比對 UTF-16 的寫法）時回報文件錯誤，否則當作沒有指紋。

## 2. 範例：文件描述同一儲存庫的程式

例：D:\stock 的一份說明文件。commit 與路徑取自 week833/stock 的 a74eb97 版，只作示意：

```markdown
# 單股分析流程說明

<!-- doc-fingerprint: repo=. commit=a74eb97 paths=programs/single_stock_analysis,config/shared_data_paths.json verified=2026-11-13 -->
```

在 D:\stock 執行（例；`<SKILL_DIR>` 換成本 skill 資料夾的完整路徑）：

```powershell
python -B "<SKILL_DIR>\scripts\check_doc_drift.py" --docs docs
```

## 3. 範例：索引文件描述其他儲存庫

例：skills-index 的 README.md 記錄兩個儲存庫的核對版本。commit 取自本流程讀到的 clone（week833/stock 的 a74eb97、week833/finmind-twstock-research-skill 的 5a8432c）：

```markdown
<!-- doc-fingerprint: repo=stock commit=a74eb97 paths=AGENTS.md,programs/RUN_ALL_TESTS.cmd verified=2026-11-13 -->
<!-- doc-fingerprint: repo=finmind commit=5a8432c paths=skills/finmind-twstock-research verified=2026-11-13 -->
```

執行時把每個名稱對應到本機 clone 的頂層（路徑為例）：

```powershell
python -B "<SKILL_DIR>\scripts\check_doc_drift.py" --docs README.md --repo stock=D:\stock finmind=D:\repos\finmind-twstock-research-skill
```

- 每個 `--repo` 值只在第一個 `=` 切開，`D:\stock` 的冒號與反斜線不受影響。相對路徑以目前資料夾為準。
- 路徑必須是 clone 的頂層；指到子資料夾或不是 git 工作目錄時，用到這個名稱的指紋回報錯誤。
- 同一個名稱給了兩個不同路徑，是執行錯誤。
- 路徑含空白時，把整個值加雙引號，例如 `--repo "notes=D:\work\my notes"`（未在 Windows 驗證）。

## 4. 監看路徑怎麼選

- 列出文件實際描述的程式、設定與測試，盡量指到具體的檔案或子資料夾；監看整個儲存庫時，任何變動都算漂移。
- 指紋的儲存庫就是文件所在的儲存庫時，這份文件自己的變動不算漂移；同資料夾其他文件的變動仍會算進來，所以不要監看文件所在的資料夾。
- 被 `.gitignore` 忽略的檔案不列入。儲存庫外的資料（例如中央資料）不在 git 裡，檢查不到；這類依賴要寫在文件本文，另外查核。

## 5. 檢查程式做什麼

對每個指紋依序：

1. 找出儲存庫：`repo=.` 用文件資料夾所在的 git 頂層；其他名稱用 `--repo` 給的路徑，而且它必須是 git 工作目錄的頂層。找不到 git、不在 git 工作目錄內，或 git 因為儲存庫的擁有者不是目前的使用者而拒絕讀取（safe.directory 檢查）時，各自回報錯誤；最後一種不會轉述 git 建議的 `git config --global` 指令，檢查程式也不改任何 git 設定。
2. 確認 commit 能對應到唯一的 commit；對應不到時說明可能是打錯、歷史被改寫或淺層 clone 缺少，並註明這個儲存庫是不是淺層 clone。
3. 確認每個路徑在該 commit 或 HEAD 至少一邊存在；兩邊都不存在就是錯誤，打錯的路徑不會被當成未漂移。
4. 已提交的變更：比較 commit 與 HEAD 的整棵樹並偵測改名，列出舊路徑或新路徑落在監看路徑內的檔案。
5. 未提交的變更：分成暫存區、未暫存、未追蹤三類；合併衝突中的檔案以 `U` 列在未暫存。
6. 沒有任何變更是「未漂移（current）」，有變更是「已漂移（drifted）」，任何一步失敗是「錯誤（error）」。

使用的 git 子指令只有 `rev-parse`、`ls-tree`、`diff-tree`、`status`，一律以參數清單執行、不經 shell。每次都加 `--no-optional-locks`，所以 `status` 不改寫 `.git/index`。傳輸協定設為不允許（`protocol.allow=never`，並逐一設定 file、git、ssh、http、https、ext），所以部分 clone（partial clone）缺少物件時，git 不會下載，而是回報錯誤（以 file 協定實測）。執行 git 前會移除 `GIT_DIR`、`GIT_WORK_TREE` 等指定儲存庫位置的環境變數。

## 6. 看差異時保持唯讀

以下為 git 2.43.0 在 Linux 實測：

- 已提交的差異：`git -C <儲存庫> diff <commit> HEAD -- <路徑>`；舊版內容：`git -C <儲存庫> show <commit>:<路徑>`。兩者都不改寫 `.git/index`。`<儲存庫>` 用檢查輸出的「儲存庫」那一行；指紋的 `repo` 是其他名稱時，就是那個 clone。
- 一定要加 `-C <儲存庫>`：路徑以儲存庫頂層為準，在子資料夾執行不加 `-C` 的 `git diff`，或路徑打錯時，輸出是空的、結束代碼仍是 0，看起來像沒有差異。改名的檔案要把舊路徑與新路徑都列進去，只列舊路徑只會看到刪除。
- 未提交的部分：直接讀工作目錄裡的檔案。`git diff HEAD -- <路徑>`、`git diff -- <路徑>` 這類和工作目錄比較的指令，在檔案的狀態資訊過期時會改寫 `.git/index`，加 `--no-optional-locks` 也一樣。
- `git status` 在同樣情況下也會改寫 `.git/index`；加 `--no-optional-locks` 時不會。

## 7. 選項

| 選項 | 說明 |
|---|---|
| `--docs PATH ...` | 要掃描的文件或資料夾，可給多個，也可重複；預設是目前資料夾，會連同被 `.gitignore` 忽略的資料夾（例如放第三方程式的資料夾）一起掃描，所以建議明確列出。資料夾會遞迴尋找副檔名 `.md`、`.markdown`（不分大小寫）的文件，略過 `.git`、`.venv`、`venv`、`node_modules`、`__pycache__`；直接列出的檔案不論副檔名都會讀。值是空字串時是執行錯誤。 |
| `--repo NAME=PATH ...` | 把指紋的 repo 名稱對應到本機 clone 的頂層，見第 3 節。 |
| `--exclude GLOB ...` | 略過符合的文件或資料夾；比對對象是畫面上顯示的路徑、相對於 `--docs` 資料夾的路徑與名稱。`\` 視為 `/`，大小寫視為不同，`*` 也會跨過 `/`；資料夾符合時，底下全部略過。 |
| `--json` | stdout 只輸出一份 JSON 文件。 |
| `--list-unfingerprinted` | 另外列出沒有任何指紋的文件。 |

## 8. 輸出與結束代碼

文字輸出是繁體中文：每份有指紋的文件列出各指紋的行號、狀態、原因、儲存庫、比對範圍與變動檔案，程式碼區塊內的標記行另列行號，最後一行是摘要。stdout 與 stderr 一律用 UTF-8 輸出。原因中引用的 git 訊息是英文原文（git 以 `LC_ALL=C` 執行）；命令列參數錯誤時，stderr 印出中文的用法與錯誤說明，後面附 argparse 的英文原文。

變動檔案的狀態字母：`M` 修改、`A` 新增、`D` 刪除、`R` 改名（顯示為 `舊路徑 -> 新路徑`）、`T` 類型改變、`U` 合併衝突、`??` 未追蹤；其他字母照 git 原樣。

| 結束代碼 | 意義 |
|---|---|
| 0 | 每個指紋都未漂移；完全沒有指紋時也是 0，摘要行會寫「沒有找到任何指紋，未比對任何文件」。 |
| 1 | 至少一個指紋已漂移，而且沒有任何錯誤。 |
| 2 | 至少一個錯誤：指紋錯誤、文件錯誤、執行錯誤（例如 `--docs` 路徑不存在或是空值、找不到任何文件、資料夾無法讀取、`--repo` 格式錯誤）、命令列參數錯誤（此時 stdout 沒有輸出），或程式內部錯誤。 |

## 9. JSON 欄位

鍵的順序固定：

| 欄位 | 內容 |
|---|---|
| `tool`、`format_version` | `"doc-drift-check"`、`1` |
| `exit_code` | 與結束代碼相同 |
| `summary` | `documents_scanned`、`documents_with_fingerprints`、`documents_without_fingerprints`、`document_errors`、`fingerprints`、`current`、`drifted`、`error`、`fenced_lines`、`run_errors`，都是整數 |
| `run_errors` | 執行錯誤訊息的清單 |
| `documents` | 有指紋行、文件錯誤或程式碼區塊內標記行的文件，各有 `path`、`error`（沒有錯誤時為 `null`）、`fingerprints`、`fenced_lines`（程式碼區塊內含標記文字、未檢查的行號） |
| `unfingerprinted` | 沒有指定 `--list-unfingerprinted` 時為 `null`，否則是沒有指紋的文件路徑清單（只有程式碼區塊內標記行的文件也列在這裡） |

`fingerprints` 的每一項：

| 欄位 | 內容 |
|---|---|
| `line`、`text` | 行號（從 1 起算）與該行內容 |
| `repo`、`commit`、`paths`、`verified` | 解析結果；格式錯誤時為 `null`，`paths` 為空清單 |
| `status`、`reason` | `current`、`drifted` 或 `error`；`reason` 是錯誤原因，沒有錯誤時為 `null` |
| `repository`、`commit_full`、`head` | 儲存庫頂層路徑、指紋 commit 與 HEAD 的完整雜湊；無法判定時為 `null` |
| `committed` | 已提交的變更清單 |
| `uncommitted` | `staged`、`unstaged`、`untracked` 三個清單 |

每筆變更有 `status`（狀態字母）、`path`、`old_path`（改名時的舊路徑，否則為 `null`）。文件路徑照 `--docs` 給的形式（相對或絕對），以 `/` 分隔。

## 10. 限制

- 「未漂移」不代表正確：文件可能在記指紋時就寫錯，也可能依賴沒有監看的路徑或儲存庫外的資料。
- 檢查不讀數字或引文，也不比對文件內容與程式。
- 淺層 clone 可能沒有指紋的 commit，此時回報錯誤，不會自動補抓。部分 clone 在需要缺少的物件時也回報錯誤：已提交的變更是比較整棵樹並偵測改名，比對範圍內只要同時有刪除與新增的檔案（不限監看路徑），git 就要讀舊內容判斷是否改名，這個指紋就會是錯誤；只有修改，或內容完全相同的改名，不受影響（git 2.43.0 以 blob:none 的 partial clone 實測）。
- 路徑比對區分大小寫；反斜線一律當成分隔符號，檔名本身含反斜線的檔案無法監看。
- `git status` 在檔案狀態資訊過期時，會執行儲存庫設定的 clean filter（git 2.43.0 以自訂 filter 實測）。這是 git 本身的行為，檢查程式不另外啟動 git 以外的程式。
- 只在 Linux 以 git 2.43.0、Python 3.9.25、3.11.18、3.12.3、3.13.18 測試過。沒有在 Windows 執行過：磁碟代號與反斜線的處理只由解析程式的單元測試涵蓋；Windows 主控台或 PowerShell 管線能否正確顯示 UTF-8 中文，未能確認。
