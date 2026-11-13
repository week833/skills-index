---
name: trustworthy-tests
description: "Write or change trustworthy tests for research code (pandas, numpy, scikit-learn, point-in-time logic, data validators): each test is seen to fail for the expected reason before the code makes it pass, expected values are derived independently of the code under test, and look-ahead is tested explicitly. Use when the user asks for tests to be written or changed, or asks for a behaviour change and has agreed that tests are part of it. When the user asked only for a fix, propose a regression test before fixing and add it only with consent. Not for read-only reviews, running whole test suites, refactoring, or unrequested tests. 觸發語：寫測試、補測試、改測試、加回歸測試、寫前視測試、把這個測試改得可信。"
---

# 可信的測試（研究程式）

## 目的

讓研究程式（pandas、numpy、scikit-learn、時點邏輯、資料驗證器）的測試值得相信：先看到測試因為預期的原因失敗，程式才讓它通過；預期值獨立於受測程式推導；前視（look-ahead）有專門的測試。本 skill 屬研究用途。

## 何時使用、何時不用

- 使用：使用者要求撰寫或修改測試；或要求改變程式行為，並已同意測試是工作的一部分。
- 使用者只要求修正時：動手修正之前先提議加回歸測試（抓什麼錯、放哪個檔、跑哪個指令）。同意就先寫測試，看到它在未修正的程式上失敗，再修正；不同意就不加，回覆寫明「未加回歸測試」。
- 不使用：使用者只要分析或診斷（唯讀）；沒人要求卻替既有程式補測試；重構；執行整套測試或正式流程。

## 最小工作流

1. 先讀專案的 AGENTS.md。記下開始前的狀態（不另存檔）並原樣保留（路徑為範例）：`git status --porcelain --ignored --untracked-files=all -- src tests` 與 `git diff --stat`。沿用專案既有的測試框架、直譯器、入口與命名；不安裝套件或外掛，缺 pytest 就回報。指令與專案入口的例子見 expected-values.md 第 7 節。
2. 先說出要抓的錯：用一句話寫下「程式被改成什麼樣子時，這個測試應該失敗」。預期值用手算或另一種獨立的方法，不由受測程式算出。細則見 [expected-values.md](references/expected-values.md)。
3. 寫測試，只動授權範圍內的測試檔，新增前確認沒有同名檔。測試要隔離：合成小資料、`tmp_path`、固定種子、明寫 `encoding="utf-8"`，不連網、不讀中央資料、不放真實憑證；數值用容差比較（`pytest.approx`、`assert_allclose`、`assert_frame_equal`）。時點邏輯依 [pit-test-patterns.md](references/pit-test-patterns.md) 選樣式，範例見 [test_pit_patterns.py](examples/test_pit_patterns.py)。
4. 只跑目標測試：新增或修改的測試，以及直接涵蓋被改程式的既有測試檔。PowerShell 單行指令（路徑與名稱為範例，`python` 換成專案自己的直譯器）：
   `$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m pytest -q -p no:cacheprovider tests/test_labels.py::test_label_alignment`
   既有測試先讀過它、上層各資料夾的 conftest.py 與 pytest 設定，確認不會抓資料、傳訊息、跑正式訓練、啟動服務或排程、連網或碰中央資料；無法確認就先問。更大的測試入口只在使用者要求，或專案規則把它列為這類變更的安全檢查時才跑。
5. 紅燈：先看到測試因為斷言而失敗，實際值與預期值都如你所料；匯入、拼字或 fixture 出錯不算（見 expected-values.md 第 6 節）。
   - 新行為（使用者要求新增或改變行為時）：寫程式之前先跑新測試。要新增的名稱還不存在時，先寫回傳明顯錯誤值的空殼，看到斷言失敗再實作。
   - 既有行為（含先寫程式才補測試）：程式原樣保留，不刪除、不重寫。測試一寫就通過不算可信，要經使用者同意做突變檢查（第 6.2 節）：最小的暫時修改、看到測試失敗、改回原文字、以雜湊確認還原。沒有同意就不改程式檔，回覆寫明「未做突變檢查」。
   - 既有程式上的新測試一跑就失敗：先重新手算預期值；預期值沒錯就是發現了問題。回報指令、失敗輸出與判斷，不改程式；測試要保留、先不加或標成預期失敗，由使用者決定（第 6.4 節）。
6. 綠燈。使用者要求改行為時，只寫讓測試通過所需的最少程式，再跑一次看到通過；不順手重構、改名、抽函式或加功能。不為了通過而放寬斷言，也不刪除或跳過既有測試。
7. 無關的失敗只回報指令與輸出，不修，除非使用者要求。
8. 收尾：再跑步驟 1 的兩個指令並對照，只能多出或改動預期的檔案；有預期以外的新檔或變更時，不刪除、不還原，列在回覆中由使用者決定。不 commit、不 push、不開 PR，除非使用者要求。

## 回覆契約

用繁體中文，先給結果，再列出：

- 新增或修改的檔案。
- 每個測試要抓的錯，以及預期值的來源（手算或獨立方法）。
- 紅燈：實際指令與失敗輸出。綠燈：實際指令與通過輸出，含統計行（例如 `3 passed`）。核對通過數等於預期；`skipped`、`deselected`、`no tests ran` 不算通過；有 `warnings` 要列出並說明；退出碼 0 本身不是證據。
- 直譯器路徑，以及 Python、pytest、pandas、numpy 的版本。
- 突變檢查：改了什麼、失敗輸出、還原前後相同的雜湊。沒做就寫「未做突變檢查」與原因；只做了行程內突變時，在括號內註明替換的名稱。
- 沒執行的項目（例如整套測試）與原因、無關的失敗、待決事項。

貼出輸出前確認沒有 token 或含 token 的 URL，有就遮蔽。不把測試通過寫成「模型有效」或「策略能獲利」；它只代表斷言描述的行為成立。

## 界線

- 專案的 AGENTS.md 與使用者的直接指示優先於本 skill；有衝突就停下來問使用者。
- 不刪除、搬移、改名既有的程式、測試或設定；不建立備份或日期化副本；不用 `git checkout --`、`git restore`、`git reset`、`git stash` 還原檔案。
- 不改動任何虛擬環境。未經使用者明確授權，不安裝套件、不重抓資料、不重新訓練、不傳送訊息、不啟動服務或排程、不連網。
- 不印出、不記錄環境變數、token 或含 token 的 URL。
- 不下單，不呼叫券商或交易 API，不給買賣建議、目標價或部位大小。
- 本 skill 未在 Windows 或 Codex 內執行過；驗證範圍見 [NOTICE.md](NOTICE.md)。
