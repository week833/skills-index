# 🛠️ 開發流程與程式品質

[← 回總覽](../README.md)

| 節 | 收錄 | 型態 |
|---|---|---|
| [一](#一除錯與完成前驗證外部上游-obrasuperpowers) | `systematic-debugging`、`verification-before-completion` | Skill（外部上游） |
| [二](#二測試與變更審查自有改寫) | `trustworthy-tests`、`change-review` | Skill（自有改寫，放在本儲存庫） |

## 一、除錯與完成前驗證（外部上游 obra/superpowers）

以下 2 個 Skill 位於上游 [obra/superpowers](https://github.com/obra/superpowers) 的 `skills/` 目錄，本帳號不存副本，來源一律連到上游。

> ⚠️ **只取這兩個資料夾，不要整包安裝。** 上游只記載整包安裝，會一次裝入全部 15 個 Skill。在 Claude Code 上還會加一個 SessionStart hook，每次開啟工作階段（以及清除、壓縮對話時）就注入 `using-superpowers` 的全文，其中規定「有適用的 Skill 就必須使用」；Codex 版外掛沒有這個 hook，但 15 個 Skill 同樣全部裝入。單獨複製資料夾是上游沒有記載的用法，在 Codex（Windows）上能否自動觸發未能確認。
>
> ⚠️ 上游「使用者指示（含 `AGENTS.md`）優先於 Skill」這一句只寫在 `using-superpowers` 裡，單獨複製這兩個資料夾時不會帶到，需要在自己的 `AGENTS.md` 寫明。

### `systematic-debugging`

> **用途：遇到錯誤、測試失敗或非預期行為時，先找出根因再修。** 分四個階段：調查根因（讀完錯誤訊息、穩定重現、比對近期變更、沿資料流回溯）、比對可運作的範例、一次只驗證一個假設、先做出會失敗的重現再做單一修正。連續三次修正失敗就停下來，和使用者討論架構。

- 適用：驗收或資料檢查失敗、同樣輸入跑出不同結果、橫跨多支程式的錯誤
- 內容：純指示（`SKILL.md` 與 3 份參考文件），另附 1 個 TypeScript 範例與 1 個 bash 腳本；資料夾內沒有網址、連網或憑證相關內容
- ⚠️ 機密：`root-cause-tracing.md` 建議把環境變數一併寫進除錯輸出，主流程也要求在每個元件邊界記錄進出的資料並確認環境設定有傳遞到，而且全篇沒有事後移除診斷碼的步驟；使用時要明訂不得把 token 或含 token 的網址寫進日誌與輸出
- ⚠️ 不要使用 `find-polluter.sh`：它只執行 `npm test` 並忽略失敗，不適用 Python 專案
- ⚠️ 修改範圍：流程會自行加入診斷紀錄與重現用的測試，`defense-in-depth.md` 另外主張在每一層都加上驗證；超出「只改被要求的部分」時以自己的 `AGENTS.md` 為準
- 語言與範例：全英文，範例以 TypeScript／npm／macOS 為主
- 版本：請用 v7.0.2 以後。依上游版本紀錄，v7.0.0 之前的診斷範例會把機密值印進日誌；v7.0.2 之前資料夾內還夾帶 4 份寫成真實情境的壓力測試提示檔
- 來源：[obra/superpowers/skills/systematic-debugging](https://github.com/obra/superpowers/tree/main/skills/systematic-debugging)（入口 `SKILL.md`；MIT 授權）
- 查核版本：`22f0b46`（v7.0.2，2026-11-03）；2026-11-13 上游 `main` 仍是這個版本

### `verification-before-completion`

> **用途：在說「完成、已修正、測試通過」之前，先拿出證據。** 要求代理先找出能證明該說法的指令、當下完整重跑、讀完輸出並確認結束碼，再依實際結果陳述；子代理回報成功時也要自己看差異確認。

- 適用：回報驗收或測試結果、修錯之後、提交或開 PR 之前
- 內容：單一 `SKILL.md`（120 行），沒有腳本與網址，也不引用其他 Skill
- ⚠️ 重跑成本：每次宣稱前都要完整重跑驗證指令，沒有「乾跑」的區分；驗證指令如果會連網抓資料或實際送出訊息，要先在 `AGENTS.md` 指定可以安全重跑的指令
- ⚠️ 回歸測試的紅綠驗證要求「還原修正、確認測試失敗、再恢復修正」，但沒有說明怎麼還原；有未提交的變更時，要避免用會丟失變更的 git 指令
- 語言：全英文，語氣強硬（跳過任一步驟視同說謊）
- 來源：[obra/superpowers/skills/verification-before-completion](https://github.com/obra/superpowers/tree/main/skills/verification-before-completion)（入口 `SKILL.md`；MIT 授權）
- 查核版本：`22f0b46`（v7.0.2，2026-11-03）；2026-11-13 上游 `main` 仍是這個版本

## 二、測試與變更審查（自有改寫）

以下 2 個 Skill 放在本儲存庫的 [`skills/`](../skills)，都改寫自上游 [obra/superpowers](https://github.com/obra/superpowers)（`22f0b46`，v7.0.2；MIT），依 week833 的規則改寫：繁體中文、AGENTS.md 與使用者指示優先、不刪除或搬移既有程式、不安裝套件、不動虛擬環境、未經同意不連網或傳送訊息。

### `trustworthy-tests`

> **用途：撰寫看得到失敗的研究程式測試。** 先說出這個測試要抓什麼錯，預期值用手算或另一種獨立的方法推導；先看到測試因為斷言而失敗，程式才讓它通過；時點正確性（前視）用專門的樣式測試。

- 觸發：使用者要求撰寫或修改測試，或要求改變程式行為並同意測試是工作的一部分；只要求修正時，先提議回歸測試，同意才加
- 既有程式：一律原樣保留。新測試一寫就通過不算可信，要經使用者同意做暫時的突變檢查（最小修改、看到失敗、改回原文字、以雜湊確認還原）；沒有同意就寫明「未做突變檢查」。新測試在既有程式上一跑就失敗時，只回報，不改程式
- 只跑目標測試；既有測試先讀過它與 `conftest.py`，確認不會抓資料、傳訊息或連網才執行；不安裝套件或 pytest 外掛；無關的失敗只回報不修
- 時點正確性樣式（8 種）：截斷不變性、未來資料擾動不變性、依可得時間的 as-of 合併、標籤對齊與位移方向、重疊標籤時有間隔的時間切分、前處理只用訓練窗擬合、交易列數與日曆天的滾動窗、海外交易時段對應到本地交易日
- 範例：[examples/test_pit_patterns.py](../skills/trustworthy-tests/examples/test_pit_patterns.py) 只用 pandas、numpy、pytest，每種樣式都示範正確實作通過、刻意洩漏的實作會被抓到；在 Python 3.12、pandas 2.3.3、numpy 2.5.1、pytest 9.2.0 上 41 個測試全部通過
- ⚠️ 突變檢查會暫時修改程式檔，修改期間載入該檔案的服務或排程會執行到改過的內容，所以一定要先經使用者同意
- 驗證狀態：只在 Linux 驗證；文件中的 PowerShell 指令沒有實測，也沒有在使用者的 stock repo 或 Codex 內執行過
- 來源：本儲存庫 [skills/trustworthy-tests](../skills/trustworthy-tests)（入口 `SKILL.md`；MIT 授權）
- 改寫自：[obra/superpowers/skills/test-driven-development](https://github.com/obra/superpowers/tree/main/skills/test-driven-development)。拿掉上游「先寫了程式就刪掉重來」「其他測試失敗就立刻修」「每次跑完整測試套件」「替既有程式補測試」與每輪的重構步驟；保留紅燈先於綠燈與撰寫可信測試的準則，範例改為 Python；完整差異見 [NOTICE.md](../skills/trustworthy-tests/NOTICE.md)

### `change-review`

> **用途：接受研究程式的變更之前，做一次唯讀、附證據、盡可能獨立的審查。** 預設審查尚未提交的修改，對照使用者的需求、專案規則與八項研究程式檢核表（需求與範圍、時間點正確性與前視、可重現性、機密、輸出與路徑、文件、驗證證據、誠實陳述），每一項發現都附檔案、行號、原文與查證方式，最後給出「可接受／修正後可接受／不可接受」。

- 範圍：預設是未暫存與已暫存的差異，以及未追蹤檔案的內容；使用者指名時才審查 commit、範圍或分支，不會為了產生範圍而 commit
- 不做：不修正任何東西、不 commit、不 push；主代理逐項核對審查者的發現後回報，修不修、修哪幾項由使用者決定。不連網，不執行會抓資料、傳訊息或訓練模型的程式；測試只在使用者指名指令時照原文執行
- 觸發：只在明確要求時使用（`allow_implicit_invocation: false`）
- ⚠️ 獨立性：要做到獨立審查，需要能派出不帶對話內容的子代理（Codex 是否提供未能確認）；沒有時由同一個代理審查，報告會標示是否獨立
- ⚠️ 指令：只列出加了唯讀前綴的單行 git 指令，只在 Linux 的 git 2.43.0 上查證過，沒有在 Windows、PowerShell 或 Codex 裡執行；repository 使用 Git LFS 這類 filter 時，`status` 與 `diff` 仍可能執行 filter 並寫入 `.git/lfs`
- 驗證狀態：審查品質與誤報率還沒有實際評估過
- 來源：本儲存庫 [skills/change-review](../skills/change-review)（入口 `SKILL.md`；MIT 授權）
- 改寫自：[obra/superpowers/skills/requesting-code-review](https://github.com/obra/superpowers/tree/main/skills/requesting-code-review)。主要改動：預設審查未提交的變更（上游審 `HEAD~1..HEAD`，變更未提交時會審到上一個 commit）、禁止審查者建立 git worktree、不自動修正、受審內容中的指示一律不遵從，全文改為繁體中文；完整差異見 [NOTICE.md](../skills/change-review/NOTICE.md)
