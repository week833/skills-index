"""shap-model-audit 範例：在合成的時間序列面板資料上，稽核已訓練模型在樣本外期間用了哪些特徵。

流程：
1. 產生合成的「日期 × 股票」面板。特徵分四組；「雜訊」組在資料生成時對目標完全沒有作用。
2. 依日期切分，不打亂：前段是訓練期，接著留 horizon 個交易日的間隔，之後是解釋期（樣本外）。
3. 在訓練期訓練兩個示範用模型（只用合成資料，與任何專案的模型無關）：
   HistGradientBoostingRegressor，以及 SimpleImputer → StandardScaler → Ridge 的 Pipeline。
4. 背景資料只從訓練期以固定種子抽樣；用 SHAP 解釋解釋期的列，並對模型自己的輸出檢查可加性；
   模型在解釋的列上輸出不變（常數模型）時停下。
5. 計算每個特徵與每個特徵組的平均絕對 SHAP；在同一批解釋期的列上做 permutation importance
   交叉檢查（逐一特徵，以及整組一起打亂），並記下模型與天真基準在這些列上的 MSE（只作脈絡）。
6. 寫入 --output-dir，並印出繁體中文摘要。

只用合成資料：不連網、不讀檔，程式本身只寫入 --output-dir（必須是絕對路徑）；
輸出檔已存在時不覆寫。
（import shap 會載入 matplotlib；matplotlib 第一次載入時可能在使用者的快取資料夾建立字型快取，
這是函式庫的行為，不是本程式寫的檔。）

退出碼：0 完成；1 可加性檢查失敗或模型輸出是常數；2 參數或輸出資料夾不合用。1 與 2 都不寫任何輸出檔。

輸出只描述模型在指定資料與背景下的行為；不是因果證據、不是交易訊號，也不證明模型有效。

執行（PowerShell 一行；python 換成另外建立、裝有 shap 的環境的直譯器）：
    python -B examples/shap_time_ordered_example.py --output-dir <輸出資料夾的絕對路徑>
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # import shap 會一併載入 matplotlib；固定用不開視窗的 Agg 後端

import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_GROUPS: dict[str, list[str]] = {
    "海外市場": ["us_index_ret", "us_semi_ret"],
    "價格動能": ["ret_5d", "ret_20d"],
    "成交量": ["volume_z"],
    "雜訊": ["noise_a", "noise_b"],
}
NO_EFFECT_GROUP = "雜訊"
FEATURES: list[str] = [name for names in FEATURE_GROUPS.values() for name in names]
SCORING = "neg_mean_squared_error"
STATEMENT = "本結果只描述模型在指定資料、期間與背景下的行為；不是因果證據、不是交易訊號，也不證明模型有效。"
SCORE_NOTE = "保留期 MSE 只作脈絡：不代表模型有效，也不是交易績效。"
CSV_NAME = "importance.csv"
JSON_NAME = "audit_metadata.json"
DEFAULT_ATOL = 1e-6
DEFAULT_RTOL = 1e-5


class AdditivityError(RuntimeError):
    """SHAP 值加總對不回模型自己的輸出。"""


class DegenerateModelError(RuntimeError):
    """模型在解釋的列上輸出不變，不能用來判斷哪組特徵有沒有作用。"""


class SettingsError(ValueError):
    """參數或輸出資料夾不合用。"""


@dataclass
class ModelAudit:
    model_name: str
    explained_output: str
    explainer: str
    max_abs_error: float
    output_std: float
    holdout_mse: float
    naive_mse: float
    table: pd.DataFrame = field(repr=False)


# ---------------------------------------------------------------------------
# 資料與時間切分
# ---------------------------------------------------------------------------
def make_synthetic_panel(n_dates: int, n_stocks: int, horizon: int, seed: int) -> pd.DataFrame:
    """合成面板：每列的特徵依構造在當日就已知；target 是之後 horizon 個交易日的累積報酬（小數）。"""
    rng = np.random.default_rng(seed)
    total = n_dates + horizon  # 多產生 horizon 天，讓保留的每一列都有已實現的標籤
    dates = pd.bdate_range("2024-01-02", periods=total)
    us_index = rng.normal(0.0, 0.010, total)
    us_semi = 0.8 * us_index + rng.normal(0.0, 0.006, total)  # 與 us_index 高度相關
    frames = []
    for stock in range(n_stocks):
        ret_5d = rng.normal(0.0, 0.03, total)
        ret_20d = 0.6 * ret_5d + rng.normal(0.0, 0.04, total)
        volume_z = rng.normal(0.0, 1.0, total)
        volume_z[rng.random(total) < 0.05] = np.nan  # 約 5% 缺值，示範 SimpleImputer
        noise_a = rng.normal(0.0, 1.0, total)
        noise_b = rng.normal(0.0, 1.0, total)
        signal = (
            0.5 * us_index
            + 0.3 * us_semi
            + 0.004 * np.tanh(ret_5d / 0.03)
            - 0.05 * ret_20d
            + np.where(volume_z > 1.0, 0.006, 0.0)
        )  # noise_a、noise_b 不進入 signal
        next_day = signal + rng.normal(0.0, 0.008, total)  # 第 d 列：d 收盤到 d+1 收盤的報酬
        target = pd.Series(next_day).rolling(horizon).sum().shift(-(horizon - 1)).to_numpy()
        frames.append(
            pd.DataFrame(
                {
                    "date": dates,
                    "stock": f"S{stock:02d}",
                    "us_index_ret": us_index,
                    "us_semi_ret": us_semi,
                    "ret_5d": ret_5d,
                    "ret_20d": ret_20d,
                    "volume_z": volume_z,
                    "noise_a": noise_a,
                    "noise_b": noise_b,
                    "target": target,
                }
            ).iloc[:n_dates]
        )
    panel = pd.concat(frames, ignore_index=True).sort_values(["date", "stock"], ignore_index=True)
    if panel["target"].isna().any():
        raise ValueError("synthetic target has unmatured labels")
    return panel


def split_dates(dates: pd.Series, train_frac: float, horizon: int) -> tuple[pd.DatetimeIndex, pd.DatetimeIndex, pd.DatetimeIndex]:
    """依日期切成訓練期、間隔、解釋期；間隔恰好 horizon 個交易日，不打亂。

    訓練期最後一天的標籤涵蓋之後 horizon 個交易日，全部落在間隔內，早於解釋期第一天。
    """
    unique = pd.DatetimeIndex(sorted(pd.unique(dates)))
    n_train = int(len(unique) * train_frac)
    if n_train < 2 or n_train + horizon >= len(unique):
        raise ValueError("not enough dates for train window, gap and explain window")
    return unique[:n_train], unique[n_train : n_train + horizon], unique[n_train + horizon :]


# ---------------------------------------------------------------------------
# SHAP：輸出選擇、可加性、重要性彙總
# ---------------------------------------------------------------------------
def select_single_output(explanation: shap.Explanation, output_index: int | None = None) -> shap.Explanation:
    """明確處理多輸出：二維（列、特徵）直接用；三維（列、特徵、輸出）必須指定 output_index。"""
    ndim = np.asarray(explanation.values).ndim
    if ndim == 2:
        if output_index not in (None, 0):
            raise ValueError("explanation has a single output; output_index must be None or 0")
        return explanation
    if ndim == 3:
        if output_index is None:
            raise ValueError("explanation has several outputs; pass output_index explicitly")
        return explanation[..., output_index]
    raise ValueError(f"unexpected SHAP value shape {np.shape(explanation.values)}")


def check_additivity(explanation: shap.Explanation, expected: np.ndarray, atol: float, rtol: float) -> float:
    """base_values + values.sum(axis=1) 必須在容差內等於模型自己的輸出；回傳最大絕對誤差。"""
    values = np.asarray(explanation.values, dtype=float)
    if values.ndim != 2:
        raise ValueError("select one output before checking additivity")
    base = np.broadcast_to(np.asarray(explanation.base_values, dtype=float), (values.shape[0],))
    reconstructed = base + values.sum(axis=1)
    expected = np.asarray(expected, dtype=float)
    if reconstructed.shape != expected.shape:
        raise ValueError(f"shape mismatch {reconstructed.shape} vs {expected.shape}")
    if not (np.isfinite(reconstructed).all() and np.isfinite(expected).all()):
        raise AdditivityError("模型輸出或 SHAP 值含有 NaN 或無限大")
    error = np.abs(reconstructed - expected)
    if not np.all(error <= atol + rtol * np.abs(expected)):
        raise AdditivityError(f"最大絕對誤差 {error.max():.3e} 超過容差（atol={atol:g}、rtol={rtol:g}）")
    return float(error.max())


def check_not_constant(explanation: shap.Explanation, expected: np.ndarray, model_name: str) -> None:
    """模型在解釋的列上輸出不變，或 SHAP 值全為 0 時停下：常數模型照實回報，不說成「這組特徵沒有作用」。"""
    expected = np.asarray(expected, dtype=float)
    if float(np.ptp(expected)) <= 1e-12 * (1.0 + float(np.abs(expected).max())) or not np.any(np.asarray(explanation.values)):
        raise DegenerateModelError(f"{model_name} 在解釋的列上輸出是常數（SHAP 值全為 0 或輸出不變），不能用來判斷特徵組有沒有作用")


def shap_importance(explanation: shap.Explanation, groups: dict[str, list[str]]) -> tuple[pd.Series, pd.Series]:
    """特徵：mean(|SHAP|)。組：先把同組 SHAP 逐列相加（保留正負抵銷），再取 mean(|總和|)。"""
    values = np.asarray(explanation.values, dtype=float)
    names = list(explanation.feature_names)
    per_feature = pd.Series(np.abs(values).mean(axis=0), index=names)
    per_group = pd.Series(
        {g: float(np.abs(values[:, [names.index(c) for c in cols]].sum(axis=1)).mean()) for g, cols in groups.items()}
    )
    return per_feature, per_group


# ---------------------------------------------------------------------------
# permutation importance（零額外相依：只用 scikit-learn）
# ---------------------------------------------------------------------------
class _RowPositionView:
    """給 permutation_importance 用的占位估計器；實際評分由 scorer 依列位置重建特徵後計算。"""

    def fit(self, X, y=None):  # noqa: N803 - scikit-learn 介面
        return self


def grouped_permutation_importance(score, X: pd.DataFrame, y, groups: dict[str, list[str]], *, n_repeats: int, random_state: int):
    """整組一起打亂的 permutation importance，用 sklearn.inspection.permutation_importance 計算。

    傳給 sklearn 的是「列位置」矩陣：每欄代表一組，初值都是 0..n-1。sklearn 打亂某一欄，
    等於把該組所有特徵用同一個列順序一起打亂。score(y_true, X_rebuilt) 回傳越大越好的分數。
    每組只有一個特徵時，結果與直接對 X 呼叫 permutation_importance（同一 random_state）相同。
    """
    covered = [c for cols in groups.values() for c in cols]
    if sorted(covered) != sorted(X.columns) or len(covered) != len(set(covered)):
        raise ValueError("groups must partition the columns of X")
    columns = {g: [(c, X[c].to_numpy()) for c in cols] for g, cols in groups.items()}
    names = list(groups)

    def rebuild(positions: np.ndarray) -> pd.DataFrame:
        positions = np.asarray(positions, dtype=np.intp)
        data = {}
        for j, g in enumerate(names):
            for c, values in columns[g]:
                data[c] = values[positions[:, j]]
        return pd.DataFrame(data, columns=X.columns)

    def scorer(_estimator, positions, y_true):
        return score(np.asarray(y_true), rebuild(positions))

    positions = np.tile(np.arange(len(X), dtype=np.intp)[:, None], (1, len(names)))
    result = permutation_importance(
        _RowPositionView(), positions, np.asarray(y), scoring=scorer, n_repeats=n_repeats, random_state=random_state
    )
    return pd.Series(result.importances_mean, index=names), pd.Series(result.importances_std, index=names)


def _shares(values: pd.Series) -> pd.Series:
    positive = values.clip(lower=0.0)
    total = float(positive.sum())
    return positive / total if total > 0 else positive * 0.0


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def audit_model(model_name, explanation, expected, predict_for_score, X_explain, y_explain, naive_value, args, explained_output, explainer_name):
    one = select_single_output(explanation)
    max_err = check_additivity(one, expected, args.atol, args.rtol)
    check_not_constant(one, expected, model_name)
    shap_f, shap_g = shap_importance(one, FEATURE_GROUPS)
    # 保留期的分數只作脈絡（讓 permutation 的分數下降有尺度可比），不代表模型有效。
    holdout_mse = float(mean_squared_error(y_explain, expected))
    naive_mse = float(mean_squared_error(y_explain, np.full(len(y_explain), naive_value)))

    def score(y_true, X_rebuilt):
        return -mean_squared_error(y_true, predict_for_score(X_rebuilt))

    singles = {c: [c] for c in FEATURES}
    perm_f, perm_f_std = grouped_permutation_importance(score, X_explain, y_explain, singles, n_repeats=args.n_repeats, random_state=args.seed)
    perm_g, perm_g_std = grouped_permutation_importance(score, X_explain, y_explain, FEATURE_GROUPS, n_repeats=args.n_repeats, random_state=args.seed)
    group_of = {c: g for g, cols in FEATURE_GROUPS.items() for c in cols}
    rows = []
    for level, s_val, p_val, p_std in (("feature", shap_f, perm_f, perm_f_std), ("group", shap_g, perm_g, perm_g_std)):
        s_share = _shares(s_val)
        for name in s_val.index:
            # 兩種方法的尺度不同（permutation 以 MSE 的增加計，是平方單位），所以各用自己的判斷規則：
            # SHAP：占全部平均絕對 SHAP 的比例低於門檻；permutation：平均值減兩倍標準差不大於 0。
            shap_zero = bool(s_share[name] < args.near_zero_share)
            perm_zero = bool(p_val[name] - 2.0 * p_std[name] <= 0.0)
            rows.append(
                {
                    "model": model_name,
                    "level": level,
                    "name": name,
                    "group": group_of[name] if level == "feature" else name,
                    "mean_abs_shap": float(s_val[name]),
                    "shap_share": float(s_share[name]),
                    "perm_importance_mean": float(p_val[name]),
                    "perm_importance_std": float(p_std[name]),
                    "shap_near_zero": shap_zero,
                    "perm_near_zero": perm_zero,
                    "methods_agree": shap_zero == perm_zero,
                }
            )
    return ModelAudit(
        model_name, explained_output, explainer_name, max_err, float(np.std(expected)), holdout_mse, naive_mse, pd.DataFrame(rows)
    )


def run_audit(args: argparse.Namespace) -> dict:
    panel = make_synthetic_panel(args.n_dates, args.n_stocks, args.horizon, args.seed)
    try:
        train_dates, gap_dates, explain_dates = split_dates(panel["date"], args.train_frac, args.horizon)
    except ValueError as exc:
        raise SettingsError("交易日數不足以切出訓練期、間隔與解釋期；請增加 --n-dates，或調整 --train-frac 與 --horizon") from exc
    train = panel[panel["date"].isin(train_dates)]
    explain_pool = panel[panel["date"].isin(explain_dates)]
    background = train.sample(n=min(args.background_size, len(train)), random_state=args.seed).sort_values(["date", "stock"])
    explain = explain_pool
    if len(explain_pool) > args.max_explain_rows:  # 事先宣告的固定種子抽樣，不挑「好看」的列
        explain = explain_pool.sample(n=args.max_explain_rows, random_state=args.seed).sort_values(["date", "stock"])
    if not background["date"].max() < explain["date"].min():
        raise AssertionError("background must end before the first explained date")

    X_train, y_train = train[FEATURES], train["target"].to_numpy()
    X_bg, X_ex, y_ex = background[FEATURES], explain[FEATURES], explain["target"].to_numpy()
    naive_value = float(y_train.mean())  # 天真基準：一律預測訓練期的平均報酬
    audits = []

    # 模型一：HGB。特徵型別與訓練時一致（float32）；early_stopping=False，避免內部隨機切驗證集。
    hgb = HistGradientBoostingRegressor(
        max_iter=150, learning_rate=0.05, max_leaf_nodes=7, min_samples_leaf=200,
        l2_regularization=1.0, early_stopping=False, random_state=args.seed,
    ).fit(X_train.astype(np.float32), y_train)
    bg32, ex32 = X_bg.astype(np.float32), X_ex.astype(np.float32)
    tree = shap.TreeExplainer(
        hgb, data=shap.maskers.Independent(bg32, max_samples=len(bg32)),
        feature_perturbation="interventional", model_output="raw",
    )
    audits.append(
        audit_model(
            "HistGradientBoostingRegressor", tree(ex32), hgb.predict(ex32), hgb.predict, ex32, y_ex, naive_value, args,
            "predict（未來報酬，小數）", "TreeExplainer（interventional，model_output=raw）",
        )
    )

    # 模型二：Pipeline。在前處理後的空間用 LinearExplainer；插補與標準化逐欄進行，所以每欄仍對應一個原始特徵。
    pipe = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=1.0)),
        ]
    ).fit(X_train, y_train)
    pre = pipe[:-1]
    names = list(pre.get_feature_names_out())
    if names != FEATURES:
        raise AssertionError("preprocessing changed the feature columns")
    z_bg = pd.DataFrame(pre.transform(X_bg), columns=names)
    z_ex = pd.DataFrame(pre.transform(X_ex), columns=names)
    linear = shap.LinearExplainer(pipe[-1], shap.maskers.Independent(z_bg, max_samples=len(z_bg)))
    audits.append(
        audit_model(
            "Pipeline(SimpleImputer→StandardScaler→Ridge)", linear(z_ex), pipe.predict(X_ex), pipe.predict, X_ex, y_ex, naive_value, args,
            "predict（未來報酬，小數）", "LinearExplainer（前處理後空間，Independent masker）",
        )
    )

    def day(ts) -> str:
        return pd.Timestamp(ts).strftime("%Y-%m-%d")

    sampled = len(explain) < len(explain_pool)
    meta = {
        "data": "合成面板資料（不連網、不讀檔）",
        "seed": args.seed,
        "horizon_trading_days": args.horizon,
        "data_last_date": day(panel["date"].max()),
        "train_window": [day(train_dates[0]), day(train_dates[-1])],
        "train_rows": int(len(train)),
        "gap_dates": [day(d) for d in gap_dates],
        "explain_window": [day(explain_dates[0]), day(explain_dates[-1])],
        "explain_rows": int(len(explain)),
        "explain_pool_rows": int(len(explain_pool)),
        "explain_selection": f"從 {len(explain_pool)} 列以固定種子 {args.seed} 抽樣" if sampled else "解釋期全部的列",
        "background_rows": int(len(background)),
        "background_window": [day(background["date"].min()), day(background["date"].max())],
        "background_selection": f"訓練期內以固定種子 {args.seed} 抽樣",
        "feature_groups": FEATURE_GROUPS,
        "no_effect_group_by_construction": NO_EFFECT_GROUP,
        "permutation": {"scoring": SCORING, "n_repeats": args.n_repeats, "random_state": args.seed, "rows": "與 SHAP 解釋的列相同"},
        "near_zero_rule": {
            "shap": f"占全部平均絕對 SHAP 的比例低於 {args.near_zero_share}",
            "permutation": "importance_mean - 2 * importance_std <= 0",
        },
        "near_zero_share": args.near_zero_share,
        "additivity_tolerance": {"atol": args.atol, "rtol": args.rtol},
        "holdout_score_note": SCORE_NOTE,
        "naive_baseline": "一律預測訓練期目標的平均值",
        "models": [
            {
                "model": a.model_name,
                "explained_output": a.explained_output,
                "explainer": a.explainer,
                "max_abs_additivity_error": a.max_abs_error,
                "explained_output_std": a.output_std,
                "holdout_mse": a.holdout_mse,
                "naive_baseline_mse": a.naive_mse,
            }
            for a in audits
        ],
        "versions": {"python": platform.python_version(), "platform": platform.platform()}
        | {p: importlib.metadata.version(p) for p in ("shap", "scikit-learn", "numpy", "pandas", "scipy", "matplotlib")},
        "statement": STATEMENT,
    }
    return {"audits": audits, "meta": meta}


def existing_outputs(output_dir: Path) -> list[Path]:
    return [p for p in (output_dir / CSV_NAME, output_dir / JSON_NAME) if p.exists()]


def write_outputs(result: dict, output_dir: Path) -> list[Path]:
    """只新建檔案（模式 "x"）：同名檔已存在時丟出 FileExistsError，不覆寫。"""
    if existing_outputs(output_dir):
        raise FileExistsError(str(output_dir))
    output_dir.mkdir(parents=True, exist_ok=True)
    table = pd.concat([a.table for a in result["audits"]], ignore_index=True)
    csv_path = output_dir / CSV_NAME
    with csv_path.open("x", encoding="utf-8", newline="") as handle:
        table.to_csv(handle, index=False, lineterminator="\n", float_format="%.6g")
    json_path = output_dir / JSON_NAME
    with json_path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result["meta"], ensure_ascii=False, indent=2) + "\n")
    return [csv_path, json_path]


def summary_lines(result: dict, paths: list[Path]) -> list[str]:
    m = result["meta"]
    lines = [
        "SHAP 模型稽核範例（合成資料，研究用途）",
        f"訓練期 {m['train_window'][0]} 至 {m['train_window'][1]}（{m['train_rows']} 列）；"
        f"間隔 {len(m['gap_dates'])} 個交易日；解釋期 {m['explain_window'][0]} 至 {m['explain_window'][1]}"
        f"（{m['explain_rows']} 列，{m['explain_selection']}）",
        f"背景資料：{m['background_rows']} 列，{m['background_selection']}（{m['background_window'][0]} 至 {m['background_window'][1]}）",
    ]
    for a in result["audits"]:
        groups = a.table[a.table["level"] == "group"]
        lines.append(f"[{a.model_name}] 解釋的輸出：{a.explained_output}；{a.explainer}")
        lines.append(
            f"  可加性：最大絕對誤差 {a.max_abs_error:.2e}（容差 atol={m['additivity_tolerance']['atol']:g}、"
            f"rtol={m['additivity_tolerance']['rtol']:g}；輸出標準差 {a.output_std:.2e}），通過"
        )
        lines.append(f"  保留期 MSE {a.holdout_mse:.3e}；天真基準 MSE {a.naive_mse:.3e}。{SCORE_NOTE}")
        for _, r in groups.sort_values("mean_abs_shap", ascending=False).iterrows():
            lines.append(
                f"  {r['name']}：平均絕對 SHAP {r['mean_abs_shap']:.2e}（占 {r['shap_share']:.1%}）；"
                f"permutation（MSE 增加）{r['perm_importance_mean']:.2e}±{r['perm_importance_std']:.1e}"
            )
        disagree = groups[~groups["methods_agree"]]["name"].tolist()
        lines.append("  兩種方法對「是否接近零」的判斷：" + ("一致" if not disagree else "不一致，需調查：" + "、".join(disagree)))
    lines.append(
        f"「接近零」的規則（事先設定，篩選用，不是統計檢定）：SHAP 占比低於 {m['near_zero_share']:.0%}；"
        "permutation 平均值減兩倍標準差不大於 0"
    )
    lines.append(STATEMENT)
    lines.extend(f"輸出：{p}" for p in paths)
    return lines


def _number(text: str, kind, message: str):
    try:
        return kind(text)
    except ValueError:
        raise argparse.ArgumentTypeError(message) from None


def _positive_int(text: str) -> int:
    value = _number(text, int, "必須是 1 以上的整數")
    if value < 1:
        raise argparse.ArgumentTypeError("必須是 1 以上的整數")
    return value


def _seed(text: str) -> int:
    value = _number(text, int, "必須是 0 到 4294967295 的整數")
    if not 0 <= value <= 2**32 - 1:
        raise argparse.ArgumentTypeError("必須是 0 到 4294967295 的整數")
    return value


def _fraction(text: str) -> float:
    value = _number(text, float, "必須是介於 0 與 1 之間的數")
    if not (math.isfinite(value) and 0.0 < value < 1.0):
        raise argparse.ArgumentTypeError("必須是介於 0 與 1 之間的數")
    return value


def _tolerance(limit: float):
    message = f"必須是大於 0、不超過 {limit:g} 的數（容差只能收緊，不能放寬）"

    def parse(text: str) -> float:
        value = _number(text, float, message)
        if not (math.isfinite(value) and 0.0 < value <= limit):
            raise argparse.ArgumentTypeError(message)
        return value

    return parse


def _output_dir(text: str) -> Path:
    if not text.strip():
        raise argparse.ArgumentTypeError("必須指定輸出資料夾")
    path = Path(text)
    if not path.is_absolute():
        raise argparse.ArgumentTypeError("必須是絕對路徑（放在 repository 與 skill 資料夾以外）")
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="以合成時間序列資料示範 SHAP 模型稽核（研究用途，不連網、不讀檔）")
    p.add_argument("--output-dir", type=_output_dir, required=True, help="輸出資料夾的絕對路徑（只寫入這裡；同名檔已存在時不覆寫）")
    p.add_argument("--seed", type=_seed, default=7, help="資料生成、抽樣、模型與 permutation 的固定種子")
    p.add_argument("--n-dates", type=_positive_int, default=300, help="交易日數")
    p.add_argument("--n-stocks", type=_positive_int, default=20, help="股票數")
    p.add_argument("--train-frac", type=_fraction, default=0.6, help="訓練期占全部日期的比例")
    p.add_argument("--horizon", type=_positive_int, default=1, help="標籤涵蓋的交易日數，也是訓練期與解釋期之間的間隔")
    p.add_argument("--background-size", type=_positive_int, default=200, help="背景資料列數（只從訓練期抽）")
    p.add_argument("--max-explain-rows", type=_positive_int, default=1000, help="解釋期最多解釋幾列（超過就以固定種子抽樣）")
    p.add_argument("--n-repeats", type=_positive_int, default=10, help="permutation importance 的重複次數")
    p.add_argument("--atol", type=_tolerance(DEFAULT_ATOL), default=DEFAULT_ATOL, help="可加性檢查的絕對容差（只能收緊）")
    p.add_argument("--rtol", type=_tolerance(DEFAULT_RTOL), default=DEFAULT_RTOL, help="可加性檢查的相對容差（只能收緊）")
    p.add_argument("--near-zero-share", type=_fraction, default=0.05, help="SHAP 占比低於此值視為接近零（篩選用）")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.output_dir.exists() and not args.output_dir.is_dir():
        print(f"輸出路徑已存在但不是資料夾，未寫入任何輸出：{args.output_dir}", file=sys.stderr)
        return 2
    if existing_outputs(args.output_dir):
        print(f"輸出檔已存在，不覆寫，也未寫入任何輸出：{args.output_dir}（請換一個資料夾）", file=sys.stderr)
        return 2
    try:
        result = run_audit(args)
    except AdditivityError as exc:
        print(f"可加性檢查失敗，未寫入任何輸出：{exc}", file=sys.stderr)
        return 1
    except DegenerateModelError as exc:
        print(f"模型輸出是常數，未寫入任何輸出：{exc}", file=sys.stderr)
        return 1
    except SettingsError as exc:
        print(f"參數不合用，未寫入任何輸出：{exc}", file=sys.stderr)
        return 2
    try:
        paths = write_outputs(result, args.output_dir)
    except FileExistsError:
        print(f"輸出檔已存在，不覆寫：{args.output_dir}（請換一個資料夾）", file=sys.stderr)
        return 2
    print("\n".join(summary_lines(result, paths)))
    return 0


def _force_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


if __name__ == "__main__":
    _force_utf8_stdio()
    raise SystemExit(main())
