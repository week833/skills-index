---
name: shap-model-audit
description: "Explain and audit which features an already-trained scikit-learn model (HistGradientBoosting, Ridge, LogisticRegression, pipelines with SimpleImputer and StandardScaler, or coefficient-only linear heads) relies on for time-ordered research data, using SHAP under point-in-time rules: out-of-sample periods, backgrounds from earlier windows, explicit output units, additivity checked against the model's own output, feature-group totals, and a permutation-importance cross-check. Describes model behaviour only, never causality or trading value. Use when the user asks what a trained model uses or whether it relies on a feature group at all. Not for training, tuning, ablation backtests or stock picking. 觸發語：模型用了哪些特徵、模型有沒有用到這組特徵、用 SHAP 解釋模型、特徵重要性稽核。"
---

# SHAP 模型稽核

## 目的

說明並稽核一個已訓練的 scikit-learn 模型，在時間序列研究資料上靠哪些特徵做預測，例如模型有沒有用到某組特徵。以 SHAP 描述模型行為、遵守時點規則，再以 permutation importance 交叉檢查。結果不是因果證據、不是交易訊號，也不證明模型有效。

## 何時使用、何時不用

- 使用：使用者想知道已訓練模型用了哪些特徵或特徵組、有沒有用到某組特徵、兩個模型使用特徵的方式有何不同。
- 「有沒有作用」在這裡指已訓練的模型有沒有用到。問加入或移除某組特徵能否改善樣本外表現時，要重新訓練或回測，不在本 skill 範圍，先向使用者確認。
- 不用：訓練、調參或重新訓練模型；選股、買賣建議、目標價、部位大小；證明模型有效或策略能獲利；影像、文字或深度學習模型。
- 只要求分析時唯讀：使用者明確要求執行時才跑程式。

## 最小工作流

1. 先讀專案的 AGENTS.md。在 repository 根目錄執行 `git --no-optional-locks status --porcelain --untracked-files=all --ignored=matching`，對其中列出的未提交修改與未追蹤檔案再執行 `git hash-object --no-filters -- <檔案>`，記下輸出（不另存檔）。使用者的未提交變更原樣保留。
2. 寫下稽核目標（[shap-recipes.md](references/shap-recipes.md) 第 1 節）：模型與版本、要解釋的輸出與單位、特徵分組。專案已有分組就沿用。
3. 決定期間（[time-series-rules.md](references/time-series-rules.md)）：從模型中繼資料讀出訓練期與資料截止日；解釋期在訓練期之後，標籤重疊時留間隔；背景只取第一個解釋日以前的列；固定種子，不打亂。
4. 環境（[environment.md](references/environment.md)）：專案環境不能改動。先唯讀讀出專案的版本並確認有沒有 shap，再問使用者；同意後在 repository 外另建新環境，固定與專案相同的 numpy、pandas、scikit-learn、scipy 版本，再跑範例測試確認。不同意就略過步驟 6 與 8，其餘照做（步驟 7 不需要 shap）。
5. 模型與特徵只用專案自己的程式取得。先讀過會呼叫的每個專案函式（載入模型、讀資料、算特徵）；會寫快取、鎖檔、lease、receipt 或 manifest，或會清除快取，就停下來問。不對來源不明的檔案 unpickle。稽核腳本放在 repository 外，用 `-B` 執行。
6. 算 SHAP：依 shap-recipes.md 第 2 節選 explainer；背景用 `shap.maskers.Independent(bg, max_samples=len(bg))`；三維結果用 `exp[..., k]` 選輸出。對模型自己的輸出檢查可加性（atol=1e-6、rtol=1e-5）；失敗就停下，照第 3 節換方法，不放寬容差。模型在解釋期的輸出不變（常數模型，或專案標為基準模型）時照實回報，不說成「這組特徵沒有作用」。算每個特徵與每組的平均絕對 SHAP。
7. 交叉檢查：在同一批樣本外列上跑 `sklearn.inspection.permutation_importance`（固定 `random_state`），以及整組打亂的版本。判斷規則事先寫下；兩種方法對某組有沒有作用的判斷不一致時，回報並調查，不選邊。
8. 圖表（使用者要才畫）：照 shap-recipes.md 第 8 節，存到使用者給的資料夾並檢查缺字。
9. 收尾：重跑步驟 1 的指令並對照。報告寫「前後比對沒有差異」或列出差異，並註明比對看不到的部分（environment.md 的「前後比對 repository」）；沒有 git 或不在 repository 裡時照實說明，不宣稱沒有改動。

[範例程式](examples/shap_time_ordered_example.py)以合成資料示範步驟 3、6、7（執行方式見 environment.md 步驟 9）。

## 回覆契約

用繁體中文，先給結果，再列出：

- 模型類別、訓練期、資料截止日、scikit-learn 版本；shap、numpy、pandas 與 Python 版本。
- 解釋的輸出與單位，例如 `predict` 的未來報酬、二元 `decision_function` 的 log-odds、`predict_proba[:, 1]` 的機率。
- explainer、masker、背景資料：期間起訖日、列數、實際用到的列數、抽樣方式與種子。
- 解釋期起訖日、列數與抽樣方式；標籤長度與間隔。
- 可加性：最大絕對誤差、容差、輸出標準差、是否通過。
- 平均絕對 SHAP 最高的特徵，以及各組的總和與其定義。
- permutation importance：保留期、`scoring`、`n_repeats`、`random_state`、各組結果、兩種方法是否一致；不一致時列出組別與調查方向。
- 保留期上模型與天真基準的分數，只作脈絡，不代表模型有效。
- 限制、實際執行的指令與輸出摘要（退出碼 0 或檔案存在本身不算完成）、repository 前後比對的結果；沒做的事與原因。
- 固定聲明：「本結果只描述模型在指定資料、期間與背景下的行為；不是因果證據、不是交易訊號，也不證明模型有效。」

## 界線

- 專案的 AGENTS.md 與使用者的直接指示優先於本 skill；有衝突就停下來問使用者。
- 不下單，不呼叫券商或交易 API，不給買進、賣出或持有建議、目標價或部位大小。
- 不改動專案或其他專案的 Python 環境。未經使用者明確授權，不安裝套件、不連網、不重抓資料、不重新訓練、不傳訊息、不啟動服務或排程。
- 不印出、不記錄環境變數、token 或含 token 的 URL。
- 檔案只寫到使用者指定、位在 repository 外的資料夾；不搬移、改名或刪除既有檔案，不建立備份或日期化副本；在 repository 裡寫檔、commit、push 或開 PR，都要使用者明確要求。
- 本 skill 只在 Linux 上以合成資料驗證，沒有在 Windows、Codex 或使用者的真實模型上執行過；範圍見 [NOTICE.md](NOTICE.md)。
