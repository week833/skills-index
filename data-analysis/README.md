# 🔬 資料分析與統計建模

[← 回總覽](../README.md)

### `shap-model-audit`

> **用途：稽核已訓練的模型實際用了哪些特徵與特徵組。** 以 SHAP 在樣本外期間解釋 scikit-learn 模型，遵守時點規則，對模型自己的輸出檢查可加性，算出每個特徵與每組特徵的平均絕對 SHAP，再用 permutation importance 交叉比對；例如回答「開盤前模型到底有沒有用到前一晚的美股特徵」。

- 支援的模型：`HistGradientBoostingRegressor`、`HistGradientBoostingClassifier`、`Ridge`、`LogisticRegression`，以及含 `SimpleImputer` 與 `StandardScaler` 的 pipeline；每種的 explainer 寫法、解釋的輸出與單位都實測過
- 時點規則：只解釋訓練期之後的期間；背景資料只取第一個解釋日以前的列；標籤重疊時留間隔；固定種子、不打亂
- 可加性：容差固定為 atol=1e-6、rtol=1e-5，失敗就換方法，不放寬容差、不關掉檢查。實測發現以 float64 資料訓練的 `HistGradientBoosting*` 用 interventional TreeExplainer 時可加性不成立，而且在這次的樣本外測試中，shap 自己的檢查（容差 1e-2）沒有示警；skill 寫明此時的替代作法
- 交叉檢查：permutation importance 只需要 scikit-learn，在專案現有環境就能跑；兩種方法對某組特徵有沒有作用的判斷不一致時，回報並調查，不選邊
- 結果的意義：只描述模型在指定資料、期間與背景下的行為；不是因果證據、不是交易訊號，也不證明模型有效。報告固定附上這句聲明
- ⚠️ 環境：shap 不在專案環境裡，專案環境不可改動。要先問使用者，同意後才在 repository 外另建環境，固定與專案相同的 numpy、pandas、scikit-learn、scipy 版本；不同意時只做 permutation importance
- ⚠️ 讀模型與特徵只用專案自己的程式；會寫快取、鎖檔或 receipt 的函式要先停下來問，不對來源不明的檔案 unpickle
- 範例：[examples/shap_time_ordered_example.py](../skills/shap-model-audit/examples/shap_time_ordered_example.py) 以合成的「日期 × 股票」資料示範，含一組刻意無效的「雜訊」特徵，兩種方法都判定接近零；只寫入指定的輸出資料夾、不連網
- 驗證狀態：在 Linux 的 Python 3.12.3 與 3.13.18、shap 0.54.1、numpy 2.5.1、pandas 2.3.3、scikit-learn 1.9.1、scipy 1.18.1 上，範例的 37 個測試全部通過；只用過合成資料，沒有在 Windows、Codex 或使用者的真實模型上執行過；Windows 上的中文字型顯示未測
- 來源：本儲存庫 [skills/shap-model-audit](../skills/shap-model-audit)（入口 `SKILL.md`；MIT 授權）
- 改寫自：[K-Dense-AI/scientific-agent-skills 的 shap](https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/shap)（原名 claude-scientific-skills；`2d2065f`；MIT）。拿掉要求把廠商論文加進使用者報告並連線 arxiv.org 的「Citing Scientific Agent Skills」段落、`allowed-tools` 預先核准、執行時自動安裝套件的 `uv run --with` 指令、固定資料集的示範腳本，以及影像、文字與深度學習內容；版本依據改為 shap 0.54.1，詳見 [NOTICE.md](../skills/shap-model-audit/NOTICE.md)
