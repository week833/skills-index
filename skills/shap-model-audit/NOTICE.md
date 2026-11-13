# NOTICE

## 這是什麼

`shap-model-audit` 是 week833 的 agent skill：用 SHAP 說明並稽核已訓練的 scikit-learn 模型在時間序列研究資料上用了哪些特徵，遵守時點規則，並以 permutation importance 交叉檢查；結果只描述模型行為。內容是一份 `SKILL.md`、給 Codex 介面用的 `agents/openai.yaml`、三份參考文件、一支範例程式與它的 pytest 測試；沒有 hook、MCP 伺服器、安裝程式、遙測、自動更新或網路呼叫。

整理日期：2026-11-13。

## 來源

| 項目 | 內容 |
|---|---|
| 上游儲存庫 | [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills)（舊名 claude-scientific-skills；本流程讀取的 clone，remote 是 `https://github.com/K-Dense-AI/claude-scientific-skills`） |
| 路徑 | `skills/shap/`（`SKILL.md`、`references/` 的八份文件、`scripts/tabular_report.py`） |
| Commit | `2d2065fb4520fa3f3f2bcf61cff26ec8b7eba4b5` |
| 授權 | MIT（repository 的 `LICENSE.md`；該 skill 的 frontmatter 也寫 `license: MIT`），全文見 [LICENSE.txt](LICENSE.txt) |
| 著作權人 | Copyright (c) 2025 K-Dense Inc. |

本 skill 是改寫版，與上游作者沒有隸屬或背書關係。

- 衍生自上游的部分：讓 SHAP 結果可信的作法，包括使用 `shap.Explanation` 與 `explainer(X)`、寫明解釋的輸出與單位、刻意選擇 explainer 與背景資料、對模型自己的輸出檢查可加性並給容差（沿用上游的 atol=1e-6、rtol=1e-5）、明確處理多輸出、誠實抽樣、背景資料預設只用 100 列的陷阱、SHAP 描述模型行為而非因果，以及「解釋要附上模型的預測表現」。這些內容改寫在 `SKILL.md`、`references/shap-recipes.md` 與 `references/time-series-rules.md`。
- 本版新增的部分：`references/environment.md`、`examples/` 的範例程式與測試、時間序列規則的大部分、permutation importance 交叉檢查、各模型的實測對照、圖表的中文字型設定，以及下列差異中標為新增的內容。

## 與上游的差異

1. 移除「Citing Scientific Agent Skills」整節：它要求在使用者的報告加入廠商論文，並連到 arxiv.org 取資料。
2. 移除 frontmatter 的 `allowed-tools`，以及 `license`、`compatibility`、`metadata` 欄位；frontmatter 只留 `name` 與 `description`。
3. 移除 `uv run --with` 這類執行時才安裝套件的指令，以及 `source`、`/tmp` 等 POSIX 專用寫法。改為：先唯讀讀出專案的版本，徵得使用者同意後，再以 PowerShell 單行指令在 repository 外另建新環境，不碰專案環境。
4. 移除固定以乳癌資料示範的 `scripts/tabular_report.py`（本流程只讀過，沒有執行）。改為以合成時間序列資料示範的範例程式與 pytest 測試（新增）；範例只接受絕對路徑的輸出資料夾，不覆寫既有的輸出檔。
5. 移除使用者用不到的內容：影像、文字、深度學習與序列資料（`modalities.md` 全部，以及其他檔案的相關段落）；XGBoost、LightGBM、CatBoost；cohort、錯誤與損失歸因、公平性、模型比較、特徵工程、生產環境服務與監控等工作流程；Partition masker 與 PartitionExplainer、Impute masker（本版改為事後把同組的 SHAP 值逐列相加）；bar 以外的大多數圖（beeswarm 只提到回傳型別，waterfall、scatter、heatmap、violin、force、decision 沒有收錄）；`SKILL.md` 結尾的 Primary Sources 連結清單。`migration.md`（舊版 API 遷移）與 `theory.md`（理論）大多沒有沿用；KernelExplainer、DeepExplainer、GradientExplainer、交互作用值與 link 函式的段落沒有收錄。穩定度只保留「換背景期間或種子再算一次」。
6. 版本：上游以 SHAP 0.52.0 為準，並列出舊版 Python 可改用的版本。本版改以 2026-11-13 PyPI 上最新的 0.54.1 實測，引用它自己的套件中繼資料，不沿用上游的版本敘述。上游的 `shap[plots]` 在 0.54.1 沒有對應的 extra，所以改為另外安裝 matplotlib。
7. 模型範圍改為使用者程式實際 import 的 HistGradientBoostingRegressor、HistGradientBoostingClassifier、Ridge、LogisticRegression，以及含 SimpleImputer、StandardScaler 的 Pipeline；另加只存係數、由專案函式重播的線性模型（使用者的部分模型以係數 dict 或 JSON 保存）。每一種的 explainer 呼叫、輸出空間與可加性都在本流程實測，並由範例測試重跑（新增）。
8. 新增實測發現：以 float64 訓練的 HistGradientBoosting 在 interventional TreeExplainer 下，解釋訓練期之後的列時可加性誤差是 3.6e-4 到 7.3e-3，shap 自己的檢查沒有報錯（它的內部容差是 atol=1e-2、rtol=1e-2），解釋訓練用的列時 shap 會丟出 `ExplainerError`；不給背景的 tree_path_dependent 不受影響。另列替代作法與 PermutationExplainer 評估次數的實測精度。
9. 新增時間序列規則：解釋樣本外期間、依時間切分、背景只取第一個解釋日以前的列、只用預測當時可得的特徵、標籤重疊時留間隔、不打亂也不用 K-fold、報告用了哪些期間；相關特徵分組並報告組總和；同一天共用的特徵在打亂時的問題。上游只有一小段時間序列說明。
10. 新增 permutation importance 交叉檢查（含整組一起打亂），以及兩種方法不一致時的處理：回報並調查，不選邊。
11. 新增圖表的繁體中文字型清單、Agg 後端、存到呼叫端給的資料夾、不覆寫既有檔，以及缺字檢查。
12. 新增回覆契約與界線：AGENTS.md 與使用者的直接指示優先、有衝突就停下來問；不下單、不給買賣建議；不改動環境；不印出秘密；不在 repository 裡寫檔。上游「解釋要附上預測表現」改寫為：附上保留期上模型與天真基準的分數，只作脈絡，不代表模型有效。
13. 新增安全檢查：呼叫專案函式前先確認它不寫快取、鎖檔、lease、receipt 或 manifest，也不清除快取；工作開始與結束時以 `git status --ignored` 與 `git hash-object` 比對 repository，並寫明比對看不到的部分；模型輸出是常數時照實回報，範例程式則以退出碼 1 停下。
14. 全文改為繁體中文。

## 已驗證

以下都是本流程於 2026-11-13 在 Linux（Ubuntu 24.04.5 LTS，x86_64）上實際執行的結果。暫時環境以 uv 0.11.32 的 `uv venv --python 3.12` 建立（CPython 3.12.3），以 `uv pip install "numpy==2.5.1" "pandas==2.3.3" "scikit-learn==1.9.1" "scipy==1.18.1" shap matplotlib pytest` 安裝。`uv pip freeze` 全文：cloudpickle 3.1.2、contourpy 1.4.0、cycler 0.12.1、fonttools 4.68.0、iniconfig 2.3.1、joblib 1.6.0、kiwisolver 1.5.1、matplotlib 3.11.2、narwhals 2.28.0、numpy 2.5.1、packaging 26.3、pandas 2.3.3、pillow 13.0.0、pluggy 1.7.0、pygments 2.21.0、pyparsing 3.3.3、pytest 9.2.0、python-dateutil 4.0.0、pytz 2026.6、scikit-learn 1.9.1、scipy 1.18.1、shap 0.54.1、slicer 0.0.8、threadpoolctl 3.8.0、tqdm 4.70.1、tzdata 2026.6（同 [environment.md](references/environment.md) 的「已驗證環境」）。起草、兩次審查與最後的修正各自新建過這樣的環境，freeze 結果都相同。執行時設定 `PYTHONDONTWRITEBYTECODE=1`，`MPLCONFIGDIR` 指向暫存資料夾。下文的 `python` 指這個暫時環境的直譯器；第 1 到 3 項是修正後的最終版本重跑的結果。

1. 範例測試，在本 skill 資料夾內執行 `python -B -m pytest -q -p no:cacheprovider examples/test_shap_time_ordered_example.py`（另加 `--basetemp` 指向暫存資料夾）：`37 passed`；加 `-W error` 也是 `37 passed`。同樣的版本裝在 CPython 3.13.18 的環境：`37 passed`。把兩個 `.py` 檔改成 BOM 加 CRLF 換行（模擬 Windows 上的副本）再跑：`37 passed`。測試中有一次是在禁止 socket 連線、工作目錄設在暫存資料夾的情況下跑完整個範例。執行後資料夾內沒有 `__pycache__`、`.pytest_cache` 或 `.pyc`。另以 6 個故意改壞的範例版本確認測試會失敗：寫檔到工作目錄、同組特徵用不同列順序打亂、組總和改成各特徵平均絕對值相加、覆寫既有輸出檔、拿掉常數模型檢查、允許放寬容差，每個版本都有 1 個測試失敗。
2. 範例程式，`python -B examples/shap_time_ordered_example.py --output-dir <暫存資料夾>`：退出碼 0；只產生 `importance.csv` 與 `audit_metadata.json`；可加性最大絕對誤差，HistGradientBoostingRegressor 8.73e-11、Pipeline 1.04e-17（容差 atol=1e-6、rtol=1e-5）；兩種方法對四組的判斷一致，「雜訊」組兩種方法都判為接近零；保留期 MSE 分別是 6.61e-5 與 6.80e-5，天真基準 1.30e-4（只作脈絡）。以 strace 追蹤同一個指令：寫入的只有這兩個輸出檔、`MPLCONFIGDIR` 裡的 matplotlib 字型快取與它的鎖檔，以及 `/dev/shm` 裡函式庫建立的暫時號誌；沒有任何 `connect` 呼叫。在 `LC_ALL=C` 與 `-X utf8=0`（stdout 編碼為 ascii）下執行：退出碼 0，中文摘要正常輸出，兩個輸出檔與上一次逐位元組相同。錯誤情況都不寫任何輸出檔：可加性不通過（`--atol 1e-30 --rtol 1e-30`）與常數模型（`--n-dates 5` 或 `--n-dates 8 --n-stocks 5`）退出碼 1；輸出檔已存在、輸出路徑是檔案、空白或相對路徑、交易日數不足、種子超出範圍、`--n-dates abc`、放寬容差，退出碼 2，訊息為繁體中文。程式碼沒有讀檔的呼叫（逐行讀過確認）。
3. 範例結論的穩定度：種子 1、2、3、7、11 各跑預設參數、較少資料（160 日 × 12 檔）與 5 日標籤三種設定。預設參數全部一致，「雜訊」組的 SHAP 占比 0.7% 到 3.7%；另兩種設定在部分種子出現不一致。
4. 參考文件中標「實測」的事實，都以草稿腳本確認：各模型的 explainer 呼叫、輸出形狀與可加性（含 HistGradientBoostingClassifier 二元的 raw 與 probability、多類的 raw 與 probability 丟出的 `NotImplementedError`，LogisticRegression 二元與多類，多類 `decision_function` 是 softmax 前的分數而不是各類的 log-odds）；只存係數的線性模型以 `LinearExplainer((coef, intercept), ...)` 解釋，以及回傳 tuple 的函式交給 PermutationExplainer 會出錯；float64 與 float32 訓練的 HistGradientBoosting 可加性比較（解釋訓練期之後的列與訓練用的列，以及 tree_path_dependent），以及 shap 原始碼裡 TreeExplainer 的內部容差；與 ExactExplainer、逐一列舉 Shapley 值的對照；PermutationExplainer 不同 `max_evals` 的精度；`shap.Explainer` 的自動選擇；背景列數上限與屬性名；`exp[k]` 與 `exp[..., k]`；Pipeline 兩種空間的結果一致；組合模型的可加；整組打亂的 permutation importance 與 scikit-learn 直接呼叫的結果相同（迴歸與二元分類）；`SimpleImputer` 的 `keep_empty_features`；傳給函式的資料型別；`loss` 為 poisson、gamma 時 raw 是 log 尺度；`train_test_split` 與 `KFold` 的 `shuffle` 預設、不打亂的 `KFold` 仍用較晚的資料訓練、`TimeSeriesSplit` 的 `gap` 以樣本數計；常數模型的 SHAP 值全為 0；HistGradientBoosting 的 `early_stopping` 說明與內部驗證集切法；`import shap` 會載入 matplotlib 並寫入字型快取；tqdm 進度列輸出到 stderr；中文字型清單與缺字警告；`-B` 不寫 `__pycache__`；上層有 pytest 設定檔時會載入上層的 `conftest.py`；以自製的無害檔案確認 `pickle` 與 `joblib` 載入時會執行檔案指定的程式碼；對既有環境資料夾再執行 `python -m venv`（CPython 3.12.3）退出碼 0 並改寫 `pyvenv.cfg`；`environment.md` 的三個 `-c` 單行指令的 Python 內容。
5. `references/shap-recipes.md` 的兩個 Python 程式區塊：抽出後執行，`additivity_error` 對正確的輸出回傳通過、對差 1e-3 的輸出回傳不通過、對三維輸入丟出 `ValueError`；`save_bar` 存出圖檔並回傳 0（看過這張圖，中文正常），只留 DejaVu Sans 時回傳 82，同名檔已存在時丟出 `FileExistsError`。範例的 `grouped_permutation_importance` 與 `_RowPositionView` 單獨抽出、不 import shap 也能執行，結果與 scikit-learn 直接呼叫相同。
6. git（2.43.0，Linux 的暫存 repository，套用使用者 a74eb97 版的 .gitignore）：`environment.md`「前後比對 repository」列出的每一項行為，包括各種 `git status` 選項看得到與看不到的變化、`git hash-object --no-filters` 對再次修改的檔案給出不同雜湊、加 `--no-optional-locks` 的 `git status` 不改寫 `.git/index` 而 `git diff` 會改寫，以及不在 repository 裡時的退出碼 128。
7. 套件資訊：shap 0.54.1 的 `Requires-Python`、`Requires-Dist`、`Provides-Extra` 由已安裝套件的中繼資料讀出；2026-11-13 查 PyPI 的 JSON API，確認 shap 的最新版與檔案清單，以及 numpy、pandas、scikit-learn、scipy、matplotlib 指定版本的 cp312 win_amd64 wheel。
8. 使用者專案 week833/stock（a74eb97，唯讀 clone）只讀不執行：兩份 requirements 檔沒有 shap；`TWNextDayTop10/requirements.txt` 的版本；pre-open 模型載入函式先核對 sha256 與 scikit-learn 版本；`GROUPS` 對照表與 `GLOBAL_PRE` 組；pre-open 的市場部分依日期取 `.first()`；資料讀取函式 `load_object` 寫快取、鎖檔與 lease 並清除舊快取；每日線性模型以係數 dict 保存、重播函式回傳 tuple、有常數基準模型；單股研究模型以 JSON 匯出；AGENTS.md 全文。
9. 上游資訊：commit 由 clone 的 refs 讀出；`SKILL.md`、`references/` 八份文件、`scripts/tabular_report.py` 與 `LICENSE.md` 全文讀過，沒有執行任何上游檔案。
10. 結構檢查：以系統的 CPython 3.11.18 用隔離模式（`-I`）執行本流程的 `validate_skill.py`，對本資料夾輸出 `PASS`。

## 未驗證

- 沒有在 Windows 上執行。PowerShell 指令（`python -m venv`、`pip install`、`Test-Path`、呼叫運算子 `&`、`-c` 單行指令的引號、`Scripts\python.exe` 路徑）、繁體中文 Windows（cp950）主控台的輸出、Microsoft JhengHei 的實際顯示、matplotlib 字型快取在 Windows 上的位置與 `MPLCONFIGDIR` 的設定方式，都沒有確認。本流程的機器上沒有 PowerShell。
- 沒有在 Codex 內執行：skill 能否被載入、會不會自動觸發、`SKILL.md` 會不會被截斷，都沒有確認。也沒有在 Claude Code 內以 skill 的形式載入。
- 沒有用使用者的真實模型或資料執行；專案的載入程式能否在另建的環境中 import 並載入模型（例如是否需要其他套件），沒有確認。使用者專案環境的 Python 版本與實際安裝的套件未能確認。
- `SKILL.md` 步驟 1 與 9 的 git 指令只在 Linux 的暫存 repository 演練，沒有在使用者的 repository 或 Windows 的 git 上執行。
- 以 pip 而非 uv 解析與安裝沒有實測；Windows wheel 只確認在 PyPI 上存在。
- 分類模型只實測到「已驗證」第 4 項列出的範圍，而且都是合成資料；範例程式本身只含迴歸模型。
- 以日期為單位打亂同一天共用的特徵，只寫成規則，沒有提供或測試程式。TreeExplainer 能否讀專案匯出成 JSON 的樹，沒有測試。
- float64 訓練的 HistGradientBoosting 可加性誤差的原因未能確認；只在 shap 0.54.1、scikit-learn 1.9.1 下觀察到。
- shap、scikit-learn、numpy、pandas 的其他版本沒有測；Python 只測了 3.12.3 與 3.13.18。
- 「接近零」的判斷規則（SHAP 占比低於 5%；permutation 平均值減兩倍標準差不大於 0）是本版自訂的篩選規則，只在合成資料上檢查過，不是統計檢定。
