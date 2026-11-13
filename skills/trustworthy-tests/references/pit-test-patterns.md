# 時點正確性（PIT）測試樣式

這些樣式用來測一件事：在時點 t 算出來的值，有沒有用到 t 之後才會知道的資料。每個樣式列出它抓哪一種洩漏、測試想法，以及可執行範例的位置。範例都在 [examples/test_pit_patterns.py](../examples/test_pit_patterns.py)，使用合成小資料與虛構的行事曆。

本頁只講通則，不描述任何既有程式的實作方式。標示「實測」的事實，其版本與平台見 [NOTICE.md](../NOTICE.md) 的「已驗證」。

## 怎麼用

1. 先確認「t」的定義：這個值要在第 t 列的哪個時點使用（例如開盤前或收盤後），當時哪些資料已經可得。同一天的資料算不算未來，由這個定義決定。定義不明時先問使用者，不要自己假設。
2. 依受測程式做的事，從下表選樣式；把範例裡 `check_` 開頭的函式改成呼叫專案的函式，資料仍然用合成小資料。
3. 每個檢查都要證明它會失敗：配一個故意做錯的實作，或做一次突變檢查（見 [expected-values.md](expected-values.md) 第 6 節）。
4. 不變性檢查只說明「沒有用到未來」，不說明算得對；至少再加一兩個手算的預期值。

## 樣式總表

| 樣式 | 抓什麼 | 測試想法 | 範例裡的名稱 |
|---|---|---|---|
| (a) 截斷不變性 | 置中視窗、往回補值（包括用 `ffill().bfill()` 補開頭）、全樣本統計量、結果取決於後面還有幾列 | 對每個截止列 t：只給到 t 的資料重算，t（含）以前的結果必須與用全部資料算出的相同 | `check_truncation_invariance`、`test_a_`、`test_ab_` |
| (b) 未來擾動不變性 | 結果取決於 t 之後的值 | 把 t 之後的值大幅改動，放大與變號各一次；t（含）以前的結果必須不變 | `check_future_perturbation_invariance`、`test_b_`、`test_ab_` |
| (c) as-of 合併 | 以數字的所屬期間合併、方向寫成 forward 或 nearest、公告當天就用上 | 合併後留著可得日欄位，斷言每一列的可得日都早於該列日期（或依時點定義改成不晚於）；再加手推的逐日預期值 | `check_join_respects_availability`、`test_c_` |
| (d) 標籤對齊 | 位移方向相反、多移或少移一列、跨股票位移、尾端 H 列被補值 | 改動第 j 列的價格，同一檔股票裡只有第 j-H 列與第 j 列的標籤可以改變（只適用兩個時點的報酬，其他標籤見下方補充）；每檔最後 H 列必須是 NaN；再加手算值 | `check_label_alignment`、`test_d_` |
| (e) 依時間切分並留間隔 | 不依時間順序的切分、訓練窗緊貼測試窗 | 每一折：訓練列全部早於測試列，而且兩者之間至少隔 H 列 | `check_split_respects_horizon`、`test_e_` |
| (f) 前處理只用訓練窗擬合 | 補值或標準化的統計量用到測試窗 | 擾動訓練窗之後的值，擬合出的統計量必須不變；再與只用訓練列手算的值比對 | `check_fit_uses_training_rows_only`、`test_f_` |
| (g) 視窗以交易列計數 | 規格是 N 個交易列，卻用日曆天數計算 | 用含週末與休市日的行事曆，比對手算的逐列預期值 | `check_three_row_mean_matches_hand_values`、`test_g_` |
| (h) 海外前一交易日 | 對到同一天的海外交易日、對到海外休市日、本地連休後沿用舊的對應、查不到就給空值 | 兩邊的行事曆都由測試資料提供；斷言對到的是真的海外交易日、日期早於本地交易日、中間沒有漏掉更近的一場，而且只有真的沒有更早的一場時才是 NaT；再加手推的對照表 | `check_previous_session_mapping`、`test_h_` |

## 各樣式的補充

### (a) 截斷與 (b) 擾動要一起用

- (b) 只改值、不改列數，抓不到「結果取決於後面還有幾列」的洩漏，例如以最後一列為基準的權重；(a) 抓得到。見 `test_ab_row_count_leak_is_seen_by_truncation_but_not_by_perturbation`。
- (b) 的擾動要往兩個方向各做一次：只把未來的值放大時，中位數可能完全不動。見 `test_f_fit_check_detects_full_sample_median`（只放大時抓不到，變號那次才抓到）與 `test_f_one_sided_shake_would_miss_a_leaky_median`（手算）。
- 兩種作法的數值剛好相同時，只比對數值看不出洩漏：範例的缺值用往前補與往回補都得到 13，擾動之後才分得出來。見 `test_b_perturbation_check_detects_backward_fill`。
- 測試資料要涵蓋序列一開頭就缺值的情況：`ffill().bfill()` 會拿後面的值補開頭，資料開頭沒有缺值時，兩種檢查都看不到這個洩漏。見 `test_ab_checks_detect_backfilled_start_with_leading_gap` 與 `test_ab_backfilled_start_is_invisible_without_a_leading_gap`。
- 兩種檢查都依輸入的日期對齊輸出，所以會丟掉列的函式（例如最後接 `dropna()`）也能檢查。輸出的索引不是輸入的日期、輸出全部是 NaN，或沒有輸入時，檢查直接報錯，不會空轉通過。見 `test_ab_checks_align_outputs_by_date_when_rows_are_dropped` 與 `test_ab_checks_refuse_outputs_that_leave_nothing_to_compare`。
- 擾動與放大前，整數欄（例如股數）會先轉成浮點數，否則 pandas 2.3.3 會發出型別的 `FutureWarning`（實測）。見 `test_bd_checks_accept_integer_columns_without_dtype_warnings`。
- 兩種檢查說的「t 之後」都不含第 t 列本身。第 t 列的資料在使用時點能不能用，要回到「怎麼用」第 1 步的定義，並靠手算值把關，例如範例中 3/6 的預測值必須是 11.5。本流程以未收錄的暫用測試確認過：用到同一列的預測，兩種不變性檢查都會通過。
- (a) 需要受測函式能接受較短的資料；不能截斷時（例如函式要求固定長度）只能用 (b)，並在回覆中說明沒有做 (a)。
- 輸入有多欄時，(b) 可以一次只擾動一欄，用來縮小洩漏來源；本流程以未收錄的暫用測試實測過，範例檔沒有這個例子。
- 同樣的檢查可以套在預測值上：把「用 t 之前的資料訓練，並對 t 預測」整段當成受測函式。範例用最簡單的模型示範（以過去各列的平均當預測，對照用全部資料算平均的做法），見 `test_a_truncation_check_detects_prediction_fitted_on_all_rows`；套在 scikit-learn 估計器上的情況，本流程沒有實測。

### (c) as-of 合併

pandas `merge_asof`（實測）：

- 預設 `direction="backward"`、`allow_exact_matches=True`：取鍵值小於或等於左表鍵值的最後一筆，所以公告日當天就會併入。公告若在當天的使用時點之後，要設 `allow_exact_matches=False`。哪一種才對，由「怎麼用」第 1 步的定義決定。
- `direction="forward"` 取之後的第一筆，`direction="nearest"` 取最接近的一筆；兩者都可能取到尚未公告的數字。
- 左右兩表都要先依鍵排序，否則丟出 `ValueError`，訊息是 `left keys must be sorted` 或 `right keys must be sorted`。
- 多檔股票要加 `by=` 逐檔比對；不加時會取到別檔股票的數字。用 `by=` 時，兩表仍要依時間鍵整體排序：先依股票、再依日期排序的面板會丟出 `left keys must be sorted`。範例只有單一序列，沒有示範 `by=`。

檢查靠的是「可得日」欄位，所以合併時要把它留在結果裡。來源資料沒有可得時間時，不可以拿所屬期間代替；回報這個缺口並問使用者。

### (d) 標籤對齊

- 未來 H 列的報酬用 `shift(-H)`。寫成 `shift(H)` 得到的是過去 H 列的報酬，在第 t 列當下就已經知道，不是要預測的對象。
- 多檔股票必須逐檔位移（`groupby(...).shift(...)`）。整欄一起位移時，一檔股票尾端的列會拿到下一檔股票的價格。
- 每檔股票最後 H 列沒有未來價格，標籤必須是 NaN，不可以補 0 或往前補。
- 「改一列、看哪些列跟著變」的檢查不需要手算值，適合資料較大的情況；小資料上仍要加手算值（`test_d_forward_return_matches_hand_values`）。
- 範例的規則（只有第 j-H 列與第 j 列可以變）只適用兩個時點的報酬，也就是第 t+H 列對第 t 列。看整段路徑的標籤（例如未來 H 列內的最高價）在改動第 j 列時，第 j-H 到第 j 列都可能改變、也可能不變；同日橫斷面排名的標籤還會牽動同一天的其他股票。這兩種標籤直接套用範例的檢查會誤報（實測）。本流程以未收錄的暫用腳本實測：把允許的範圍改成第 j-H 到第 j 列，並改成只檢查「改變的列沒有超出範圍」後，看整段路徑的正確標籤會通過，方向反了、多移一列、跨股票位移與尾端補值仍然抓得到；但完全沒用到未來價格的標籤也會通過，所以一定要配手算值。範例沒有示範這兩種標籤。

### (e) 切分與間隔

- 第 t 列的標籤用到第 t+H 列的價格。訓練窗最後一列是 a、測試窗第一列是 s 時，範例的檢查要求 `s - a - 1 >= H`，也就是中間至少隔 H 列。只隔 H-1 列時，訓練窗最後一列的標籤剛好用到第 s 列的價格；範例把這種情況判為不通過（`test_e_split_check_detects_missing_or_short_gap`）。訓練窗或測試窗是空的時，檢查也直接報錯（`test_e_split_check_detects_empty_fold`）。
- 間隔、視窗與期限都以交易列計數，不用日曆天數，理由見 (g)。
- 面板資料（多檔股票疊在一起）要先換算成交易日的位置再檢查；堆疊後的列數不等於交易日數。範例是單一時間軸，沒有示範面板。
- scikit-learn 1.9.1（實測）：對 400 列資料，`TimeSeriesSplit(n_splits=3, test_size=40, gap=63)` 切出的三折與範例的 `walk_forward_splits` 相同，訓練窗最後一列與測試窗第一列之間正好隔 63 列；`gap` 的預設值是 0。`train_test_split` 預設 `shuffle=True`，是先打散再切，不是依時間順序的切分；設 `shuffle=False` 時測試列才是最後一段。`KFold` 預設不打散，但中間的折會讓訓練列同時落在測試列之前與之後。

### (f) 前處理

- 這裡的統計量包括：補值用的中位數或平均、標準化用的平均與標準差。分位數切點、類別編碼對照表等其他由資料算出的參數同理，但範例沒有示範。
- scikit-learn 1.9.1（實測，資料與範例相同，`StandardScaler` 擬合在中位數補值後的資料上，例如 `make_pipeline(SimpleImputer(strategy="median"), StandardScaler())`）：只用訓練列擬合時，`SimpleImputer` 的 `statistics_` 是 2.0，`StandardScaler` 的 `mean_` 是 2.0、`scale_` 是 0.7071…（`ddof=0` 的標準差），與手算相同；用全部列擬合時，`statistics_` 變成 3.0、`mean_` 變成 6.5。`StandardScaler` 直接擬合含 NaN 的原始列時會略過 NaN，數字不同：訓練列的 `scale_` 是 0.8165…，全部列的 `mean_` 是 7.2。測試可以直接比對這些屬性。
- 中位數對單一方向的擾動不敏感，所以除了擾動檢查，一定要再比對手算值。
- 訓練窗全是缺值時，正確的擬合得到 NaN；檢查把兩邊都是 NaN 視為相同（`pytest.approx` 的 `nan_ok=True`），見 `test_f_fit_check_passes_when_training_window_is_all_nan`。對全是缺值的資料取中位數時，numpy 會發出 `RuntimeWarning: Mean of empty slice`（實測），範例只在這個測試上明確忽略這一種警告。

### (g) 交易列與日曆天

- pandas（實測）：`rolling(3)` 數的是列，前兩列是 NaN。`rolling("3D")` 數的是日曆天；週一的視窗裡只有它自己一列，照樣算出數字而不是 NaN，所以這種錯不會自己浮現。
- 測試資料的行事曆要含週末與至少一段休市日，手算值要涵蓋休市日前後的那幾列。

### (h) 海外前一交易日

- 規則本身（哪一個海外交易日的資料，在本地第 D 日的使用時點已經可得）取決於兩地的交易時間與使用時點，要先向使用者確認，或從既有程式讀出來。範例採用「日期早於 D 的最後一個海外交易日」，只是其中一種規則。
- 兩邊的行事曆都由測試資料提供（範例是寫在測試檔裡的清單），不讀正式行事曆、不連網。
- 沒有更早的海外交易日時要得到 NaT。位置算出 -1 又直接拿去取值，會取到最後一個交易日。見 `test_h_no_earlier_session_gives_nat`。檢查只在確實沒有更早的海外交易日時接受 NaT（`test_h_mapping_check_passes_on_nat_when_no_earlier_session`）；「前一個平日不是海外交易日就給 NaT」的寫法會被判為漏掉一場（`test_h_mapping_check_detects_bad_mappings` 的 `exact_lookup`）。
- 本地連休期間海外可能有好幾個交易日。特徵只用最後一個，還是累計整段，屬於特徵定義，由使用者決定。

## 這些測試不能證明什麼

通過只表示：在測到的函式與輸入上，沒有出現該樣式要抓的那一種洩漏。它不證明資料來源記載的可得時間是對的，不證明模型有效，也不證明任何策略能獲利；回覆時不可以把測試通過寫成這些結論。

## 執行範例

在本 skill 的資料夾內執行；`python` 換成裝有 pandas、numpy 與 pytest 的直譯器（優先用專案自己的）：

`python -B -m pytest -q -p no:cacheprovider examples/test_pit_patterns.py`

範例不連網，也不讀寫專案資料，也不另開 Python 子行程；帶 `-B` 與 `-p no:cacheprovider` 時不會留下 `__pycache__` 與 `.pytest_cache`（實測）。本流程在 Linux 上的執行結果記在 NOTICE.md。
