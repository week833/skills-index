# Current-only 計畫修正確認：Claude 審閱 → Codex 確認

**狀態：REVIEW_HANDOFF／NOT_EXECUTION。審閱時點：2026-10-09，依據使用者上傳的 `2026-10-09-current-only-claude-checkpoint-handoff.md`。**

本文件是 Claude 對 Codex 交接檔的審閱結果。Claude 本次在雲端容器執行，只能讀到 `week833/week833` 這個索引 repo；**沒有接觸 `D:\TWStockData`、`D:\TWStockUpdater`、`D:\collect data tool`、`D:\stock` 任何檔案，沒有核對任何 SHA／size／PID／mutex，沒有啟動任何更新或分析入口，沒有修改 Windows 本機任何狀態。** 下列每一項都是「依交接檔文字與本 repo 內容推得」，需要 Codex 以本機 receipt 確認後才算定案。

Codex 請對每一項回覆 `ACCEPT`／`REJECT`／`NEED_INFO` 並附 exact 證據 ref；未回覆的項目視為未確認，不得被當成已修正。

---

## 0. 阻斷項：執行宿主尚未決定

交接檔 §7 要求「Claude 第一個動作須 fresh 核 current head／source／PIN／checkpoint／PID／mutex／prepare」。本 session 是 claude.ai 雲端容器（Linux），GitHub scope 只有 `week833/week833`，沒有 remote-devices／computer-use 工具連到使用者電腦。**§7 步驟 1～6 在此 session 全部不可執行。**

需要使用者或 Codex 先決定其中一種，再談接手：

| 選項 | 內容 | 影響 |
|---|---|---|
| A | Codex 繼續當本機執行者；Claude 只做唯讀審閱（即本文件）。 | 交接檔 §1「原 Codex 下一次 resume／normal GO 已撤回」需要由使用者重新授權 Codex。 |
| B | 使用者在 Windows 本機啟動 Claude Code（CLI／桌面 app），cwd 可達 `D:\`，把交接檔與本文件一起餵入。 | 本機 Claude 需遵守交接檔 §1 的授權範圍與 `D:\` 上的 AGENTS.md；雲端 session 的本文件不等於本機已啟動。 |
| C | 雲端 session 透過 Remote Control／computer-use 連到該電腦。 | 本 session 目前沒有這些工具；需使用者另行設定。 |

在決定之前，交接檔 §7「Claude 接手順序」整節視為**未生效**。

---

## 1. 計畫需修正的項目

### C1. Collect／Central 的 asof 與日曆證據前置條件缺一步

交接檔自己提供的事實：

- §5 表：`official_calendar` route actual max date 為 **2026-09-10**，但 verified-market-calendar-v2 coverage 到 **2026-10-08**，`future_targets_verified=false`。
- §3：Collect 自己的 settings **沒有 expected-asof override**；Central 用 `--expected-asof <fresh_verified_DATE8>`，待 fresh 日曆證據選定。
- §4：Collect `20261009T073235Z-75a037cf` 在 15:32 失敗，`scope_unknown/calendar_descriptor_invalid`，HTTP 0、head 未變。
- §2 規則：「未知不猜 weekday、不補 padding、不因 unknown 發 HTTP」「scope unknown 必須 precise BLOCKED／0 HTTP」。

推論（待確認）：Collect 在 2026-10-09 執行時需要自行推論 asof；若日曆無法證明 10-09 是否為交易 session，依規則就應 BLOCKED／0 HTTP。那麼 15:32 的失敗**可能是規則下的正確結果，而不是程式 bug**；真正缺的是「10-09 的官方日曆證據」。另外 2026-10-10 國慶日逢週六，依台灣補假慣例 10-09（週五）**很可能**是補假休市日，但依交接檔規則不得用慣例猜，必須以官方來源證明。

建議修正：

1. 在 §7 步驟 4 之前加一步：以 active route `0 official_calendar` 在合法 scope 內更新日曆到 **≥ 2026-10-09**（最好涵蓋 H≤63 可證部分），取得 10-09 的 session／休市證明。這是 6 route 之一，不是越域。
2. 明確定義 Collect「無新 session 到期」時的**正確終態**：應是 typed `not_due`／`BLOCKED` 且 exit 0 或專用 code、0 HTTP、head 不變，並留 receipt；若目前程式對此情況回 exit 26 + `calendar_descriptor_invalid`，那才是要修的 owned bug（錯誤分類），不是「0/6 症狀」。
3. Central 的 `<fresh_verified_DATE8>` 預設**維持 `20261008`**，除非官方日曆證明 10-09 為交易日。不得因系統日期是 10-09 就填 `20261009`。
4. 若 10-09 確為休市，則 DU 4772（expected-asof 2026-10-08）、Collect、Central 三者的 asof 一致，不需要新的 scope_id；若 10-09 為交易日，253 窗會前移一天，scope_id 會變，4772 的 resume 須先確認是否仍在原 sealed scope 內。

Codex 需確認：`75a037cf` receipt 的 exact typed reason 是「日曆無 10-09 證據」還是其他；calendar descriptor 失效的 exact 欄位。

### C2. `補齊歷史資料.cmd --from 19900101 --yes` 負向回歸缺 PASS 判準與護欄

交接檔 §7 說這是「拒越域負向回歸，不授權 1990 全史」，但沒有寫預期結果。`--yes` 會跳過確認；若 scope guard 有回歸，這條指令會直接開始全史下載，直接違反使用者「超出目前應用範圍不要下載」。

建議修正：

- 寫明 PASS 判準：exact exit code、typed 拒絕原因、receipt 中 `http_attempts=0`、head 不變、無新 raw 檔。
- 先以網路停用或 dry-run 等價條件跑一次確認 guard 生效，再跑正式負向回歸；或至少先用程式碼層級證據（guard 所在函式與其 F case）確認後再執行。
- 這條與 `collect.py update` 的順序：建議先負向回歸、後正常入口，避免正常入口留下的 lease／prepare 狀態干擾判讀。

### C3. DU resume 範本與其自述要求不符

§7 文字要求「執行時另保存 actual command／PID lineage／stdout-stderr／native exit／summary 與 immutable ACK」，但 PowerShell 範本只用 `&` 直接呼叫並取 `$LASTEXITCODE`，沒有：

- 保存 stdout／stderr 到檔案
- 記錄子 PID、啟動時間、parent PID
- 任何 fresh guards 的具體檢查指令（範本前只寫「fresh guards 全部成立後」）

建議修正：

- 改用 `Start-Process -PassThru -RedirectStandardOutput -RedirectStandardError -Wait` 或 `Start-Transcript`，把 PID／start time／exit 寫入同一收據目錄。
- 在範本前列出 guards 的 exact 檢查：Python 進程清單、兩個 named mutex 的 exact 名稱、`publication_prepare` 檔路徑與 count、`current.pointer` 內容、free bytes；每一項寫下「不成立時只阻該操作」的對應。
- Codex 確認：4772 **原始啟動**時的環境變數（尤其 `STOCK_DAILY_PROFILE`、`STOCK_DAILY_REQUIREMENTS_VERSION`、被清掉的 `TWSTOCKUPDATER_ROOT`／`TWSTOCK_ROOT`／`STOCK_DAILY_REQUIREMENTS_PATH`／`STOCK_DAILY_POLICY_MODULE_PATH`）是否與範本一致。若原 run 的 identity 是從 control 檔讀的而非環境變數，範本多設的變數是否會被判成 scope 變更而 typed blocked。

### C4. `current.pointer` 語意未說明

§3 只說 pointer 內容是 `26adfcb4…`（64 hex），「不是 4772」，所以要明示 `--run-id`。64 hex 不是 run id 格式（run id 形如 `20261009T103142Z-4772c6d4`），比較像 scope_id／content hash。缺的資訊：

- pointer 指向什麼（run、scope、head、還是 lease）
- `resume --run-id` 是否讀它、是否在成功後改寫它
- 若 resume 成功後 pointer 應指向 4772 的終態，誰負責更新；若不應更新，接手者不要「順手修正」

### C5. PIN 數量前後不一致

§3 表：「DU 沒有另造 PIN」，readback 為「兩 private PIN 吻合」（Collect `2a9053…`、Central `b6197d…`）。§7 步驟 1 卻寫「三 current PIN」。需確認 Updater 是否有 PIN 檔；步驟 1 要核的 exact 清單應只列實際存在的檔案與其 SHA，避免接手者去找不存在的第三個 PIN 而誤判不一致。

### C6. HKLM 修改與「未改系統設定」陳述需一致揭露

§4：為修 Windows 符號連結權限 SKIP，「修 HKLM 最小設定後，普通 own Python 真補驗 5 PASS」。§1：「未改系統 PATH／環境變數」。兩者技術上不矛盾（registry 不是 PATH），但 HKLM 修改屬系統層級變更，使用者原始要求裡只授權「設定 Windows 環境變數與 PATH」。最終報告需明列：

- exact key／value name、修改前後值
- 是否由使用者授權、是否可回滾、回滾方式
- 這項是否要列入 §10 完成判定「Windows 符號連結與 own 環境真可用」的證據

### C7. Forward 178 rows 在現行規則下無法成熟，H 階段刪除需另核

§6：178 rows 全部 target-null／ordinary-unknown；§5：`future_targets_verified=false`；§2：未知 future／target 一律 0 HTTP，期限為 target+20 session 或 recorded+180 曆日先到。結果：在 future targets 未證之前，沒有任何 forward 可以結算，只有 recorded+180 硬上限會讓它們過期。

需確認：

- 這是預期行為（forward 在日曆未證 future 前 dormant），不是 bootstrap 漏填 target。
- H 階段若依 expiry 刪除，recorded 時點與 180 天計算的 exact 來源欄位；不能用 activation epoch `2026-10-08T20:03:56` 當 recorded。
- C1 的日曆更新若把 future targets 證到 H≤63，178 rows 中有多少會從 target-null 變成可結算，這會改變 H 的刪除量。

### C8. 本索引 repo 與 `stock` repo 的 README 將與 current-only 狀態衝突

本 repo（`week833/week833`）`stock/README.md` 目前寫：

> 一鍵安裝／修復 Windows 股票研究環境（`D:\stock\GitHub`），整理 39 個可選外部研究來源（37 primary＋2 legacy），預設下載 3 個 core……選單提供安裝環境、下載 core 來源、修復路徑……

交接檔 §1／§8：廣泛研究 repo download／apply／sync 已退休、不復活；39 roots／49 aliases 在 H 實刪清單。兩者在 H 完成後會直接矛盾。

建議：

- H 實刪與 release receipt 完成**之後**，再更新本 repo 與 `week833/stock` 的 README（含「本機配置同步日期：2026-10-07」）；H 之前不要先改文件冒充完成。
- Codex 需確認：「預設下載 3 個 core」那 3 個來源是否屬於「現役引用」而保留，還是也在 39 roots 刪除清單內。這決定 README 要改成「保留 3 個」還是「全部退役」。

### C9. 規範文件只存在於 `D:\`，雲端無法審閱

主計畫（`D:\TWStockData\docs\superpowers\plans\2026-10-09-current-only-cleanup-performance-plan.md`）、五份附件、`plan-manifest.json`、AGENTS.md、checkpoint 小 JSON 都不在任何 git repo。只要執行宿主選 A 或 B，這不是問題；若要讓雲端 Claude 做第二次審閱，需把**規範與 checkpoint 小 JSON**（不含 raw 資料、budget、token、.env）放進可讀位置。這是可選項，不是修正。

---

## 2. 已核對、無需修正的部分

以下只核對交接檔內部算術與引用一致性，不代表檔案內容已驗證：

| 項目 | 核對結果 |
|---|---|
| 53 ready × 253 = 13,409 rows | 一致 |
| 13,409 ＋ 72 檔 16,709 rows ＝ 30,118 ＝ budget candidate_rows | 一致 |
| 53 ＋ 72 ＝ 125 saved raw；raw_bytes 5,595,166 ≈ 「約 5.6 MB」 | 一致 |
| 1414：缺 7 個日期 → 246／253；1435：218／253 → 缺 35 | 一致 |
| canonical head `8047018…`／600,250 B 在 §3、§4 一致；DU 095004 的 `157324…`／599,562 是較早 head | 一致 |
| resume argv 與 run identity（run-id、from 2025-09-22、asof 2026-10-08、requirements_version）對應 | 一致 |
| 失敗歷史表與「不覆寫原 receipt」原則 | 一致，無需改 |

---

## 3. 需 Codex 補答的開放問題

| # | 問題 | 對應項 |
|---|---|---|
| Q1 | `75a037cf` 的 exact typed reason 與 calendar descriptor 失效欄位 | C1 |
| Q2 | 10-09 是否已有任何官方日曆證據；official_calendar route 為何只到 09-10 | C1 |
| Q3 | 4772 原始啟動環境變數清單（從 run 自己的 argv／env capture 取） | C3 |
| Q4 | `current.pointer` 的語意與 resume 的讀寫行為 | C4 |
| Q5 | Updater 是否有 PIN 檔；步驟 1 要核的 exact 檔案清單 | C5 |
| Q6 | HKLM 修改的 key／前後值／授權／回滾 | C6 |
| Q7 | 178 forward rows 的 recorded 欄位與 expiry 計算 | C7 |
| Q8 | 3 個 core 來源是否保留 | C8 |
| Q9 | §5「下一個最小證據：以既存官方 OMD 核 1414 的 7 個日期」是否已有人做；若已做，結果 ref | — |
| Q10 | 使用者是否重新授權 Codex 執行（選項 A），或要走選項 B | §0 |

---

## 4. 建議的修正後執行順序（僅在 §0 宿主決定、§1 修正被 ACCEPT 後生效）

1. Fresh guards（C3 補齊的 exact 檢查）。
2. Route 0 official_calendar 在 scope 內更新到 ≥ 10-09，取得 10-09 session 狀態證據（C1）。
3. 若 10-09 休市：asof 維持 2026-10-08，依原範本 resume 4772；若 10-09 為交易日：先確認 4772 sealed scope 是否仍有效，再決定 resume 或 typed blocked。
4. DU 真 terminal summary＋immutable normal ACK。
5. Collect 負向回歸（C2 判準）→ Collect `update` → Central `daily --expected-asof <依步驟 2 證據>`。
6. 凍結 final head，依交接檔 §7 步驟 5 跑 Single／MIX／Top10／Telegram offline。
7. G release bindings → H 實刪（含 C7 forward expiry 核對）。
8. H 完成後更新本 repo 與 `week833/stock` README（C8）。

其餘交接檔 §2、§5、§6、§8、§9 的限制全部沿用，不在此重複。

---

## 5. 本文件的完成判定

- 本文件完成 ＝ 審閱意見已交付，**不是計畫已修正、不是任何入口已執行、不是 Claude 已在本機接手。**
- 交接檔原件未被修改；本文件不取代它，只附加修正請求。
- 任何一項 Codex 回 REJECT 並附證據，該項以 Codex 證據為準。
