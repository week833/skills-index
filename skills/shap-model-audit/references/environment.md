# 執行環境：另建一個 SHAP 環境

week833/stock 在 a74eb97 版的兩份 requirements 檔都沒有列 shap；專案環境實際裝了什麼，用下面步驟 1 的唯讀指令確認。專案的虛擬環境與其他專案的 Python 環境一律不動，規定見專案的 AGENTS.md。需要 SHAP 時，經使用者同意後，另建一個放在 repository 外面的新環境。permutation importance 交叉檢查只用 numpy、pandas 與 scikit-learn，不需要這個環境。

## 步驟

以下指令都寫成 PowerShell 的單行指令，但沒有在 Windows 上執行過，能否照原樣執行未能確認。`<專案直譯器>`、`<環境資料夾>` 換成實際路徑；不需要啟用（activate）環境，一律用完整路徑呼叫該環境的 `python.exe`。路徑含空白時，整段路徑加引號，並在前面加 PowerShell 的呼叫運算子 `&`，例如 `& "D:\my envs\shap-audit\Scripts\python.exe" -B ...`（本流程沒有 PowerShell 可以實測）。

1. 唯讀讀出專案的版本，並確認專案環境有沒有 shap（例：`D:\stock\.venv\Scripts\python.exe` 是專案直譯器的例子）：
   `<專案直譯器> --version`
   `<專案直譯器> -B -c "import importlib.metadata as m; print({p: m.version(p) for p in ('numpy', 'pandas', 'scikit-learn', 'scipy', 'joblib')})"`
   `<專案直譯器> -B -c "import importlib.util as u; print(u.find_spec('shap') is not None)"`（只查找，不 import）
   印出 `True` 時，先問使用者要不要直接用專案直譯器執行稽核（加 `-B`，不安裝、不升級任何套件）。使用者同意就略過步驟 2 到 7，步驟 8、9 改用專案直譯器執行。
2. 問使用者，同意後才繼續。說明：環境資料夾的位置（放在 repository 外，例：`D:\venvs\shap-audit`，只是例子）、步驟 6 的完整安裝指令（版本用步驟 1 讀到的值），以及安裝會連到 PyPI 下載。不同意就停在這裡，只做不需要 shap 的部分（見 [shap-recipes.md](shap-recipes.md) 第 6 節）。之後要加裝套件或改版本時再問一次。
3. 確認要用來建環境的直譯器：`python --version`。版本必須符合 shap 的 `Requires-Python`（0.54.1 是 `>=3.12`），而且最好與專案相同。不符合就停下來問使用者要用哪一個直譯器；不要自行安裝 Python。
4. 確認環境資料夾還不存在：`Test-Path <環境資料夾>` 回傳 `True` 就停下來問使用者，不要沿用。對已經存在的環境資料夾再執行 `python -m venv` 不會報錯，而且會改寫它的 `pyvenv.cfg`（本流程在 Linux 以 CPython 3.12.3 實測）。
5. 建立環境：`python -m venv <環境資料夾>`
6. 安裝，版本換成步驟 1 讀到的值（下例是本流程驗證過的組合）：
   `<環境資料夾>\Scripts\python.exe -m pip install numpy==2.5.1 pandas==2.3.3 scikit-learn==1.9.1 scipy==1.18.1 joblib==1.6.0 shap==0.54.1 matplotlib==3.11.2 pytest==9.2.0`
   不要對專案直譯器執行 `pip`。專案的載入程式若還 import 其他套件，先問使用者，再以專案的版本加裝到這個環境。
7. 讀 shap 自己的套件中繼資料，確認需求：
   `<環境資料夾>\Scripts\python.exe -c "import importlib.metadata as m; md = m.metadata('shap'); print(md['Version'], md['Requires-Python'], [r for r in md.get_all('Requires-Dist') if 'extra' not in r])"`
8. 在本 skill 資料夾內跑範例測試；預期統計行是 `37 passed`：
   `<環境資料夾>\Scripts\python.exe -B -m pytest -q -p no:cacheprovider examples\test_shap_time_ordered_example.py`
   skill 資料夾若位在某個 repository 裡，先把 `examples` 的兩個檔複製到 repository 外的工作資料夾再跑：上層有 pytest 設定檔時，上層的 `conftest.py` 會被載入（本流程以 pytest 9.2.0 實測）。
9. 範例程式（使用者要求執行時才跑）。`--output-dir` 用 repository 與 skill 資料夾以外的絕對路徑；同名檔已存在時程式不覆寫，以退出碼 2 結束：
   `<環境資料夾>\Scripts\python.exe -B examples\shap_time_ordered_example.py --output-dir <輸出資料夾>`

## 載入模型與取得特徵

- 只用專案自己的程式取得模型與特徵（例：a74eb97 版的 pre-open 模型載入函式會先核對 sha256 與 scikit-learn 版本，不同就拒絕載入）。載入程式拒絕時停下來回報，不要繞過檢查。
- 不對來源不明的檔案執行 `pickle.load` 或 `joblib.load`：這類檔案在載入時會執行檔案作者指定的程式碼（本流程以自製的無害檔案實測，`pickle` 與 `joblib` 都會執行）。
- 稽核會呼叫的每個專案函式（載入模型、讀資料、算特徵，以及它們再呼叫的函式）都先讀過，確認只讀不寫：不抓資料、不重新訓練、不傳訊息；不寫快取、鎖檔、lease、receipt 或 manifest；不清除或刪除快取。有任何寫入或刪除就停下來問使用者：可以請使用者提供已算好的特徵檔，或由使用者明確同意並指定寫入的位置。例：a74eb97 版 pre-open 的資料讀取函式 `load_object` 會寫 parquet 快取與鎖檔，在中央資料（預設 `D:\TWStockData\shared_market_data`）的 `_query` 資料夾寫 lease 檔，並清除被取代的快取檔。
- 稽核用的腳本放在 repository 外（例如另一個工作資料夾），由新環境的直譯器加 `-B` 執行；需要時在腳本裡用 `sys.path.insert` 指向專案的程式資料夾。`-B` 讓被 import 的專案模組不在 repository 裡留下 `__pycache__`（本流程實測：不加 `-B` 會產生）。輸出只寫到使用者同意、位在 repository 外的資料夾。
- 特徵資料用專案已有的、預測當時可得的資料；不重抓資料。規則見 [time-series-rules.md](time-series-rules.md)。

## 前後比對 repository

SKILL.md 步驟 1 與 9 在 repository 根目錄執行下列指令，輸出記在回覆或工作筆記裡，不另存檔：

- `git --no-optional-locks status --porcelain --untracked-files=all --ignored=matching`
- 對上一行列出的未提交修改（例如 ` M`）與未追蹤檔案（`??`）：`git hash-object --no-filters -- <檔案>`（不列 `!!` 的被忽略路徑）

本流程以 git 2.43.0 在 Linux 的暫存 repository（套用使用者 a74eb97 版的 .gitignore）實測：

- 不加 `--ignored` 時，.gitignore 忽略的路徑（例如 `__pycache__/`、`outputs/`）完全不列出，寫進這些路徑的新檔前後比對看不出來；加上後以 `!!` 列出。
- `--untracked-files=all` 逐檔列出未追蹤的檔案；不加時，已經存在的未追蹤資料夾裡多出的新檔看不出來。`--ignored=matching` 讓被忽略的資料夾只列一行（例如 `!! .venv/`），不展開內容。
- 仍然看不到：步驟 1 時已存在的被忽略資料夾（例如既有的 `__pycache__/`）裡多出的檔案。這要靠 `-B` 與「只寫到 repository 外」預防。
- 步驟 1 已列為 ` M` 或 `??` 的檔案再被修改時，`git status` 前後的那一行相同；`git hash-object --no-filters` 的雜湊會不同。
- 加 `--no-optional-locks` 的 `git status` 不改寫 `.git/index`，不加時會改寫。`git diff` 即使加了這個選項，在檔案狀態資訊過期時仍會改寫 `.git/index`，所以這裡不用 `git diff`。
- 不在 repository 裡時，`git status` 以退出碼 128 結束。沒有 git 或不在 repository 裡時照實回報，不宣稱 repository 沒有改動。
- 比對結果寫成「前後比對沒有差異」或列出差異，並註明上面看不到的部分；不寫成「確認沒有任何改動」。

## 已驗證環境

| 項目 | 內容 |
|---|---|
| 日期 | 2026-11-13 |
| 平台 | Linux（Ubuntu 24.04.5 LTS，x86_64）；沒有在 Windows 上建立或執行 |
| 建立方式 | 本流程用 `uv venv --python 3.12` 與 `uv pip install`；上面的 `python -m venv` 與 `pip` 指令沒有實測 |
| 直譯器 | CPython 3.12.3 |
| 套件（`uv pip freeze` 全文） | cloudpickle 3.1.2、contourpy 1.4.0、cycler 0.12.1、fonttools 4.68.0、iniconfig 2.3.1、joblib 1.6.0、kiwisolver 1.5.1、matplotlib 3.11.2、narwhals 2.28.0、numpy 2.5.1、packaging 26.3、pandas 2.3.3、pillow 13.0.0、pluggy 1.7.0、pygments 2.21.0、pyparsing 3.3.3、pytest 9.2.0、python-dateutil 4.0.0、pytz 2026.6、scikit-learn 1.9.1、scipy 1.18.1、shap 0.54.1、slicer 0.0.8、threadpoolctl 3.8.0、tqdm 4.70.1、tzdata 2026.6 |
| 結果 | 範例測試 `37 passed`（加 `-W error` 也是 `37 passed`）；範例以預設參數執行，退出碼 0 |

numpy、pandas、scikit-learn、scipy 與使用者 `TWNextDayTop10\requirements.txt`（a74eb97）的版本相同。本流程只固定這四個：narwhals、python-dateutil、pytz、tzdata、threadpoolctl 的版本與該檔不同，該檔另列的 duckdb、six 沒有安裝。

## shap 0.54.1 的套件中繼資料（本流程讀出）

- `Requires-Python: >=3.12`。
- 不分 extra 的 `Requires-Dist`：`numpy>=2`、`scipy`、`scikit-learn`、`pandas`、`tqdm>=4.27.0`、`packaging>20.9`、`slicer==0.0.8`、`cloudpickle`。
- `Provides-Extra` 只有 `cuda`；沒有 `plots`，所以 matplotlib 要另外列出來安裝。
- 2026-11-13 查 PyPI：最新版是 0.54.1；檔案清單有 `shap-0.54.1-cp312-abi3-win_amd64.whl`（2026-10-16 上傳）。numpy 2.5.1、pandas 2.3.3、scikit-learn 1.9.1、scipy 1.18.1、matplotlib 3.11.2 都有 cp312 的 win_amd64 wheel；numpy 2.5.1 與 scipy 1.18.1 本身也要求 Python `>=3.12`。在 Windows 上安裝沒有實測。

## 實測到的函式庫行為（Linux，shap 0.54.1）

- `import shap` 會載入 `matplotlib.pyplot`。第一次載入時，matplotlib 會在 `MPLCONFIGDIR`（沒設定時是使用者的快取資料夾，Linux 上是 `~/.cache/matplotlib`）寫入字型快取 `fontlist-v3.11.0.json`。本流程每次執行都把 `MPLCONFIGDIR` 設成暫存資料夾，快取就寫在那裡；要把這個快取也限制在使用者同意的資料夾，就照同樣作法設定這個環境變數（PowerShell 的設定方式與 Windows 上的預設位置未能確認）。執行前告訴使用者這個檔會寫在哪裡。
- 背景資料超過 masker 的 `max_samples` 時，shap 以 logging 警告提示並抽樣成 `max_samples` 列。
- 執行較久的 explainer（例如 PermutationExplainer 跑 16 秒）會在 stderr 顯示 tqdm 進度列。
