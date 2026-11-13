# SHAP 作法（本流程實測過的部分）

本頁的事實都以 shap 0.54.1、scikit-learn 1.9.1、numpy 2.5.1、pandas 2.3.3、CPython 3.12.3 在 Linux 上用合成資料實測。第 2 節表格的各列，以及第 3 節 float64 段落的三個結論（超出容差而 shap 沒有報錯、訓練用的列丟出 `ExplainerError`、tree_path_dependent 通過），由[範例測試](../examples/test_shap_time_ordered_example.py)重跑；其餘標「實測」的事實與數字只在本流程的草稿腳本確認過。版本不同時先跑那份測試，其餘事實也要另外確認，不要直接沿用本頁的結論。

## 1. 先寫下要解釋什麼

計算之前先記下，報告也照抄：

- 模型類別、訓練期、訓練時的 scikit-learn 版本；
- 要解釋的輸出：哪個方法（`predict`、`decision_function`、`predict_proba[:, k]`）與單位（目標單位、log-odds、機率）。分類模型的 k 由 `model.classes_` 對出，寫明代表哪個類別；
- 要解釋的列與背景資料（期間、列數、抽樣方式與種子）；
- explainer 與 masker。

單位只看這份記錄與可加性對照，不看圖的顏色或正負號推測。

## 2. 各模型的作法

下表的 `masker` 一律是 `shap.maskers.Independent(bg, max_samples=len(bg))`，`bg` 是背景資料。「通過」指第 3 節的檢查在容差 atol=1e-6、rtol=1e-5 內成立。

| 模型 | 呼叫 | 解釋的輸出 | 可加性對照 | 實測 |
|---|---|---|---|---|
| HistGradientBoostingRegressor | `shap.TreeExplainer(model, data=masker, feature_perturbation="interventional")` | `predict`，目標單位 | `model.predict(X)` | float32 訓練的模型通過；float64 訓練的見第 3 節 |
| HistGradientBoostingClassifier，二元 | 同上，加 `model_output="raw"` | log-odds；二維，單一輸出 | `model.decision_function(X)` | 通過 |
| HistGradientBoostingClassifier，二元 | 同上，加 `model_output="probability"` | 正類機率；二維，單一輸出，不必再切 `[..., 1]` | `model.predict_proba(X)[:, 1]` | 通過 |
| HistGradientBoostingClassifier，多類 | 同上，加 `model_output="raw"` | 每類一個分數；三維（列、特徵、類別） | `model.decision_function(X)[:, k]` | 通過；`model_output="probability"` 丟出 `NotImplementedError` |
| Ridge | `shap.LinearExplainer(model, masker)` | `predict` | `model.predict(X)` | 通過；值等於 `model.coef_ * (X - bg.mean())` |
| LogisticRegression | `shap.LinearExplainer(model, masker)` | 二元：log-odds，不是機率。多類：每類一個 softmax 前的分數（不是各類的 log-odds），三維 | 二元 `model.decision_function(X)`；多類 `model.decision_function(X)[:, k]` | 通過 |
| 只存係數的線性模型（專案以自己的函式重播，例如係數 dict 或 JSON） | 先用專案存的中位數補缺值、減平均、除以標準差，得到標準化後的 `z`（背景為 `z_bg`）；`shap.LinearExplainer((coef, intercept), shap.maskers.Independent(z_bg, max_samples=len(z_bg)))(z)` | `z @ coef + intercept`：Ridge 是預測值，LogisticRegression 是 log-odds | 專案重播函式的同一個輸出 | 通過；與原始空間的 PermutationExplainer 相差在 1e-9 以內 |
| 任何模型的機率或其他自訂輸出 | `shap.PermutationExplainer(f, masker, seed=固定)`，呼叫時給 `max_evals` | `f` 的輸出 | `f(X)` | 通過；`max_evals` 小於 `2 * 特徵數 + 1` 會丟 `ValueError` |
| Pipeline（SimpleImputer、StandardScaler、Ridge 或 LogisticRegression），前處理後空間 | `pre = pipe[:-1]`；`shap.LinearExplainer(pipe[-1], shap.maskers.Independent(pre.transform(bg), max_samples=len(bg)))(pre.transform(X))` | 與最後一步相同 | `pipe.predict(X)` 或 `pipe.decision_function(X)` | 通過；`pre.get_feature_names_out()` 與原欄位相同 |
| 同一個 Pipeline，原始特徵空間 | `shap.PermutationExplainer(lambda a: pipe.predict(pd.DataFrame(a, columns=cols)), shap.maskers.Independent(bg, max_samples=len(bg)), seed=固定)` | `pipe.predict` | `pipe.predict(X)` | 通過，含缺值；float64 資料時與上一列的值相差在 1e-9 以內 |

補充（皆實測）：

- 插補與標準化逐欄進行，所以前處理後的每一欄仍對應一個原始特徵。`SimpleImputer` 預設會丟掉訓練時全是缺值的欄，`keep_empty_features=True` 才保留。用 `pre.get_feature_names_out()` 對好名稱再解釋。
- `shap.Explainer(model, bg)` 自動選擇：HistGradientBoosting 選 TreeExplainer，Ridge 與 LogisticRegression 選 LinearExplainer；但背景會被限成 100 列（第 4 節）。Pipeline 物件不能直接交給 `shap.Explainer`（`TypeError`：不可呼叫）。交給它一個函式（例如 `pipe.predict`）時，特徵數 10 以下選 ExactExplainer，11 以上選 PermutationExplainer。寧可像上表一樣明確指定 explainer。
- 不給背景資料的 `shap.TreeExplainer(model)` 走 `tree_path_dependent`，對 HistGradientBoosting 的可加性也通過，但它不使用你的背景資料，是另一種賽局（game）；用了就在報告寫明，不和 interventional 的結果直接比較。
- 傳給函式的資料型別跟著背景資料：背景是 DataFrame 時函式收到 DataFrame，是陣列時收到陣列。函式裡一律用 `pd.DataFrame(a, columns=cols)` 重建欄名，兩種情況都適用。
- HistGradientBoostingRegressor 的 `loss` 是 `poisson` 或 `gamma` 時，TreeExplainer 解釋的是 log 尺度的 raw 輸出，加總等於 `log(model.predict(X))`；`squared_error`、`absolute_error`、`quantile` 時加總等於 `model.predict(X)`。
- 專案的重播函式一次回傳多個輸出（tuple）時，包成只回傳一個輸出的函式，例如 `lambda a: replay(head, a)[k]`；直接交給 PermutationExplainer 會出錯（`AssertionError`）。
- 樹模型只存成 JSON、由專案的函式重播時：本流程沒有驗證 TreeExplainer 能否讀專案匯出的樹，改用 PermutationExplainer 包專案的重播函式，先用少量列計時。為了取得 scikit-learn 物件而重新訓練，要使用者明確授權；沒有授權就停下來問。

## 3. 可加性檢查

```python
import numpy as np


def additivity_error(explanation, expected, atol=1e-6, rtol=1e-5):
    """回傳（最大絕對誤差，是否通過）；explanation 必須已選好單一輸出（二維）。"""
    values = np.asarray(explanation.values, dtype=float)
    if values.ndim != 2:
        raise ValueError("先用 exp[..., k] 選好單一輸出")
    base = np.broadcast_to(np.asarray(explanation.base_values, dtype=float), (values.shape[0],))
    expected = np.asarray(expected, dtype=float)
    error = np.abs(base + values.sum(axis=1) - expected)
    return float(error.max()), bool(np.all(error <= atol + rtol * np.abs(expected)))
```

- `expected` 是模型自己的輸出：同一批列、同樣順序、同一個輸出空間（`predict`、`decision_function` 或 `predict_proba[:, k]`）。
- 報告最大絕對誤差、容差，以及被解釋輸出的標準差，讓讀者看得出誤差相對有多大。
- 失敗時（shap 自己丟出 `ExplainerError` 也算失敗）不放寬容差，也不用 `check_additivity=False` 關掉檢查。依序確認：列與順序相同；欄位、欄序、dtype、缺值表示與模型訓練及預測時相同；是同一個已訓練的模型；輸出與單位選對；只拿一列重算。仍失敗就改用下面的方法。

**HistGradientBoosting 以 float64 訓練時（實測）**：interventional TreeExplainer 解釋訓練期之後的列時，本流程幾組合成資料的可加性最大誤差是 3.6e-4 到 7.3e-3（輸出量級約 1），shap 自己沒有報錯，因為 0.54.1 的 TreeExplainer 內部檢查用 atol=1e-2、rtol=1e-2（原始碼 `shap/explainers/_tree.py`）；解釋訓練用的列時誤差達 0.17 到 0.29，shap 丟出 `ExplainerError`。同一批資料改成 float32 可表示的值再訓練，誤差都在 1e-7 以下。二元分類器以 float64 訓練時，raw 與 probability 輸出也失敗。只有 interventional 受影響：同一個 float64 模型用不給背景的 `shap.TreeExplainer(model)`（tree_path_dependent）通過。在這些測試中，結果取決於訓練資料：float32 訓練的模型改用 float64 的列解釋仍然通過；float64 訓練的模型改用 float32 的列解釋仍然失敗。原因未能確認。

- 先查專案訓練時送進模型的 dtype；不論是哪一種都要做上面的檢查。不要為了讓檢查通過而重新訓練模型。
- 失敗時改用 `shap.PermutationExplainer(model.predict, masker, seed=固定)`，用同一份背景；在同樣的資料上可加性誤差約 1e-15。`max_evals` 只給最小值 `2 * 特徵數 + 1` 時，單列的值與精確值最多差 0.10（平均絕對 SHAP 約 0.19），各特徵的平均絕對 SHAP 最多差 6%；給到最小值的 10 倍時，分別降到約 0.035 與 1%。所以至少給 10 倍，並用兩個種子各跑一次，比較結果。
- 或改用不給背景的 `shap.TreeExplainer(model)`（見第 2 節補充），並在報告寫明換了賽局。

## 4. 背景資料與抽樣

- `shap.maskers.Independent(bg, max_samples=len(bg))` 會用到全部背景列。直接把 DataFrame 或陣列交給 explainer，或用 `Independent(bg)` 的預設值，只會用到 100 列，shap 以 logging 警告提示（實測）。
- 實際用到的列數：TreeExplainer 看 `explainer.data`，LinearExplainer 與 PermutationExplainer 看 `explainer.masker.data`（實測的屬性名）。報告寫這個數字。
- base value 等於被解釋的輸出在背景資料上的平均（TreeExplainer 與 PermutationExplainer 實測），所以換背景就會換基準與歸因。結論重要時，換一個早於解釋期的背景期間或種子再算一次，列出差異。
- 要解釋的列：全部，或以固定種子事先抽樣；先用少量列試跑並計時，再決定列數。

## 5. 多輸出

- 先看 `np.asarray(exp.values).ndim`。2 是單一輸出；3 是（列、特徵、輸出），用 `exp[..., k]` 選輸出。`exp[k]` 選到的是第 k 列，不是第 k 個輸出（實測）。
- 不要把不同輸出的 SHAP 值平均，也不要比較不同輸出空間的 SHAP 大小。比較兩個模型時，只有同一批列、同一個輸出與單位、同一份背景，才比較 SHAP 的大小；條件不同時只比較排序與「接近零」的判斷。
- HistGradientBoostingClassifier 二元的 raw 與 probability 都是單一輸出；`model_output="predict_proba"` 才是（列、特徵、2）（實測）。
- 範例的 `select_single_output` 遇到三維卻沒指定輸出時會丟 `ValueError`。

## 6. permutation importance 交叉檢查

- 只需要 numpy、pandas 與 scikit-learn。可以用專案原本的直譯器執行（不安裝任何東西，加 `-B`），也可以在 SHAP 環境執行。
- 呼叫 `sklearn.inspection.permutation_importance(model, X_holdout, y_holdout, scoring=..., n_repeats=10, random_state=固定)`。`X_holdout` 是依時間保留、標籤已實現的樣本外列，通常就是 SHAP 解釋的那些列（規則見 [time-series-rules.md](time-series-rules.md)）。迴歸用 `"neg_mean_squared_error"`，二元分類可用 `"neg_log_loss"`。
- 整組一起打亂：把範例的 `grouped_permutation_importance` 與 `_RowPositionView` 複製到稽核腳本（範例檔本身會 import shap，所以不要直接 import 它）。它用同一個列順序打亂整組特徵，內部仍呼叫 `permutation_importance`；每組只有一個特徵時，與直接呼叫的結果完全相同（測試確認；分類用負 log loss 也實測相同）。相關特徵整組打亂的重要性可以遠大於逐一打亂的總和（實測一對相關特徵：整組 1.12，逐一相加 0.64）。
- 同時報告保留期上模型的分數與天真基準（例如一律預測訓練期平均值）的分數，讓 permutation 的分數下降有尺度可比；這只是脈絡，不代表模型有效。範例把兩者寫進 `audit_metadata.json`。
- 同一天所有股票共用的特徵怎麼打亂，見 [time-series-rules.md](time-series-rules.md) 第 6 節。
- 判斷「這組有沒有作用」的規則要在計算前寫下。範例的規則：SHAP 占全部平均絕對 SHAP 的比例低於 5% 視為接近零；permutation 的平均值減兩倍標準差不大於 0 視為接近零。兩者的尺度不同（permutation 是分數的下降，MSE 是平方單位），只比較判斷，不比較數值或占比。
- 兩種方法對同一組的判斷不一致時：列出兩邊的數字，寫明不一致，然後調查可能原因，例如模型用了這組、但它在樣本外沒有幫助；相關的組互相替代；背景期間的選擇。不要只挑其中一個結果。
- 實測：範例用預設參數、5 個種子，兩種方法都把「雜訊」組判為接近零（SHAP 占比 0.7% 到 3.7%），其他組都判為有作用；資料較少（1,920 列）或標籤改為 5 日時，部分種子出現不一致。

## 7. 組合模型

- 最終輸出若是幾個模型輸出的加權和，而且各部分用同一批特徵、同一份背景與同一種 masker，可以分別解釋再依權重相加（實測：float32 訓練的 HistGradientBoostingRegressor 加 Ridge，與用 ExactExplainer 直接解釋整個和相差 1.5e-7）。
- 最終輸出若再經過非線性轉換（例如機率校準），改用 PermutationExplainer 解釋整個預測函式，並對同一個函式做第 3 節的檢查。

## 8. 圖表

```python
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # 在 import shap 之前；不開視窗
import matplotlib.pyplot as plt
import shap

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Noto Sans CJK TC", "WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def save_bar(explanation, output_dir: Path, title: str, name: str = "shap_bar.png") -> int:
    """畫平均絕對 SHAP 長條圖，存到呼叫端給的資料夾（同名檔已存在就不寫）；回傳缺字警告的數量。"""
    path = output_dir / name
    if path.exists():
        raise FileExistsError(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ax = shap.plots.bar(explanation, max_display=15, show=False)
        ax.set_title(title)
        ax.figure.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(ax.figure)
    return sum("missing from font" in str(w.message) for w in caught)
```

- `output_dir` 由呼叫端提供，放在使用者指定、repository 外的資料夾；寫進 repository 要使用者明確要求。同名檔已存在時丟出 `FileExistsError`，不覆寫。
- `title` 寫出輸出、單位、背景期間，以及「模型行為，非因果」，例如「predict（未來報酬）的平均絕對 SHAP；背景 2024-01-05 至 2024-09-09；模型行為，非因果」。
- 回傳值大於 0 表示有中文字沒畫出來：回報，不把那張圖當成可用的成品。
- 實測（Linux，中文特徵名與上例標題）：在有 WenQuanYi Zen Hei 的機器上，`save_bar` 回傳 0，圖上中文正常；字型清單只留 DejaVu Sans 時回傳 82。同名檔已存在時丟出 `FileExistsError`。`shap.plots.bar` 與 `shap.plots.beeswarm` 在 `show=False` 時回傳 `Axes`。
- Windows 上 Microsoft JhengHei 的實際顯示沒有測試，未能確認。
- 只畫已選好單一輸出的二維 explanation。
