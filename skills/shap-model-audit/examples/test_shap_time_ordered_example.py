"""shap_time_ordered_example.py 的 pytest 測試。

只用合成資料；不連網、不讀專案或中央資料；輸出只寫進 pytest 的 tmp_path。
後半段的測試用同一組輔助函式，實際確認 references/shap-recipes.md 表格裡各模型的
explainer 呼叫、輸出空間與可加性，以及第 3 節 float64 段落的三個結論。

執行（PowerShell 一行，在 skill 資料夾內；python 換成另外建立、裝有 shap 的環境的直譯器）：
    python -B -m pytest -q -p no:cacheprovider examples/test_shap_time_ordered_example.py
"""
from __future__ import annotations

import importlib.util
import json
import socket
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import shap
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

EXAMPLE_PATH = Path(__file__).with_name("shap_time_ordered_example.py")
_spec = importlib.util.spec_from_file_location("shap_time_ordered_example", EXAMPLE_PATH)
ex = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = ex  # dataclass 需要模組已登錄
_spec.loader.exec_module(ex)


def _block_network(mp: pytest.MonkeyPatch) -> None:
    def refuse(*_args, **_kwargs):
        raise AssertionError("network access attempted")

    mp.setattr(socket.socket, "connect", refuse)
    mp.setattr(socket.socket, "connect_ex", refuse)
    mp.setattr(socket, "create_connection", refuse)


@pytest.fixture(scope="module")
def default_run(tmp_path_factory):
    """以預設參數跑一次（禁止網路；工作目錄設在 root，寫到工作目錄的檔也會被測到），供多個測試共用。"""
    root = tmp_path_factory.mktemp("default_run")
    out = root / "out"
    with pytest.MonkeyPatch.context() as mp:
        _block_network(mp)
        mp.chdir(root)
        code = ex.main(["--output-dir", str(out)])
    table = pd.read_csv(out / ex.CSV_NAME, encoding="utf-8")
    meta = json.loads((out / ex.JSON_NAME).read_text(encoding="utf-8"))
    return {"code": code, "root": root, "out": out, "table": table, "meta": meta}


# ---------------------------------------------------------------------------
# 時間切分與背景資料
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("horizon", [1, 5])
def test_split_dates_keeps_order_and_leaves_horizon_gap(horizon):
    dates = pd.Series(pd.bdate_range("2024-01-02", periods=40))
    train, gap, explain = ex.split_dates(dates, 0.5, horizon)
    assert len(gap) == horizon
    assert train.max() < gap.min() and gap.max() < explain.min()
    assert list(train.append(gap).append(explain)) == list(dates)  # 沒有打亂、沒有遺漏


def test_split_dates_refuses_windows_that_do_not_fit():
    dates = pd.Series(pd.bdate_range("2024-01-02", periods=10))
    with pytest.raises(ValueError):
        ex.split_dates(dates, 0.9, 5)


def test_synthetic_panel_is_deterministic_and_time_ordered():
    a = ex.make_synthetic_panel(30, 3, 2, seed=1)
    b = ex.make_synthetic_panel(30, 3, 2, seed=1)
    pd.testing.assert_frame_equal(a, b)
    assert a["date"].is_monotonic_increasing
    assert a["target"].notna().all()


def test_windows_in_metadata_respect_point_in_time(default_run):
    meta = default_run["meta"]
    assert meta["background_window"][1] <= meta["train_window"][1] < meta["gap_dates"][0]
    assert meta["gap_dates"][-1] < meta["explain_window"][0]
    assert len(meta["gap_dates"]) == meta["horizon_trading_days"]


# ---------------------------------------------------------------------------
# 主程式的輸出
# ---------------------------------------------------------------------------
def test_main_succeeds_without_network_and_writes_only_output_dir(default_run):
    assert default_run["code"] == 0
    assert sorted(p.name for p in default_run["root"].iterdir()) == ["out"]
    assert sorted(p.name for p in default_run["out"].iterdir()) == sorted([ex.CSV_NAME, ex.JSON_NAME])


def test_additivity_within_tolerance_for_both_models(default_run):
    meta = default_run["meta"]
    atol = meta["additivity_tolerance"]["atol"]
    assert len(meta["models"]) == 2
    for model in meta["models"]:
        assert model["max_abs_additivity_error"] <= atol


def test_no_effect_group_is_near_zero_by_both_methods(default_run):
    table = default_run["table"]
    groups = table[table["level"] == "group"]
    assert set(groups["model"]) == {m["model"] for m in default_run["meta"]["models"]}
    for _, g in groups.groupby("model"):
        g = g.set_index("name")
        noise = g.loc[ex.NO_EFFECT_GROUP]
        assert bool(noise["shap_near_zero"]) and bool(noise["perm_near_zero"])
        assert g["mean_abs_shap"].idxmin() == ex.NO_EFFECT_GROUP
        assert g["perm_importance_mean"].idxmin() == ex.NO_EFFECT_GROUP
        assert g["mean_abs_shap"].idxmax() == "海外市場"
        assert g["perm_importance_mean"].idxmax() == "海外市場"
        assert g["methods_agree"].all()


def test_summary_is_traditional_chinese_and_states_limits(tmp_path, capsys):
    code = ex.main(["--output-dir", str(tmp_path / "o"), "--n-dates", "120", "--n-stocks", "8", "--n-repeats", "2"])
    assert code == 0
    out = capsys.readouterr().out
    assert "可加性" in out and "背景資料" in out and "permutation" in out
    assert "天真基準" in out and ex.SCORE_NOTE in out
    assert ex.STATEMENT in out


def test_holdout_scores_are_recorded_as_context(default_run):
    for model in default_run["meta"]["models"]:
        assert model["holdout_mse"] > 0 and model["naive_baseline_mse"] > 0
    assert default_run["meta"]["holdout_score_note"] == ex.SCORE_NOTE


def test_runs_are_reproducible(default_run, tmp_path):
    out = tmp_path / "again"
    assert ex.main(["--output-dir", str(out)]) == 0
    first = default_run["out"]
    assert (out / ex.CSV_NAME).read_bytes() == (first / ex.CSV_NAME).read_bytes()
    assert (out / ex.JSON_NAME).read_bytes() == (first / ex.JSON_NAME).read_bytes()


def test_additivity_failure_stops_without_writing(tmp_path, monkeypatch, capsys):
    def always_fails(*_args, **_kwargs):
        raise ex.AdditivityError("forced for test")

    monkeypatch.setattr(ex, "check_additivity", always_fails)
    out = tmp_path / "never"
    assert ex.main(["--output-dir", str(out), "--n-dates", "120", "--n-stocks", "8"]) == 1
    assert not out.exists()
    assert "可加性檢查失敗" in capsys.readouterr().err


def test_constant_model_stops_instead_of_reporting_no_effect(tmp_path, capsys):
    out = tmp_path / "const"  # 只有 20 列訓練資料：HGB（min_samples_leaf=200）切不出任何分支，輸出是常數
    assert ex.main(["--output-dir", str(out), "--n-dates", "8", "--n-stocks", "5"]) == 1
    assert not out.exists()
    assert "常數" in capsys.readouterr().err


def test_existing_output_files_are_not_overwritten(tmp_path, capsys):
    out = tmp_path / "existing"
    out.mkdir()
    (out / ex.CSV_NAME).write_text("USER DATA\n", encoding="utf-8")
    assert ex.main(["--output-dir", str(out), "--n-dates", "120", "--n-stocks", "8"]) == 2
    assert (out / ex.CSV_NAME).read_text(encoding="utf-8") == "USER DATA\n"
    assert sorted(p.name for p in out.iterdir()) == [ex.CSV_NAME]
    assert "已存在" in capsys.readouterr().err


def test_too_few_dates_stop_with_a_message_and_no_output(tmp_path, capsys):
    out = tmp_path / "few"
    assert ex.main(["--output-dir", str(out), "--n-dates", "3"]) == 2
    assert not out.exists()
    assert "交易日數不足" in capsys.readouterr().err


@pytest.mark.parametrize("value", ["", "   ", "relative_out"])
def test_output_dir_must_be_a_non_empty_absolute_path(value, capsys):
    with pytest.raises(SystemExit) as info:
        ex.parse_args(["--output-dir", value])
    assert info.value.code == 2
    assert "必須" in capsys.readouterr().err


@pytest.mark.parametrize(
    "extra", [["--seed", "-1"], ["--seed", "4294967296"], ["--n-dates", "abc"], ["--atol", "1e-3"], ["--rtol", "0.1"]]
)
def test_invalid_arguments_are_rejected_in_chinese(extra, tmp_path, capsys):
    with pytest.raises(SystemExit) as info:
        ex.parse_args(["--output-dir", str(tmp_path / "x"), *extra])
    assert info.value.code == 2
    assert "必須" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# 輔助函式
# ---------------------------------------------------------------------------
def _toy(n=600, f=4, seed=0, dtype=np.float32):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, f))
    X[:, 1] = 0.8 * X[:, 0] + 0.6 * X[:, 1]
    y = 0.5 * X[:, 0] + 0.3 * X[:, 1] - 0.4 * X[:, 2] + 0.2 * X[:, 2] * X[:, 3] + rng.normal(scale=0.5, size=n)
    cols = [f"x{i}" for i in range(f)]
    return pd.DataFrame(X.astype(dtype), columns=cols), y


def test_check_additivity_detects_a_wrong_output():
    X, y = _toy(dtype=np.float64)
    model = Ridge().fit(X.iloc[:400], y[:400])
    exp = shap.LinearExplainer(model, shap.maskers.Independent(X.iloc[:100], max_samples=100))(X.iloc[400:])
    assert ex.check_additivity(exp, model.predict(X.iloc[400:]), 1e-6, 1e-5) < 1e-6
    with pytest.raises(ex.AdditivityError):
        ex.check_additivity(exp, model.predict(X.iloc[400:]) + 1e-3, 1e-6, 1e-5)
    # Ridge：SHAP 值等於 coef_ ×（x − 背景平均）
    expected = model.coef_ * (X.iloc[400:] - X.iloc[:100].mean()).to_numpy()
    np.testing.assert_allclose(np.asarray(exp.values), expected, atol=1e-12)


def test_group_total_sums_within_each_row_before_taking_absolute_values():
    values = np.array([[1.0, -1.0, 0.5], [2.0, -2.0, -0.5]])
    exp = shap.Explanation(values=values, base_values=np.zeros(2), data=np.zeros((2, 3)), feature_names=["a", "b", "c"])
    per_feature, per_group = ex.shap_importance(exp, {"ab": ["a", "b"], "c": ["c"]})
    assert per_feature.to_dict() == {"a": 1.5, "b": 1.5, "c": 0.5}
    assert per_group.to_dict() == {"ab": 0.0, "c": 0.5}  # a 與 b 逐列抵銷；不是 1.5 + 1.5


def test_grouped_permutation_shuffles_each_group_with_one_row_order():
    n = 200
    idx = np.arange(n, dtype=float)
    X = pd.DataFrame({"a": idx, "b": 10.0 * idx, "c": -idx})
    seen = {"calls": 0, "ab_moved": 0, "c_moved": 0, "split_group": 0}

    def score(_y_true, X_rebuilt):
        seen["calls"] += 1
        a, b, c = (X_rebuilt[k].to_numpy() for k in ("a", "b", "c"))
        seen["split_group"] += int(not np.array_equal(b, 10.0 * a))  # 同組的 a、b 必須用同一個列順序
        seen["ab_moved"] += int(not np.array_equal(a, idx))
        seen["c_moved"] += int(not np.array_equal(c, -idx))
        return 0.0

    ex.grouped_permutation_importance(score, X, np.zeros(n), {"ab": ["a", "b"], "c": ["c"]}, n_repeats=3, random_state=0)
    assert seen["split_group"] == 0
    assert seen["ab_moved"] == 3 and seen["c_moved"] == 3
    assert seen["calls"] == 1 + 2 * 3  # 基準一次，每組各 n_repeats 次


def test_grouped_permutation_with_single_feature_groups_matches_sklearn():
    X, y = _toy()
    model = HistGradientBoostingRegressor(max_iter=30, random_state=0).fit(X.iloc[:400], y[:400])
    Xh, yh = X.iloc[400:], y[400:]

    def score(y_true, X_rebuilt):
        return -mean_squared_error(y_true, model.predict(X_rebuilt))

    mine, _ = ex.grouped_permutation_importance(score, Xh, yh, {c: [c] for c in X.columns}, n_repeats=5, random_state=0)
    ref = permutation_importance(model, Xh, yh, scoring="neg_mean_squared_error", n_repeats=5, random_state=0)
    np.testing.assert_array_equal(mine.to_numpy(), ref.importances_mean)


def test_grouped_permutation_requires_a_partition():
    X, y = _toy()
    with pytest.raises(ValueError):
        ex.grouped_permutation_importance(lambda yt, xr: 0.0, X, y, {"a": ["x0"]}, n_repeats=1, random_state=0)


def test_pipeline_transformed_linear_matches_raw_space_permutation():
    X, y = _toy(dtype=np.float64)
    X = X.mask(np.random.default_rng(1).random(X.shape) < 0.1)  # 10% 缺值
    pipe = Pipeline(
        [("impute", SimpleImputer(strategy="median", keep_empty_features=True)), ("scale", StandardScaler()), ("ridge", Ridge())]
    ).fit(X.iloc[:400], y[:400])
    bg, rows = X.iloc[:100], X.iloc[400:450]
    pre = pipe[:-1]
    linear = shap.LinearExplainer(pipe[-1], shap.maskers.Independent(pre.transform(bg), max_samples=len(bg)))(pre.transform(rows))

    def predict_raw(a):
        return pipe.predict(pd.DataFrame(a, columns=X.columns))

    perm = shap.PermutationExplainer(predict_raw, shap.maskers.Independent(bg, max_samples=len(bg)), seed=0)(
        rows, max_evals=2 * X.shape[1] + 1
    )
    assert list(pre.get_feature_names_out()) == list(X.columns)
    assert ex.check_additivity(linear, pipe.predict(rows), 1e-6, 1e-5) < 1e-6
    assert ex.check_additivity(perm, pipe.predict(rows), 1e-6, 1e-5) < 1e-6
    np.testing.assert_allclose(np.asarray(perm.values), np.asarray(linear.values), atol=1e-9)


# ---------------------------------------------------------------------------
# 各模型的 explainer、輸出空間與可加性（對應 references/shap-recipes.md）
# ---------------------------------------------------------------------------
def _interventional(model, bg, **kw):
    return shap.TreeExplainer(model, data=shap.maskers.Independent(bg, max_samples=len(bg)), feature_perturbation="interventional", **kw)


def test_hgb_regressor_tree_explainer_reconstructs_predict():
    X, y = _toy()
    model = HistGradientBoostingRegressor(max_iter=50, random_state=0).fit(X.iloc[:400], y[:400])
    rows = X.iloc[400:500]
    exp = _interventional(model, X.iloc[:100])(rows)
    assert np.asarray(exp.values).shape == rows.shape
    assert ex.check_additivity(exp, model.predict(rows), 1e-6, 1e-5) < 1e-6
    path = shap.TreeExplainer(model)(rows)  # 不給背景：tree_path_dependent，是另一種賽局（game）
    assert ex.check_additivity(path, model.predict(rows), 1e-6, 1e-5) < 1e-6


def test_float64_trained_hgb_interventional_additivity_gap():
    """shap-recipes.md 第 3 節：float64 訓練的 HGB 在 interventional 下可加性不成立，shap 自己的檢查只在誤差大時報錯。"""
    X, y = _toy(dtype=np.float64)
    model = HistGradientBoostingRegressor(max_iter=100, random_state=0).fit(X.iloc[:400], y[:400])
    explainer = _interventional(model, X.iloc[:100])
    later = X.iloc[400:500]
    exp = explainer(later)  # 沒有例外
    with pytest.raises(ex.AdditivityError):
        ex.check_additivity(exp, model.predict(later), 1e-6, 1e-5)
    with pytest.raises(Exception) as info:  # 訓練用的列：誤差更大，shap 丟出 ExplainerError
        explainer(X.iloc[100:200])
    assert type(info.value).__name__ == "ExplainerError"
    path = shap.TreeExplainer(model)(later)  # 同一個模型，tree_path_dependent 通過
    assert ex.check_additivity(path, model.predict(later), 1e-6, 1e-5) < 1e-6


def test_hgb_binary_classifier_raw_is_log_odds_and_probability_is_single_output():
    X, y = _toy()
    yb = (y > 0).astype(int)
    model = HistGradientBoostingClassifier(max_iter=50, random_state=0).fit(X.iloc[:400], yb[:400])
    rows, bg = X.iloc[400:500], X.iloc[:100]
    raw = _interventional(model, bg, model_output="raw")(rows)
    assert np.asarray(raw.values).ndim == 2
    assert ex.check_additivity(raw, model.decision_function(rows), 1e-6, 1e-5) < 1e-6
    prob = _interventional(model, bg, model_output="probability")(rows)
    assert np.asarray(prob.values).ndim == 2
    assert ex.check_additivity(prob, model.predict_proba(rows)[:, 1], 1e-6, 1e-5) < 1e-6


def test_hgb_multiclass_raw_needs_explicit_output_selection():
    X, y = _toy()
    y3 = np.digitize(y, [-0.5, 0.5])
    model = HistGradientBoostingClassifier(max_iter=20, random_state=0).fit(X.iloc[:400], y3[:400])
    rows, bg = X.iloc[400:440], X.iloc[:50]
    raw = _interventional(model, bg, model_output="raw")(rows)
    assert np.asarray(raw.values).shape == (len(rows), X.shape[1], 3)
    with pytest.raises(ValueError):
        ex.select_single_output(raw)
    margins = model.decision_function(rows)
    for k in range(3):
        assert ex.check_additivity(ex.select_single_output(raw, k), margins[:, k], 1e-6, 1e-5) < 1e-6
    with pytest.raises(NotImplementedError):
        _interventional(model, bg, model_output="probability")(rows)


def test_logistic_linear_explainer_is_log_odds_and_probability_needs_a_callable():
    X, y = _toy(dtype=np.float64)
    yb = (y > 0).astype(int)
    model = LogisticRegression(max_iter=1000, random_state=0).fit(X.iloc[:400], yb[:400])
    rows, bg = X.iloc[400:450], X.iloc[:100]
    lin = shap.LinearExplainer(model, shap.maskers.Independent(bg, max_samples=len(bg)))(rows)
    assert ex.check_additivity(lin, model.decision_function(rows), 1e-6, 1e-5) < 1e-6
    p = model.predict_proba(rows)[:, 1]
    np.testing.assert_allclose(model.decision_function(rows), np.log(p / (1 - p)), atol=1e-9)  # 二元：log-odds

    def proba_up(a):
        return model.predict_proba(pd.DataFrame(a, columns=X.columns))[:, 1]

    explainer = shap.PermutationExplainer(proba_up, shap.maskers.Independent(bg, max_samples=len(bg)), seed=0)
    perm = explainer(rows, max_evals=2 * X.shape[1] + 1)
    assert ex.check_additivity(perm, proba_up(rows), 1e-6, 1e-5) < 1e-6
    with pytest.raises(ValueError):
        explainer(rows.iloc[:2], max_evals=2 * X.shape[1])


def test_logistic_multiclass_scores_are_softmax_inputs_not_log_odds():
    X, y = _toy(dtype=np.float64)
    y3 = np.digitize(y, [-0.5, 0.5])
    model = LogisticRegression(max_iter=1000, random_state=0).fit(X.iloc[:400], y3[:400])
    rows, bg = X.iloc[400:450], X.iloc[:100]
    exp = shap.LinearExplainer(model, shap.maskers.Independent(bg, max_samples=len(bg)))(rows)
    assert np.asarray(exp.values).shape == (len(rows), X.shape[1], 3)
    scores = model.decision_function(rows)
    for k in range(3):
        assert ex.check_additivity(ex.select_single_output(exp, k), scores[:, k], 1e-6, 1e-5) < 1e-6
    proba = model.predict_proba(rows)
    np.testing.assert_allclose(np.exp(scores) / np.exp(scores).sum(axis=1, keepdims=True), proba, rtol=1e-9)
    assert not np.allclose(scores, np.log(proba / (1 - proba)))  # 不是各類的 log-odds


def test_coefficient_only_linear_head_and_tuple_returning_replay():
    """專案只存係數（dict 或 JSON）、以自己的函式重播時的兩種作法（shap-recipes.md 第 2 節）。"""
    X, y = _toy(dtype=np.float64)
    X = X.mask(np.random.default_rng(2).random(X.shape) < 0.1)
    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    scaler = StandardScaler()
    z_fit = scaler.fit_transform(imputer.fit_transform(X.iloc[:400].to_numpy(dtype=float)))
    logistic = LogisticRegression(max_iter=500, random_state=0).fit(z_fit, (y[:400] > 0).astype(int))
    head = {"medians": imputer.statistics_, "mean": scaler.mean_, "scale": scaler.scale_,
            "coef": logistic.coef_[0], "intercept": float(logistic.intercept_[0])}

    def standardize(a):
        a = np.asarray(a, dtype=float)
        return (np.where(np.isnan(a), head["medians"], a) - head["mean"]) / head["scale"]

    def replay(a):  # 仿專案的重播函式：一次回傳兩個輸出
        logit = standardize(a) @ head["coef"] + head["intercept"]
        return 1.0 / (1.0 + np.exp(-logit)), logit

    bg, rows = X.iloc[:100].to_numpy(dtype=float), X.iloc[400:450].to_numpy(dtype=float)
    z_masker = shap.maskers.Independent(standardize(bg), max_samples=len(bg))
    lin = shap.LinearExplainer((head["coef"], head["intercept"]), z_masker)(standardize(rows))
    assert ex.check_additivity(lin, replay(rows)[1], 1e-6, 1e-5) < 1e-6
    raw_masker = shap.maskers.Independent(bg, max_samples=len(bg))
    with pytest.raises(AssertionError):  # shap 0.54.1：回傳 tuple 的函式不能直接交給 explainer
        shap.PermutationExplainer(replay, raw_masker, seed=0)(rows[:2], max_evals=2 * X.shape[1] + 1)
    perm = shap.PermutationExplainer(lambda a: replay(a)[1], raw_masker, seed=0)(rows, max_evals=2 * X.shape[1] + 1)
    assert ex.check_additivity(perm, replay(rows)[1], 1e-6, 1e-5) < 1e-6
    np.testing.assert_allclose(np.asarray(perm.values), np.asarray(lin.values), atol=1e-9)


def test_bare_background_is_capped_at_100_rows():
    X, y = _toy()
    model = HistGradientBoostingRegressor(max_iter=10, random_state=0).fit(X, y)
    capped = shap.TreeExplainer(model, data=X.iloc[:250], feature_perturbation="interventional")
    kept = _interventional(model, X.iloc[:250])
    assert np.shape(capped.data)[0] == 100
    assert np.shape(kept.data)[0] == 250
