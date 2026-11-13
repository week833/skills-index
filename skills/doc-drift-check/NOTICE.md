# NOTICE

## 這是什麼

`doc-drift-check` 是 week833 的 agent skill，用來找出「所描述的程式在核對之後又變動過」、需要重新查核的 Markdown 文件。檢查程式只提示漂移，不判斷文件內容對錯；已漂移的文件由 agent 對照目前的程式重新查核。內容是一份 `SKILL.md`、一份參考文件、一個只用 Python 標準函式庫的唯讀檢查程式與它的測試；沒有 hook、MCP 伺服器、安裝程式、遙測、自動更新或網路呼叫。

整理日期：2026-11-13。

## 來源

| 項目 | 內容 |
|---|---|
| 上游儲存庫 | [wshobson/agents](https://github.com/wshobson/agents) |
| 路徑 | `plugins/documentation-standards/skills/grounded-vault/`（`SKILL.md` 與 `references/details.md`） |
| Commit | `9c61ab243def98f72da12abd41cfcf5bcd91af9d` |
| 授權 | MIT，全文見 [LICENSE.txt](LICENSE.txt) |
| 授權檔的著作權聲明 | Copyright (c) 2024 Seth Hobson（上游儲存庫根目錄的 `LICENSE`） |
| plugin manifest 的作者 | Niksa Barlovic（`plugins/documentation-standards/.claude-plugin/plugin.json` 與 `.codex-plugin/plugin.json`，授權欄為 MIT） |

本 skill 是改寫版，與上游作者沒有隸屬或背書關係。`LICENSE.txt` 保留上游授權檔的著作權聲明，另加 week833 的一行。上游文件說明它的慣例來自 llm-wiki-loop 專案；本流程沒有讀取該專案。

- 衍生自上游的部分：每份文件記下「查核時的 commit 與監看路徑」，再用 git 比較該 commit 與目前版本，判斷文件是否需要重新查核。
- 本版新寫的部分：指紋格式、`scripts/check_doc_drift.py`、`scripts/test_check_doc_drift.py`、`references/fingerprint-format.md` 與 `SKILL.md` 的工作流。

## 與上游的差異

1. 移除 raw／wiki／archive 三層知識庫、`index.md`、`log.md`，以及頁首的 Raw 與 Status 欄位。
2. 移除數字與引文的對照檢查程式。
3. 移除把過期頁面搬到 `archive/` 的流程、pre-commit hook 與 CI 關卡。
4. 指紋改為一行 HTML 註解，一份文件可有多行；`repo` 名稱可對應到其他儲存庫的本機 clone。上游的範例只處理單一儲存庫。
5. 以新的唯讀檢查程式取代上游內嵌的範例程式：
   - 路徑一律相對於儲存庫頂層，不受執行位置影響；上游必須在同時是 git 頂層的知識庫根目錄執行，否則可能比對不到而沒有任何提示。
   - 路徑在指紋 commit 與 HEAD 都不存在時回報錯誤；上游把打錯的路徑當成沒有漂移。
   - 另外列出未提交的變更（暫存區、未暫存、未追蹤）；上游只比較兩個 commit，看不到未提交的修改。
   - commit 對應不到時說明可能是淺層 clone，並註明儲存庫是不是淺層 clone。
   - 偵測改名，包括改到監看路徑外的檔案。
   - 文件一律以 UTF-8 讀取，可處理 BOM 與 CRLF；輸出強制 UTF-8；git 輸出以 UTF-8 解碼，中文與含空白的路徑保持原樣。
   - 標記寫錯（全形冒號、大寫、少了冒號）或文件是 UTF-16 等非 UTF-8 格式時回報錯誤，不會當成沒有指紋。
   - git 因儲存庫擁有者不同而拒絕讀取（safe.directory）時照實回報，不轉述 git 建議的設定指令。
   - 找不到任何文件時回報錯誤；上游在錯的位置執行時回報 0 個問題並以 0 結束。
   - 結束代碼區分未漂移、漂移與錯誤；上游不加 `--strict` 時一律以 0 結束。
   - git 一律加 `--no-optional-locks`，並把傳輸協定設為不允許，避免改寫 `.git/index` 或下載物件。
6. 圍欄程式碼區塊內的範例不檢查，但列出行號；指紋的儲存庫就是文件所在的儲存庫時，文件自己的變動不算漂移。
7. 新增規則：只在本次確實完成查核後才寫指紋，更新既有指紋要使用者要求更新文件，新增指紋要使用者明確要求；不得為了讓檢查通過而改動指紋或略過文件；重新查核只讀檔案；改完要重跑檢查並附上輸出；「未漂移」不代表正確。
8. 新增界線：專案的 AGENTS.md 與使用者指示優先，不 commit、push，不連網，不搬移或刪除文件，不改 git 設定。
9. 全文改為繁體中文；指令依 PowerShell 語法寫成單行並使用 `python`（未在 Windows 實測，見「未驗證」）。
10. 移除上游批次檢查的 bash／sh 指令、建議用 `npx llm-wiki-loop init` 建立結構的參考實作指引，以及 raw 來源的邊界情況說明（二進位來源、外部網址、大型 raw 檔）。上游把「git 無法比對」當成漂移並要求重新蓋上新指紋；本版改為錯誤，而且只在查核完成並經使用者要求時才更新指紋。

## 已驗證

以下都是本流程於 2026-11-13 在 Linux（Ubuntu 24.04.5 LTS，x86_64）上實際執行的結果，git 版本 2.43.0。指令中的 `python` 指當次列出的直譯器。除非另外註明，都是對目前這一版檔案執行。

1. 在本 skill 資料夾執行 `python -B -m unittest discover -s scripts -p "test_*.py"`：系統的 CPython 3.11.18、3.12.3、3.13.18，以及用 uv 裝在暫時資料夾的 CPython 3.9.25，各 62 個測試全部通過（`OK`，沒有略過）。
2. 在 CPython 3.12.3 的暫時環境（pytest 9.2.0、iniconfig 2.3.1、packaging 26.3、pluggy 1.7.0、pygments 2.21.0）執行 `python -B -m pytest -q -p no:cacheprovider scripts/test_check_doc_drift.py`：`62 passed, 26 subtests passed`。
3. 測試涵蓋：未漂移；監看路徑內與路徑外的已提交變更；未暫存、暫存區、未追蹤（新資料夾內的檔案逐一列出）；被 `.gitignore` 忽略的檔案；刪除、改名（含改到監看路徑外）、暫存區的改名、類型改變、合併衝突；`paths=.`；文件本身的變動；未對應的 repo 名稱；對應不到的 commit（含淺層 clone）；打錯的路徑與只存在於未提交變更的路徑；全形逗號與多餘鍵的提示；路徑大小寫；格式錯誤附行號與 15 種錯誤寫法；全形冒號、大寫、少了冒號等 5 種寫錯的標記；程式碼區塊內的標記行（列出行號、不檢查）與沒有結束的區塊；同一文件多個指紋；`repo=.` 且文件在子資料夾、從其他資料夾執行；跨儲存庫對應（含相對路徑、子資料夾、非儲存庫、同名不同路徑、路徑含 `=`）；中文與空白的檔名和資料夾名；第 1 行就是指紋、有 BOM 與 CRLF 的文件；Big5 與 UTF-16 文件；git 因擁有者不同而拒絕讀取儲存庫（用 git 的測試用環境變數 `GIT_TEST_ASSUME_DIFFERENT_OWNER` 模擬，git 不支援時略過）；找不到 git；無法進入的資料夾（替換 `Path.is_dir` 模擬）；`--docs` 的預設值、空值與各種寫法、略過的資料夾、`.MD` 大寫副檔名；`--exclude` 與 `--list-unfingerprinted`；JSON 鍵的順序與直接輸出的 UTF-8 中文；結束代碼與摘要行；中文的命令列說明與參數錯誤、內部錯誤；忽略 `GIT_DIR` 與 `GIT_WORK_TREE`；Windows 形式的 `--repo` 值與反斜線路徑的解析；git 錯誤訊息中網址帳密的遮蔽。
4. 唯讀：
   - 測試在兩個儲存庫（含未提交變更與狀態資訊過期的檔案）執行檢查前後，比對包含 `.git` 在內每個檔案的 SHA-256 與 `git status` 輸出，完全相同；同一情境下一般的 `git status` 會改寫 `.git/index`，表示這個比對抓得到寫入。
   - 以 `strace -f` 追蹤檢查程式與它啟動的 git（兩個儲存庫，含未提交變更與狀態資訊過期的檔案）：除了 `/dev/null` 沒有以寫入模式開啟的檔案，也沒有建立、刪除、改名、改權限或改時間的系統呼叫；git 只執行 `rev-parse`、`ls-tree`、`status`；兩個儲存庫前後的檔案雜湊相同。審查時對修正前的版本做過同樣的追蹤，結果相同。
   - partial clone 測試中，需要缺少的物件時檢查回報錯誤，clone 內的檔案前後相同，沒有下載物件。另以 blob:none 的 partial clone 實測：只有修改，或內容完全相同的改名時正常比對；比對範圍內有刪除加新增或內容有變的改名（在監看路徑外也一樣）時回報錯誤，物件數不變。
5. 非 UTF-8 預設編碼：測試以子行程設定 `LC_ALL=C`，並用 `-X utf8=0` 啟動直譯器；此時預設編碼是 ASCII（`ANSI_X3.4-1968`），輸出的中文訊息與中文路徑仍是正確的 UTF-8。這是本流程能用的、最接近 cp950 Windows 主控台的替代情境，不等於在 Windows 測試。
6. 突變檢查：對檢查程式做 38 種單點修改（審查時用過的 20 種，加上針對本輪修正的 18 種），每一種都至少讓一個測試失敗。草稿階段對修正前的版本做過 24 種，23 種被抓到；沒抓到的是刪除「去掉行尾 CR」的程式行，之後每行都會去掉前後空白，行為不變。
7. git 行為（git 2.43.0，暫時儲存庫）：`git --no-optional-locks status` 不改寫 `.git/index`，一般的 `git status` 會；和工作目錄比較的 `git diff`（加不加 `--no-optional-locks` 都一樣）在狀態資訊過期時改寫 `.git/index`，兩個 commit 之間的 `git diff` 與 `git show` 不會；停用傳輸協定後，partial clone 的 `git diff-tree -M` 失敗而且不下載物件，沒停用時會下載；`git status` 會執行儲存庫設定的 clean filter；從子資料夾用以頂層為準的路徑執行 `git diff`（不加 `-C`），或指定不存在的路徑，都是空輸出、結束代碼 0；只列改名前的路徑時 `git diff` 只顯示刪除，新舊路徑都列時顯示改名。上游的漂移檢查以 `git diff --stat` 是否為空判斷，「與上游的差異」第 5 點中關於上游的敘述，是依上游程式碼閱讀加上這些實測推得，沒有執行上游的程式。
8. 參考文件與 `SKILL.md` 的指令：
   - 第 3 節的兩行指紋放進暫存資料夾的文件，以 `--repo` 對應到 week833/stock（a74eb97）與 week833/finmind-twstock-research-skill（5a8432c）的唯讀 clone 執行：2 個指紋都是未漂移、結束代碼 0；兩個 clone 的檔案（含 `.git`）與檔案清單前後雜湊相同。
   - 第 2 節的範例放進 week833/stock clone 的複本（`repo=.`）：照第 2 節的 `--docs docs` 與 `SKILL.md` 步驟 1 的 `--docs docs README.md`（Linux 寫法）執行，都是未漂移、結束代碼 0；在複本中提交一個監看路徑內的修改後，回報已漂移並列出該檔案，結束代碼 1。
   - 同一複本中，從子資料夾執行步驟 2 的 `git -C <儲存庫> diff a74eb97 HEAD -- programs/single_stock_analysis` 會印出差異，不加 `-C` 時是空的；`git -C <儲存庫> show`、步驟 4 的 `git -C <儲存庫> rev-parse --short=12 HEAD` 與 `git -C <儲存庫> --no-optional-locks status --short` 都可用，而且在狀態資訊過期時沒有改寫 `.git/index`，一般的 `git status` 則改寫了。
9. 用檢查程式掃描本 skill 資料夾：3 份文件、0 個指紋，參考文件程式碼區塊內的 4 行標記只列出、不檢查，結束代碼 0。
10. 擁有者不同的儲存庫：以 root 執行、把暫時儲存庫的擁有者改成其他使用者後，`repo=.` 與 `--repo` 兩種指紋都回報「被 git 拒絕讀取」與 safe.directory，說明沒有改動 git 設定，不含 git 建議的 `git config` 指令，結束代碼 2；隔離用的 git 全域設定檔仍是 0 位元組。
11. 無法進入的資料夾：以 `setpriv` 去掉 root 的權能，資料夾權限設為 644（可列出、不能進入）與 000，在 CPython 3.11.18、3.12.3、3.13.18 都回報執行錯誤、輸出完整的 JSON、結束代碼 2。修正前的版本在 644 的情況會因 `PermissionError` 中斷，沒有任何輸出。
12. 審查時對修正前的版本另做的實測（相關程式本輪沒有修改）：遠端網址含帳密的 partial clone 需要下載物件時，被 https 傳輸限制擋下，錯誤訊息沒有出現網址或帳密；使用者的 git 設定刻意改成 `color.ui=always`、`diff.relative=true`、`status.showUntrackedFiles=no`、`core.quotePath=true` 等時，輸出仍正確，只有暫存區的改名顯示成刪除加新增。
13. 結構檢查：以系統的 CPython 3.11.18 用隔離模式（`-I`）執行本流程的 `validate_skill.py`，輸出 `PASS`。
14. 文字檢查：所有檔案是沒有 BOM 的 UTF-8、LF 換行、結尾有換行，沒有不可見字元；Markdown 與 YAML 的中文行文沒有緊鄰中文的半形標點。
15. 上游資訊：commit 由本機 clone 的 git 資料讀出；上游的 `SKILL.md`、`references/details.md`、授權檔與兩個 plugin manifest 全文讀過。

## 未驗證

- 沒有在 Windows 上執行。PowerShell 指令（本環境沒有 PowerShell，只做過文字檢查）、`<SKILL_DIR>` 路徑的寫法、反斜線路徑與磁碟代號（只由解析程式的單元測試涵蓋）、cp950 主控台與 PowerShell 管線的中文顯示、`--repo` 值含空白時的引號寫法，以及 Git for Windows 的行為（例如 `core.autocrlf`、不分大小寫的檔案系統、擁有者檢查與 `safe.directory`）都沒有實測。
- 沒有在 Codex 內執行：skill 能否載入、會不會自動觸發、`SKILL.md` 會不會被截斷，以及 skill 資料夾在 Codex 中的實際路徑，都沒有確認。
- 沒有在 Claude Code 內以 skill 的形式載入。
- 沒有在使用者的 D:\stock 或任何實際工作中的儲存庫執行，只在唯讀 clone 與它的複本上執行過範例。
- 只測過 git 2.43.0；Python 只測過 3.9.25、3.11.18、3.12.3、3.13.18。
- 擁有者不同的情況只在 Linux 以 root 改擁有者，以及 git 的測試用環境變數模擬過。
- Git LFS 等 filter 在 `git status` 時的實際行為沒有測；只用自訂 filter 確認 `git status` 會執行 clean filter。
- 縮寫 commit 同時對應到多個物件的情況沒有實測；檢查程式只依 `git rev-parse --verify` 失敗回報錯誤。
- 大量檔案改名時的改名偵測沒有測。
