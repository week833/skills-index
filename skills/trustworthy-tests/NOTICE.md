# NOTICE

## 這是什麼

`trustworthy-tests` 是 week833 的 agent skill，用在替研究程式（pandas、numpy、scikit-learn、時點邏輯、資料驗證器）撰寫或修改測試：先看到測試因為預期的原因失敗、預期值獨立推導、前視有專門的測試。內容是一份 `SKILL.md`、兩份參考文件與一個可執行的 pytest 範例；沒有 hook、MCP 伺服器、安裝程式、遙測、自動更新或網路呼叫。

整理日期：2026-11-13。

## 來源

| 項目 | 內容 |
|---|---|
| 上游儲存庫 | [obra/superpowers](https://github.com/obra/superpowers) |
| 路徑 | `skills/test-driven-development/`（`SKILL.md` 與 `writing-good-tests.md`） |
| Commit | `22f0b463e7a5e579904dd6211a520321035526f7`（標籤 `v7.0.2` 指向這個 commit） |
| 授權 | MIT，全文見 [LICENSE.txt](LICENSE.txt) |
| 著作權人 | Copyright (c) 2025 Jesse Vincent |

本 skill 是改寫版，與上游作者沒有隸屬或背書關係。

- 衍生自上游的部分：`SKILL.md` 的「先看到失敗、再寫最少的程式讓它通過」流程；`references/expected-values.md` 改寫自 `writing-good-tests.md`。
- 本版新增、上游沒有的部分：`references/pit-test-patterns.md`、`examples/test_pit_patterns.py`，以及下列差異中標為「新增」的內容。

## 與上游的差異

1. 觸發範圍縮小。上游在實作任何功能、修錯、重構或行為變更之前都啟用，例外要問使用者；本版只在使用者要求撰寫或修改測試，或已同意測試屬於行為變更的一部分時使用，只要分析或診斷時不用。上游「沒有測試就不修錯」改為：使用者只要求修正時，在修正之前提議加回歸測試，同意才加。
2. 移除所有「先寫了程式就刪除重寫」的規定，包括「Delete it. Start over」「Delete means delete」與「探索用的程式要丟掉」。既有程式一律保留；紅燈改由經使用者同意的突變檢查取得。
3. 移除「其他測試失敗就立刻修」與「每次都要跑整個專案的測試指令」。本版只跑目標測試；無關的失敗只回報指令與輸出；更大的入口要使用者要求，或專案規則指定。
4. 移除每一輪固定的重構步驟（去重複、改名、抽函式）；本版不主動重構。
5. 移除「替既有程式補測試」。
6. 移除施壓用語與相關段落：「違反字面就是違反精神」「沒有例外」「這是在找藉口」、常見藉口對照表、「紅旗：停下來重來」清單、完成前的勾選清單（含「每個新函式都要有測試」「勾不滿就重來」）、卡住時的對照表，以及結尾的規則段落。本版明訂專案的 AGENTS.md 與使用者的直接指示優先，有衝突就停下來問。
7. 紅燈的標準比上游嚴格。上游要求「測試是失敗而不是出錯，而且因為功能不存在而失敗」；本版只認斷言失敗，而且實際值與預期值都如所料；要新增的名稱還不存在時，先寫回傳明顯錯誤值的空殼。
8. 上游遇到「新測試一跑就通過」時是改測試；本版在既有行為上改用經使用者同意的突變檢查。上游的突變檢查在腦中進行；本版新增實際操作的步驟：徵求同意，以 `git status`（含被忽略的路徑）、`git diff --stat` 與位元組雜湊記錄基準，用反向編輯還原，不使用會丟棄變更的 git 指令，並設 `PYTHONDONTWRITEBYTECODE=1`、帶 `-B` 以免留下快取。另列行程內突變與反例對照兩種不改檔的作法，兩者都回報為「未做突變檢查」並註明做了哪一種。
9. 新增：既有程式上的新測試一跑就失敗時，先重新推導預期值；確定是發現了問題就回報，不改程式，測試的去留由使用者決定。上游沒有這種情況。
10. 上游要求輸出完全乾淨（沒有錯誤與警告）；本版改為警告要列出並說明。
11. `writing-good-tests.md` 的「Tests Ship With the Implementation」一節（以紅燈、綠燈、重構的循環定義「完成」）沒有沿用，其中「只寫行為需要的測試」的意思併入第 1、4 節；快速對照表、「your human partner」的引述，以及對 `superpowers:writing-skills` 的引用也沒有沿用。
12. 範例由 TypeScript／npm 改為 Python／pytest。新增 pandas、numpy、scikit-learn 在手算預期值時容易弄錯的定義，以及三種數值比較工具的預設容差。
13. 新增隔離測試的規則：合成小資料、`tmp_path`、固定種子、明寫編碼、不連網、不讀中央資料、不放真實憑證、不跑正式的訓練流程（在合成小資料上以固定 `random_state` 擬合可以）。
14. 新增時點正確性測試樣式 (a) 到 (h) 與可執行範例。
15. 新增回覆契約：實際指令、失敗輸出、通過輸出、pytest 統計行與退出碼的判讀、警告、直譯器與套件版本，以及貼出輸出前遮蔽 token。
16. 新增界線：不改動虛擬環境、不安裝套件、不印出秘密、不下單、不提供買賣建議；收尾時發現預期以外的變更，不刪除、不還原，交給使用者決定。
17. 全文改為繁體中文。上游的流程圖與 TypeScript 範例都沒有沿用。

## 已驗證

以下都是本流程於 2026-11-13 在 Linux（Ubuntu 24.04.5 LTS，x86_64）上實際執行的結果，包含撰寫、兩次審查與修正階段的執行；範例檔的結果以修正後的版本為準。暫時環境以 uv 建立，指令中的 `python` 指該暫時環境的直譯器；執行 pytest 時都另設環境變數 `PYTHONDONTWRITEBYTECODE=1`。

環境：

- 環境甲：CPython 3.12.3；pandas 2.3.3、numpy 2.5.1、pytest 9.2.0、python-dateutil 4.0.0、pytz 2026.6、tzdata 2026.6、iniconfig 2.3.1、packaging 26.3、pluggy 1.7.0、pygments 2.21.0。
- 環境乙（使用者 `TWNextDayTop10/requirements.txt` 的釘選版本，加上 pytest）：CPython 3.12.3；duckdb 1.5.5、narwhals 2.26.0、numpy 2.5.1、pandas 2.3.3、python-dateutil 2.9.0.post0、pytz 2026.3.post1、scikit-learn 1.9.1、scipy 1.18.1、six 1.17.0、threadpoolctl 3.7.0、tzdata 2026.4、pytest 9.2.0、joblib 1.6.0、cloudpickle 3.1.2，以及與環境甲相同版本的 iniconfig、packaging、pluggy、pygments。
- 環境丙：CPython 3.13.18；套件版本與環境甲相同。
- 環境丁：CPython 3.11.18；pandas 2.3.3、numpy 2.4.6、pytest 9.2.0，其餘與環境甲相同。numpy 2.5.1 需要 Python 3.12 以上，uv 回報無法在 3.11 上安裝。

結果：

1. 範例檔（33 個測試函式、41 個測試案例）：在本 skill 資料夾的複本內執行 `python -B -m pytest -q -p no:cacheprovider examples/test_pit_patterns.py`，另加 `-W error`、加 `--assert=plain` 各一次；環境甲、乙、丙、丁都是 `41 passed`。環境甲另在 `LC_ALL=C` 與 `-X utf8=0` 下加 `-W error` 執行：`41 passed`。在本資料夾內以環境甲執行一次：`41 passed`，之後沒有 `__pycache__`、`.pytest_cache` 或 `.pyc`。範例只有兩處以標記處理警告：`test_f_fit_check_passes_when_training_window_is_all_nan` 忽略 numpy 的 `RuntimeWarning: Mean of empty slice`，`test_bd_checks_accept_integer_columns_without_dtype_warnings` 把 `FutureWarning` 當成錯誤。
2. 範例的突變檢查（環境甲）：以未收錄的暫用腳本，在範例的複本上逐一做 43 種單點修改（檢查函式、共用的輔助函式與各正確實作），每種各跑一次 `python -B -m pytest -q -p no:cacheprovider`。41 種至少讓一個測試失敗；存活 2 種：拿掉擾動裡的雜訊（這份資料上，放大與變號已經改動每一個未來值），以及把切分檢查的 `>=` 改成 `>`（訓練列與測試列共用一列時改由間隔檢查報錯，只差在訊息）。出貨的檔案只被讀取。
3. `references/expected-values.md` 的 3 個 Python 程式區塊（環境甲）：區塊本身不能單獨執行。暫用腳本把它們抽出，補上替身的 `labels` 模組（`HORIZON = 2`，函式在呼叫時才讀 `HORIZON`）、替身的 `check_forward_return()`（標籤錯時丟出 `wrong label at row 0`）、`panel = make_panel()`，以及從範例匯入的 `forward_return_correct` 與 `make_panel`，再以 `python -B -m pytest -q -p no:cacheprovider -W error` 執行：`6 passed`（3 個區塊、前後確認 `HORIZON` 已復原的 2 個測試，以及 1 個確認第 6.3 節的寫法在檢查本身壞掉時會失敗的測試）。
4. 參考文件中標示「實測」的事實，以未收錄的暫用腳本執行確認：
   - pandas 與 numpy（環境乙；最後兩項在環境甲）：`merge_asof` 的預設值、三種 `direction`、`allow_exact_matches`、未排序時的 `ValueError` 訊息、`by=` 與它對整體時間排序的要求；`rolling(3)` 與 `rolling("3D")`；`shift` 的方向；`Series.std()` 與 `numpy.std()` 的 `ddof` 預設；`pytest.approx`、`assert_allclose`、`assert_frame_equal`、`assert_series_equal` 的預設容差與 NaN 行為；`numpy.allclose` 與 `numpy.isclose` 的 NaN 預設；把小數寫進整數欄時的 `FutureWarning`。
   - pytest 9.2.0（環境甲）：統計行與退出碼表的每一列；在測試函式裡呼叫不存在的函式、在檔案頂端匯入不存在的名稱或模組、回傳錯誤值的空殼三種情況的結果；`xfail(strict=True)` 在測試失敗與意外通過時的結果；上層資料夾的 `conftest.py` 與 `pytest.ini` 的 `addopts` 都會生效；`-B` 與 `-p no:cacheprovider` 不留快取；`monkeypatch.setattr` 在測試結束後復原，以及它改不到預設參數與 `from … import` 取走的複本；`pytest.raises` 沒有 `match=` 時，檢查本身壞掉也會通過。
   - scikit-learn 1.9.1（環境乙）：`TimeSeriesSplit` 的 `gap` 與預設值；`train_test_split` 與 `KFold` 的 `shuffle` 預設；`SimpleImputer` 的 `statistics_`；`StandardScaler` 擬合在中位數補值後的資料上與直接擬合原始列時的 `mean_` 與 `scale_`。
   - git 2.43.0（暫用儲存庫）：`git status --porcelain` 對未追蹤與被忽略檔案的列法，`--ignored --untracked-files=all` 與 `-- 路徑` 的效果；原本就有未提交變更的檔案再被修改時，`git status` 與 `git diff --stat` 的差別；`git hash-object --no-filters` 在反向編輯後相同，在儲存庫外也能用；儲存庫外的 `git status` 退出碼 128；`core.autocrlf=true` 時只改換行符號的情況；`git checkout --`、`git restore`、`git reset --hard`、`git stash` 都讓未提交的變更從檔案中消失。
   - CPython 3.12.3：`__pycache__` 快取在來源檔大小與修改時間（到秒）相同時被沿用（撰寫階段）；只帶 `-B` 時，測試另開的子行程照樣寫出改壞版本的快取，還原後新的行程執行到改壞的值；另設 `PYTHONDONTWRITEBYTECODE=1` 時不寫快取（審查與修正階段各跑一次）。
   - 範例的檢查函式（環境甲）：修正前重現了這些誤報與漏洞：會丟掉列的正確函式被判為前視、正確的 NaT 對應被判為錯、整數欄觸發 `FutureWarning`、全是缺值的訓練窗被判為前視、空的訓練窗丟出 numpy 的 `ValueError`、`ffill().bfill()` 在開頭沒有缺值的資料上兩種檢查都看不到；修正後重跑，誤報消失，開頭缺值的情況被抓到。看整段路徑與同日排名的標籤直接套用 (d) 的檢查會誤報；改成「改變的列不超出第 j-H 到 j 列」後，看整段路徑的正確標籤通過，四種做錯的標籤仍被抓到，完全不看未來價格的標籤也會通過。
   - 撰寫階段（未收錄的暫用測試）：用到同一列的預測，兩種不變性檢查都會通過（審查時也重現）；一次只擾動一欄，可以縮小洩漏來源。
5. `references/expected-values.md` 第 6.2 節的步驟：修正階段依修正後的步驟，在暫用儲存庫（git 2.43.0、環境甲）完整演練一次，受測檔案原本就有未提交的變更。新測試第一次就通過；改一處後測試失敗（`0.1` 對手算的 `0.21`）；反向編輯後雜湊與基準相同；限定路徑、含被忽略檔案的 `git status` 只多出 `?? tests/test_labels.py`；`git diff --stat` 與基準相同；再跑一次通過，沒有留下快取。撰寫階段也以修正前的版本演練過一次。
6. 上游資訊：commit 與標籤由本機 clone 的 git 資料讀出（撰寫與審查階段）；上游兩個檔案與授權檔全文讀過；`LICENSE.txt` 與上游 `LICENSE` 比對，只多了 `Copyright (c) 2026 week833` 一行（修正階段重新比對）。
7. `references/expected-values.md` 第 7 節的例子：讀自 week833/stock 的 a74eb97 版 `programs/RUN_ALL_TESTS.cmd`、`programs/shared/find_python.cmd` 與兩個子套件的 `RUN_TESTS.cmd`，只讀內容，沒有執行。
8. `SKILL.md` 的 frontmatter 與 `agents/openai.yaml`：在另建的 CPython 3.12.3 環境以 PyYAML 6.0.3 的 `safe_load` 讀取，frontmatter 只有 `name` 與 `description` 兩個鍵，`allow_implicit_invocation` 是 `true`。
9. 結構檢查：以系統的 CPython 3.11.18 用隔離模式（`-I`）執行本流程的 `validate_skill.py`，對本資料夾輸出 `PASS`。

## 未驗證

- 沒有在 Windows 上執行。文件裡的指令沒有在 PowerShell 跑過，包括 `$env:PYTHONDONTWRITEBYTECODE='1'; python ...` 這種寫法、`.venv\Scripts\python.exe`、含 `--` 的 git 指令，以及用斜線分隔的相對路徑。
- 沒有在 Codex 內執行。skill 能否被載入、會不會自動觸發、`SKILL.md` 會不會被截斷，都沒有確認。
- 沒有在 Claude Code 內以 skill 的形式載入。
- 沒有在使用者的 stock 專案或它的 `.venv` 裡執行任何東西；範例與該專案既有測試、conftest 是否相容，沒有確認。
- 使用者機器上的 git 版本、`core.autocrlf` 設定與 pytest 版本沒有確認；本文件關於 pytest 統計行與退出碼的敘述以 9.2.0 為準。
- 突變檢查的還原步驟只在 Linux 的暫用儲存庫演練過；Codex 的編輯工具在 Windows 上是否保留換行符號與編碼，沒有確認，所以步驟要求以位元組雜湊驗證。
- 「修改期間載入該檔案的行程會執行到改過的內容」只以新開的 Python 行程匯入改過的檔案確認，沒有用長時間執行的服務或排程測過。
- 截斷與擾動檢查套在 scikit-learn 估計器的訓練與預測上，沒有實測；範例只示範「以過去各列的平均當預測」。
- 繁體中文 Windows 的主控台或管線在預設編碼下，pytest 失敗輸出裡的中文註解如何顯示，沒有確認。
- 範例只在上列四個環境執行過；其他 Python 或套件版本沒有測。
- (d) 對看整段路徑標籤的改寫只以暫用腳本確認，範例沒有示範；同日排名的標籤沒有試過改寫後的檢查。
