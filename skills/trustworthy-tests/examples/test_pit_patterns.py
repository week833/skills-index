"""時點正確性（point-in-time，PIT）測試樣式的可執行範例。

樣式 (a) 到 (h) 各有三樣東西：

- 正確實作：函式名結尾是 ``_correct``。
- 故意做錯的實作：結尾是 ``_leaky``（用到未來資料）或 ``_wrong``（對錯列），
  只供示範，不可抄進研究程式。
- 檢查函式：``check_`` 開頭；對正確實作不出聲，對做錯的實作丟 ``AssertionError``。

名稱含 ``passes`` 的測試證明檢查在正確實作上通過；名稱含 ``detects`` 的測試用
``pytest.raises`` 證明同一個檢查在做錯的實作上會失敗，而且失敗訊息是預期的那一種。
其餘測試是手算預期值的比對，以及檢查本身抓不到什麼的示範。

資料全是手打的合成小資料；行事曆是虛構的，不代表任何交易所的實際休市日。
測試本身不連網、不讀專案資料或中央資料、不寫檔，只用 pandas、numpy 與 pytest。
執行時會顯示的字串（斷言訊息）一律用 ASCII。
"""
from __future__ import annotations

from typing import Callable, Iterator

import numpy as np
import pandas as pd
import pytest

SEED = 20261113
RTOL = 1e-12

# 虛構的本地交易日：3/9、3/10、3/16、3/17 是週末，3/13、3/14 是虛構的休市日。
LOCAL_DATES = pd.to_datetime(
    [
        "2024-03-04", "2024-03-05", "2024-03-06", "2024-03-07", "2024-03-08",
        "2024-03-11", "2024-03-12", "2024-03-15",
        "2024-03-18", "2024-03-19", "2024-03-20",
    ]
)
CLOSES = [10.0, 13.0, 13.0, 16.0, 13.0, 19.0, 16.0, 22.0, 16.0, 25.0, 19.0]


def make_close() -> pd.Series:
    return pd.Series(CLOSES, index=LOCAL_DATES, name="close")


def shaken_copies(series: pd.Series, start: int) -> Iterator[pd.Series]:
    """把第 start 列（含）之後的值擾動兩次：一次放大、一次變號，再加上固定種子的雜訊。

    只往同一邊放大時，中位數這類統計量可能完全不動，洩漏就躲過去了；
    見 test_f_fit_check_detects_full_sample_median。整數欄先轉成浮點數，
    寫回小數時 pandas 才不會發出型別警告。
    """
    rng = np.random.default_rng(SEED)
    for scale in (10.0, -10.0):
        shaken = series.astype(float)
        noise = rng.normal(size=len(series) - start)
        shaken.iloc[start:] = shaken.iloc[start:].to_numpy() * scale + noise
        yield shaken


def on_input_dates(output: pd.Series, index: pd.Index) -> pd.Series:
    """依輸入的日期對齊輸出，所以會丟掉列的函式（例如最後接 dropna）也能檢查。

    輸出的索引若不是輸入的日期，對齊後會變成全部 NaN，檢查就形同虛設，所以直接報錯。
    """
    if not output.index.isin(index).all():
        raise AssertionError("bad output index: outputs must be indexed by the input dates")
    return output.reindex(index)


# ---------------------------------------------------------------------------
# (a) 截斷不變性：拿掉 t 之後的列，t（含）以前的結果不可以變
# ---------------------------------------------------------------------------


def trailing_mean_correct(close: pd.Series) -> pd.Series:
    """當列與前兩列的平均。"""
    return close.rolling(3).mean()


def trailing_mean_leaky(close: pd.Series) -> pd.Series:
    """置中視窗：第 t 列用到了第 t+1 列。"""
    return close.rolling(3, center=True).mean()


def trailing_mean_dropna_correct(close: pd.Series) -> pd.Series:
    """同 trailing_mean_correct，但丟掉開頭算不出來的列：輸出比輸入少兩列。"""
    return close.rolling(3).mean().dropna()


def trailing_mean_dropna_leaky(close: pd.Series) -> pd.Series:
    """置中視窗再丟掉 NaN 的列。"""
    return close.rolling(3, center=True).mean().dropna()


def past_mean_prediction_correct(close: pd.Series) -> pd.Series:
    """最簡單的模型：對第 t 列的預測，是第 t 列之前所有列的平均。"""
    return close.expanding().mean().shift(1)


def full_sample_mean_prediction_leaky(close: pd.Series) -> pd.Series:
    """先用全部資料算出平均（等於用全部資料訓練），再回頭對每一列預測。"""
    return pd.Series(close.mean(), index=close.index)


def recency_weight_leaky(close: pd.Series) -> pd.Series:
    """以整份資料的最後一列為基準算權重：同一天的權重隨後面還有幾列而變。"""
    age = np.arange(len(close))[::-1]
    return pd.Series(0.5 ** (age / 5.0), index=close.index)


def check_truncation_invariance(func: Callable[[pd.Series], pd.Series], series: pd.Series) -> None:
    """對每個截止列：只給到該列的資料算出的結果，必須等於用全部資料算出後取到該列的結果。

    兩邊都依輸入的日期對齊；全部是 NaN（或沒有輸入）時沒有東西可比，直接報錯，不讓檢查空轉。
    """
    full = on_input_dates(func(series), series.index)
    if full.isna().all():
        raise AssertionError("nothing to compare: output is empty or all NaN")
    for stop in range(1, len(series) + 1):
        truncated = on_input_dates(func(series.iloc[:stop]), series.index[:stop])
        np.testing.assert_allclose(
            truncated.to_numpy(dtype=float),
            full.iloc[:stop].to_numpy(dtype=float),
            rtol=RTOL,
            atol=0.0,
            err_msg=f"look-ahead: output up to {series.index[stop - 1].date()} changes without later rows",
        )


def test_a_truncation_check_passes_on_trailing_window():
    check_truncation_invariance(trailing_mean_correct, make_close())


def test_a_truncation_check_detects_centered_window():
    # 手推：只留 3/4、3/5 兩列時，3/5 的置中視窗少了 3/6 那一列，結果由 12 變成 NaN。
    with pytest.raises(AssertionError, match="look-ahead: output up to 2024-03-05 changes"):
        check_truncation_invariance(trailing_mean_leaky, make_close())


def test_a_truncation_check_passes_on_prediction_from_past_rows():
    check_truncation_invariance(past_mean_prediction_correct, make_close())
    # 手算：3/6 的預測是 3/4、3/5 兩列的平均 (10+13)/2 = 11.5。
    assert past_mean_prediction_correct(make_close()).loc["2024-03-06"] == pytest.approx(11.5, rel=RTOL)


def test_a_truncation_check_detects_prediction_fitted_on_all_rows():
    # 手推：只留 3/4 一列時平均是 10；全部資料的平均是 182/11，不是 10。
    with pytest.raises(AssertionError, match="look-ahead: output up to 2024-03-04 changes"):
        check_truncation_invariance(full_sample_mean_prediction_leaky, make_close())


# ---------------------------------------------------------------------------
# (b) 未來擾動不變性：改掉 t 之後的值，t（含）以前的結果不可以變
# ---------------------------------------------------------------------------


def make_close_with_gap() -> pd.Series:
    close = make_close()
    close.iloc[3] = np.nan  # 3/7 沒有收盤價
    return close


def make_close_with_leading_gap() -> pd.Series:
    close = make_close_with_gap()
    close.iloc[0] = np.nan  # 3/4 也沒有收盤價：序列一開頭就缺值
    return close


def fill_gap_correct(close: pd.Series) -> pd.Series:
    """缺值沿用前一列。"""
    return close.ffill()


def fill_gap_leaky(close: pd.Series) -> pd.Series:
    """缺值拿後一列來補：3/7 用到了 3/8 的值。"""
    return close.bfill()


def fill_gap_then_backfill_start_leaky(close: pd.Series) -> pd.Series:
    """先沿用前一列，開頭補不到的再拿後一列來補：3/4 用到了 3/5 的值。"""
    return close.ffill().bfill()


def check_future_perturbation_invariance(func: Callable[[pd.Series], pd.Series], series: pd.Series) -> None:
    """對每個截止列：擾動該列之後的值，該列（含）以前的結果必須不變。

    兩邊都依輸入的日期對齊；全部是 NaN（或沒有輸入）時沒有東西可比，直接報錯。
    """
    baseline = on_input_dates(func(series), series.index)
    if baseline.isna().all():
        raise AssertionError("nothing to compare: output is empty or all NaN")
    for stop in range(1, len(series)):
        for shaken in shaken_copies(series, stop):
            np.testing.assert_allclose(
                on_input_dates(func(shaken), series.index).iloc[:stop].to_numpy(dtype=float),
                baseline.iloc[:stop].to_numpy(dtype=float),
                rtol=RTOL,
                atol=0.0,
                err_msg=f"look-ahead: output up to {series.index[stop - 1].date()} depends on later values",
            )


def test_b_perturbation_check_passes_on_forward_fill():
    check_future_perturbation_invariance(fill_gap_correct, make_close_with_gap())


def test_b_perturbation_check_detects_backward_fill():
    close = make_close_with_gap()
    # 這份資料上兩種補法在 3/7 剛好都得到 13，只比對數值看不出差別；擾動才看得出來。
    assert fill_gap_correct(close).iloc[3] == fill_gap_leaky(close).iloc[3] == 13.0
    with pytest.raises(AssertionError, match="look-ahead: output up to 2024-03-07 depends"):
        check_future_perturbation_invariance(fill_gap_leaky, close)


def test_ab_row_count_leak_is_seen_by_truncation_but_not_by_perturbation():
    # (b) 只改值、不改列數，所以抓不到「結果取決於後面還有幾列」；(a) 抓得到。
    check_future_perturbation_invariance(recency_weight_leaky, make_close())
    with pytest.raises(AssertionError, match="look-ahead: output up to 2024-03-04 changes"):
        check_truncation_invariance(recency_weight_leaky, make_close())


def test_ab_checks_detect_backfilled_start_with_leading_gap():
    close = make_close_with_leading_gap()
    check_truncation_invariance(fill_gap_correct, close)
    check_future_perturbation_invariance(fill_gap_correct, close)
    # 手推：3/4 沒有收盤價，往前補之後再往回補，3/4 拿到 3/5 的 13；
    # 只留 3/4 一列時它是 NaN，擾動 3/5 之後的值時它也跟著變。
    assert fill_gap_then_backfill_start_leaky(close).iloc[0] == 13.0
    with pytest.raises(AssertionError, match="look-ahead: output up to 2024-03-04 changes"):
        check_truncation_invariance(fill_gap_then_backfill_start_leaky, close)
    with pytest.raises(AssertionError, match="look-ahead: output up to 2024-03-04 depends"):
        check_future_perturbation_invariance(fill_gap_then_backfill_start_leaky, close)


def test_ab_backfilled_start_is_invisible_without_a_leading_gap():
    # 資料開頭沒有缺值時，同一個洩漏兩種檢查都看不到；測試資料要涵蓋開頭缺值的情況。
    check_truncation_invariance(fill_gap_then_backfill_start_leaky, make_close_with_gap())
    check_future_perturbation_invariance(fill_gap_then_backfill_start_leaky, make_close_with_gap())


def test_ab_checks_align_outputs_by_date_when_rows_are_dropped():
    # 正確的函式丟掉開頭兩列時，兩種檢查都依日期對齊，不會誤報；置中視窗照樣抓得到。
    check_truncation_invariance(trailing_mean_dropna_correct, make_close())
    check_future_perturbation_invariance(trailing_mean_dropna_correct, make_close())
    with pytest.raises(AssertionError, match="look-ahead: output up to 2024-03-05 changes"):
        check_truncation_invariance(trailing_mean_dropna_leaky, make_close())


def test_ab_checks_refuse_outputs_that_leave_nothing_to_compare():
    # 輸出換成了 0 起算的位置索引，或全部是 NaN 時，對齊後沒有東西可比；檢查要報錯，不可以空轉通過。
    def positional(close: pd.Series) -> pd.Series:
        return close.reset_index(drop=True).rolling(3, center=True).mean()

    with pytest.raises(AssertionError, match="^bad output index"):
        check_truncation_invariance(positional, make_close())
    with pytest.raises(AssertionError, match="^nothing to compare"):
        check_future_perturbation_invariance(lambda close: close * np.nan, make_close())
    with pytest.raises(AssertionError, match="^nothing to compare"):
        check_truncation_invariance(trailing_mean_leaky, make_close().iloc[:0])


# ---------------------------------------------------------------------------
# (c) as-of 合併：用「可得日」往回找，不用數字所描述的期間
# ---------------------------------------------------------------------------


def make_revenue() -> pd.DataFrame:
    """虛構的月營收：period_end 是數字描述的月份，available_date 是公告日。"""
    return pd.DataFrame(
        {
            "period_end": pd.to_datetime(["2024-01-31", "2024-02-29"]),
            "available_date": pd.to_datetime(["2024-02-07", "2024-03-08"]),
            "revenue": [100.0, 120.0],
        }
    )


def join_revenue_correct(dates: pd.DatetimeIndex, revenue: pd.DataFrame) -> pd.DataFrame:
    """以可得日往回找，而且不收同一天（本例假設公告在當天決策時點之後）。"""
    return pd.merge_asof(
        pd.DataFrame({"date": dates}),
        revenue.sort_values("available_date"),
        left_on="date",
        right_on="available_date",
        direction="backward",
        allow_exact_matches=False,
    )


def join_revenue_by_period_leaky(dates: pd.DatetimeIndex, revenue: pd.DataFrame) -> pd.DataFrame:
    """以所屬期間合併：二月營收 3/4 就出現，但 3/8 才公告。"""
    return pd.merge_asof(
        pd.DataFrame({"date": dates}),
        revenue.sort_values("period_end"),
        left_on="date",
        right_on="period_end",
        direction="backward",
    )


def join_revenue_forward_leaky(dates: pd.DatetimeIndex, revenue: pd.DataFrame) -> pd.DataFrame:
    """方向寫成 forward：拿到的是下一筆還沒公告的數字。"""
    return pd.merge_asof(
        pd.DataFrame({"date": dates}),
        revenue.sort_values("available_date"),
        left_on="date",
        right_on="available_date",
        direction="forward",
    )


def join_revenue_same_day_leaky(dates: pd.DatetimeIndex, revenue: pd.DataFrame) -> pd.DataFrame:
    """沿用預設 allow_exact_matches=True：公告當天就用上了。"""
    return pd.merge_asof(
        pd.DataFrame({"date": dates}),
        revenue.sort_values("available_date"),
        left_on="date",
        right_on="available_date",
        direction="backward",
    )


def check_join_respects_availability(joined: pd.DataFrame) -> None:
    """併進來的每一筆，可得日都必須早於該列日期。"""
    matched = joined.dropna(subset=["available_date"])
    late = matched.loc[matched["available_date"] >= matched["date"], "date"]
    if not late.empty:
        raise AssertionError(f"look-ahead: figure not yet available, first={late.min().date()} rows={len(late)}")


def test_c_availability_check_passes_and_join_matches_hand_values():
    joined = join_revenue_correct(LOCAL_DATES, make_revenue())
    check_join_respects_availability(joined)
    # 手推：3/4 到 3/8 只看得到一月營收 100；二月營收 3/8 公告，3/11 起才是 120。
    expected = pd.Series([100.0] * 5 + [120.0] * 6, name="revenue")
    pd.testing.assert_series_equal(joined["revenue"], expected, check_exact=False, rtol=RTOL)


@pytest.mark.parametrize(
    ("leaky_join", "first_bad_date", "bad_rows"),
    [
        # 手推：二月營收 3/8 才公告，卻在 3/4 到 3/8 這 5 列就被併進來。
        pytest.param(join_revenue_by_period_leaky, "2024-03-04", 5, id="by_period"),
        pytest.param(join_revenue_forward_leaky, "2024-03-04", 5, id="forward"),
        # 手推：只有公告當天 3/8 這 1 列用到了當天才公告的數字。
        pytest.param(join_revenue_same_day_leaky, "2024-03-08", 1, id="same_day"),
    ],
)
def test_c_availability_check_detects_leaky_joins(leaky_join, first_bad_date, bad_rows):
    joined = leaky_join(LOCAL_DATES, make_revenue())
    with pytest.raises(AssertionError, match=f"look-ahead: .* first={first_bad_date} rows={bad_rows}$"):
        check_join_respects_availability(joined)


# ---------------------------------------------------------------------------
# (d) 標籤對齊：未來 H 列的報酬，位移方向與列數都要對
# ---------------------------------------------------------------------------

HORIZON = 2


def make_panel() -> pd.DataFrame:
    """兩檔股票各 6 列，依股票、日期排序。"""
    return pd.DataFrame(
        {
            "stock_id": ["A"] * 6 + ["B"] * 6,
            "date": list(LOCAL_DATES[:6]) * 2,
            "close": [100.0, 110.0, 121.0, 110.0, 99.0, 108.0, 50.0, 55.0, 44.0, 66.0, 60.0, 63.0],
        }
    )


def forward_return_correct(panel: pd.DataFrame, horizon: int) -> pd.Series:
    future = panel.groupby("stock_id")["close"].shift(-horizon)
    return future / panel["close"] - 1.0


def forward_return_backward_leaky(panel: pd.DataFrame, horizon: int) -> pd.Series:
    """位移方向反了：算出來的是過去 H 列的報酬，當天就已經知道。"""
    past = panel.groupby("stock_id")["close"].shift(horizon)
    return panel["close"] / past - 1.0


def forward_return_cross_stock_leaky(panel: pd.DataFrame, horizon: int) -> pd.Series:
    """沒有逐檔位移：A 的最後 H 列拿到 B 的價格。"""
    return panel["close"].shift(-horizon) / panel["close"] - 1.0


def forward_return_off_by_one_wrong(panel: pd.DataFrame, horizon: int) -> pd.Series:
    """多移了一列：算成 H+1 列的報酬。"""
    future = panel.groupby("stock_id")["close"].shift(-(horizon + 1))
    return future / panel["close"] - 1.0


def forward_return_filled_tail_wrong(panel: pd.DataFrame, horizon: int) -> pd.Series:
    """最後 H 列的未來價格還不存在，卻被補成 0。"""
    return forward_return_correct(panel, horizon).fillna(0.0)


def check_label_alignment(
    label_func: Callable[[pd.DataFrame, int], pd.Series], panel: pd.DataFrame, horizon: int
) -> None:
    """改掉第 j 列的價格：同一檔股票裡只有第 j-H 列與第 j 列的標籤可以變。

    另外，每檔股票最後 H 列的標籤必須是 NaN。panel 的索引須是 0 起算的連續整數。
    這條規則只適用「兩個時點的報酬」這種標籤；看整段路徑或同日排名的標籤要先改寫 allowed。
    """
    panel = panel.astype({"close": float})  # 整數價格先轉成浮點數，放大 1.5 倍時才不會有型別警告
    baseline = label_func(panel, horizon)
    position = panel.groupby("stock_id").cumcount()
    size = panel.groupby("stock_id")["close"].transform("size")
    tail = (position >= size - horizon).to_numpy()
    for row in range(len(panel)):
        bumped = panel.copy()
        bumped.loc[row, "close"] = bumped.loc[row, "close"] * 1.5
        changed = ~np.isclose(label_func(bumped, horizon), baseline, rtol=RTOL, atol=0.0, equal_nan=True)
        same_stock = (panel["stock_id"] == panel.loc[row, "stock_id"]).to_numpy()
        offset = (position - position[row]).to_numpy()
        allowed = same_stock & np.isin(offset, [-horizon, 0]) & ~tail
        if not np.array_equal(changed, allowed):
            raise AssertionError(
                f"misaligned label: bumping row {row} changed labels at rows "
                f"{np.flatnonzero(changed).tolist()}, expected {np.flatnonzero(allowed).tolist()}"
            )
    if not baseline[tail].isna().all():
        raise AssertionError(f"misaligned label: last {horizon} rows of each stock must be NaN")


def test_d_alignment_check_passes_on_forward_return():
    check_label_alignment(forward_return_correct, make_panel(), HORIZON)


def test_d_forward_return_matches_hand_values():
    labels = forward_return_correct(make_panel(), HORIZON)
    # 手算，不經過 shift：A 第 0 列是 121/100-1 = 0.21；每檔最後兩列沒有未來價格。
    expected = [
        121 / 100 - 1, 110 / 110 - 1, 99 / 121 - 1, 108 / 110 - 1, np.nan, np.nan,
        44 / 50 - 1, 66 / 55 - 1, 60 / 44 - 1, 63 / 66 - 1, np.nan, np.nan,
    ]
    np.testing.assert_allclose(labels.to_numpy(), expected, rtol=RTOL, atol=0.0)
    assert labels.iloc[0] == pytest.approx(0.21, rel=RTOL)


@pytest.mark.parametrize(
    ("bad_label", "reason"),
    [
        # 手推：改第 0 列（A 的第一列）的價格，正確的標籤只有第 0 列會變。
        pytest.param(
            forward_return_backward_leaky,
            r"bumping row 0 changed labels at rows \[2\], expected \[0\]",
            id="backward",
        ),
        # 手推：改第 2 列，第 0 列（往前 H 列）與第 2 列的標籤都該變。
        pytest.param(
            forward_return_off_by_one_wrong,
            r"bumping row 2 changed labels at rows \[2\], expected \[0, 2\]",
            id="off_by_one",
        ),
        # 手推：第 4 列是 A 的倒數第二列，不該有標籤；沒有逐檔位移時它用 B 的價格算出了數字。
        pytest.param(
            forward_return_cross_stock_leaky,
            r"bumping row 4 changed labels at rows \[2, 4\], expected \[2\]",
            id="cross_stock",
        ),
        pytest.param(forward_return_filled_tail_wrong, r"last 2 rows of each stock must be NaN", id="filled_tail"),
    ],
)
def test_d_alignment_check_detects_bad_labels(bad_label, reason):
    with pytest.raises(AssertionError, match="misaligned label: " + reason + "$"):
        check_label_alignment(bad_label, make_panel(), HORIZON)


@pytest.mark.filterwarnings("error::FutureWarning")
def test_bd_checks_accept_integer_columns_without_dtype_warnings():
    # 股數或價格是整數欄時，擾動與放大會寫進小數；檢查要先轉成浮點數，不可以觸發 pandas 的型別警告。
    volume = pd.Series(np.arange(1, 12, dtype="int64"), index=LOCAL_DATES, name="volume")
    check_future_perturbation_invariance(lambda series: series.cumsum(), volume)
    check_label_alignment(forward_return_correct, make_panel().astype({"close": "int64"}), HORIZON)


# ---------------------------------------------------------------------------
# (e) 依時間切分：訓練窗在前，且與測試窗之間至少隔 H 列
# ---------------------------------------------------------------------------

LONG_HORIZON = 63


Split = tuple[np.ndarray, np.ndarray]  # (訓練列位置, 測試列位置)


def walk_forward_splits(n_rows: int, n_folds: int, test_size: int, gap: int) -> list[Split]:
    """測試窗從尾端往前排 n_folds 個；訓練窗是測試窗起點再往前扣掉 gap 列之前的全部列。"""
    splits = []
    for fold in range(n_folds):
        test_start = n_rows - (n_folds - fold) * test_size
        splits.append((np.arange(0, test_start - gap), np.arange(test_start, test_start + test_size)))
    return splits


def interleaved_split_leaky(n_rows: int) -> list[Split]:
    """每 10 列抽 1 列當測試，其餘當訓練：和打散後再切一樣，訓練列散在測試列的前後。"""
    rows = np.arange(n_rows)
    return [(rows[rows % 10 != 0], rows[rows % 10 == 0])]


def check_split_respects_horizon(splits: list[Split], horizon: int) -> None:
    """第 t 列的標籤用到第 t+H 列的價格：訓練窗要整個在測試窗之前，兩者之間至少隔 H 列。"""
    for fold, (train, test) in enumerate(splits):
        if len(train) == 0 or len(test) == 0:
            raise AssertionError(f"empty fold: fold {fold} has {len(train)} train rows and {len(test)} test rows")
        last_train, first_test = int(train.max()), int(test.min())
        if last_train >= first_test:
            raise AssertionError(
                f"not time-ordered: fold {fold} trains on row {last_train}, test starts at row {first_test}"
            )
        between = first_test - last_train - 1
        if between < horizon:
            raise AssertionError(
                f"label overlap: fold {fold} leaves {between} rows between train and test, needs {horizon}"
            )


def test_e_split_check_passes_with_gap_of_horizon_rows():
    splits = walk_forward_splits(n_rows=400, n_folds=3, test_size=40, gap=LONG_HORIZON)
    check_split_respects_horizon(splits, LONG_HORIZON)
    train, test = splits[0]
    # 手算：第一折測試窗從 400-3*40 = 280 開始；訓練窗止於 280-63-1 = 216。
    assert (train[0], train[-1], test[0], test[-1]) == (0, 216, 280, 319)
    # 訓練窗最後一列的標籤用到第 216+63 = 279 列，還在測試窗之前。
    assert train[-1] + LONG_HORIZON < test[0]


@pytest.mark.parametrize("gap", [0, LONG_HORIZON - 1], ids=["no_gap", "one_row_short"])
def test_e_split_check_detects_missing_or_short_gap(gap):
    splits = walk_forward_splits(n_rows=400, n_folds=3, test_size=40, gap=gap)
    reason = f"label overlap: fold 0 leaves {gap} rows between train and test, needs 63$"
    with pytest.raises(AssertionError, match=reason):
        check_split_respects_horizon(splits, LONG_HORIZON)


def test_e_split_check_detects_split_that_ignores_time_order():
    # 手推：測試列是 0、10、…、390，訓練列最大是 399。
    with pytest.raises(AssertionError, match="not time-ordered: fold 0 trains on row 399, test starts at row 0$"):
        check_split_respects_horizon(interleaved_split_leaky(n_rows=400), LONG_HORIZON)


def test_e_split_check_detects_empty_fold():
    # 手算：第一折的測試窗從 280 開始，再往前扣 300 列已經不到第 0 列，訓練窗是空的。
    splits = walk_forward_splits(n_rows=400, n_folds=3, test_size=40, gap=300)
    with pytest.raises(AssertionError, match="empty fold: fold 0 has 0 train rows and 40 test rows$"):
        check_split_respects_horizon(splits, LONG_HORIZON)


# ---------------------------------------------------------------------------
# (f) 前處理只用訓練窗擬合：補值用的中位數、標準化用的平均與標準差
# ---------------------------------------------------------------------------

TRAIN_STOP = 4  # 前 4 列是訓練窗，後 2 列是測試窗


def make_feature() -> pd.Series:
    return pd.Series([1.0, 2.0, np.nan, 3.0, 10.0, 20.0], name="feature")


def _statistics(values: pd.Series) -> dict[str, float]:
    fill = float(values.median())  # 預設略過 NaN
    filled = values.fillna(fill).to_numpy()
    return {"fill": fill, "mean": float(filled.mean()), "std": float(filled.std(ddof=0))}


def fit_preprocessing_correct(values: pd.Series, train_stop: int) -> dict[str, float]:
    return _statistics(values.iloc[:train_stop])


def fit_preprocessing_leaky(values: pd.Series, train_stop: int) -> dict[str, float]:
    """統計量用了全部列，測試窗也算了進去。"""
    return _statistics(values)


def fit_median_only_leaky(values: pd.Series, train_stop: int) -> dict[str, float]:
    """只算補值用的中位數，但用了全部列。"""
    return {"fill": float(values.median())}


def check_fit_uses_training_rows_only(
    fit: Callable[[pd.Series, int], dict[str, float]], values: pd.Series, train_stop: int
) -> None:
    """擾動訓練窗之後的值，擬合出來的統計量必須不變（兩邊都是 NaN 也算不變）。"""
    baseline = fit(values, train_stop)
    for shaken in shaken_copies(values, train_stop):
        result = fit(shaken, train_stop)
        for key, value in baseline.items():
            if result[key] != pytest.approx(value, rel=RTOL, abs=0.0, nan_ok=True):
                raise AssertionError(f"look-ahead: fitted {key} depends on rows after the training window")


def test_f_fit_check_passes_and_statistics_match_hand_values():
    check_fit_uses_training_rows_only(fit_preprocessing_correct, make_feature(), TRAIN_STOP)
    statistics = fit_preprocessing_correct(make_feature(), TRAIN_STOP)
    # 手算：訓練窗 [1, 2, NaN, 3] 的中位數是 2；補值後 [1, 2, 2, 3]，平均 2、母體標準差 sqrt(0.5)。
    assert statistics == pytest.approx({"fill": 2.0, "mean": 2.0, "std": 0.5**0.5}, rel=RTOL)


def test_f_fit_check_detects_full_sample_statistics():
    # 手推：第一次擾動（放大）時全樣本中位數仍是 3，所以先被抓到的是平均。
    with pytest.raises(AssertionError, match="look-ahead: fitted mean depends on rows after the training window$"):
        check_fit_uses_training_rows_only(fit_preprocessing_leaky, make_feature(), TRAIN_STOP)


def test_f_one_sided_shake_would_miss_a_leaky_median():
    values = make_feature()
    enlarged = values.copy()
    enlarged.iloc[TRAIN_STOP:] = enlarged.iloc[TRAIN_STOP:] * 10.0
    flipped = values.copy()
    flipped.iloc[TRAIN_STOP:] = flipped.iloc[TRAIN_STOP:] * -10.0
    # 全樣本中位數是 3；把測試窗放大 10 倍後仍是 3，變號後才變成 1。
    assert (values.median(), enlarged.median(), flipped.median()) == (3.0, 3.0, 1.0)


def test_f_fit_check_detects_full_sample_median():
    # 只有中位數用了全部列：放大那次中位數不動，要靠變號那次才抓得到，所以擾動一定要兩個方向。
    with pytest.raises(AssertionError, match="look-ahead: fitted fill depends on rows after the training window$"):
        check_fit_uses_training_rows_only(fit_median_only_leaky, make_feature(), TRAIN_STOP)


@pytest.mark.filterwarnings("ignore:Mean of empty slice:RuntimeWarning")
def test_f_fit_check_passes_when_training_window_is_all_nan():
    # 訓練窗全是缺值時，正確的擬合得到 NaN；兩邊都是 NaN 要算相同，不可以誤報成前視。
    # 對全是缺值的資料取中位數時 numpy 會發出「Mean of empty slice」警告；這裡明確只忽略這一種。
    values = pd.Series([np.nan, np.nan, np.nan, np.nan, 10.0, 20.0], name="feature")
    check_fit_uses_training_rows_only(fit_preprocessing_correct, values, TRAIN_STOP)


# ---------------------------------------------------------------------------
# (g) 滾動視窗：要數「交易列」時，不可以用日曆天
# ---------------------------------------------------------------------------


def mean_of_3_rows_correct(close: pd.Series) -> pd.Series:
    return close.rolling(3).mean()


def mean_of_3_calendar_days_wrong(close: pd.Series) -> pd.Series:
    """三個日曆天的視窗：週末與休市日之後，視窗裡只剩一兩列。"""
    return close.rolling("3D").mean()


def check_three_row_mean_matches_hand_values(func: Callable[[pd.Series], pd.Series]) -> None:
    """三列平均必須等於手算的逐列預期值；行事曆含週末與休市日。"""
    # 手算：(10+13+13)/3 = 12、(13+13+16)/3 = 14、(13+16+13)/3 = 14、(16+13+19)/3 = 16、……
    expected = pd.Series(
        [np.nan, np.nan, 12.0, 14.0, 14.0, 16.0, 16.0, 19.0, 18.0, 21.0, 20.0],
        index=LOCAL_DATES,
        name="close",
    )
    pd.testing.assert_series_equal(func(make_close()), expected, check_exact=False, rtol=RTOL, obj="three-row mean")


def test_g_window_check_passes_on_row_window():
    check_three_row_mean_matches_hand_values(mean_of_3_rows_correct)


def test_g_window_check_detects_calendar_day_window():
    wrong = mean_of_3_calendar_days_wrong(make_close())
    # 3/11 是週一：三個日曆天內只有它自己一列，結果是 19 而不是 16，而且不會變成 NaN。
    assert wrong.loc["2024-03-11"] == 19.0
    with pytest.raises(AssertionError, match="three-row mean values are different"):
        check_three_row_mean_matches_hand_values(mean_of_3_calendar_days_wrong)


# ---------------------------------------------------------------------------
# (h) 海外前一交易日：兩邊休市日不同時，本地交易日該對到哪一個海外交易日
# ---------------------------------------------------------------------------


@pytest.fixture
def overseas_sessions() -> pd.DatetimeIndex:
    """虛構的海外交易日：3/8 休市；本地休市的 3/13、3/14 照常交易。"""
    return pd.to_datetime(
        [
            "2024-03-01", "2024-03-04", "2024-03-05", "2024-03-06", "2024-03-07",
            "2024-03-11", "2024-03-12", "2024-03-13", "2024-03-14", "2024-03-15",
            "2024-03-18", "2024-03-19", "2024-03-20",
        ]
    )


def previous_session_correct(local_dates: pd.DatetimeIndex, sessions: pd.DatetimeIndex) -> pd.Series:
    """本例的規則：取日期早於本地交易日的最後一個海外交易日；沒有更早的就給 NaT。"""
    position = sessions.searchsorted(local_dates, side="left") - 1
    mapped = sessions[np.clip(position, 0, None)].where(position >= 0)
    return pd.Series(mapped, index=local_dates, name="overseas_date")


def previous_session_same_day_leaky(local_dates: pd.DatetimeIndex, sessions: pd.DatetimeIndex) -> pd.Series:
    """收了同一天：本地 3/4 對到海外 3/4，而那一場在本例的決策時點還沒收盤。"""
    position = sessions.searchsorted(local_dates, side="right") - 1
    mapped = sessions[np.clip(position, 0, None)].where(position >= 0)
    return pd.Series(mapped, index=local_dates, name="overseas_date")


def previous_session_minus_one_weekday_wrong(
    local_dates: pd.DatetimeIndex, sessions: pd.DatetimeIndex
) -> pd.Series:
    """直接減一個平日，沒有查海外行事曆：3/11 會對到海外休市的 3/8。"""
    return pd.Series(local_dates - pd.offsets.BDay(1), index=local_dates, name="overseas_date")


def previous_session_exact_lookup_wrong(local_dates: pd.DatetimeIndex, sessions: pd.DatetimeIndex) -> pd.Series:
    """只查前一個平日是不是海外交易日，不是就給 NaT：3/11 的前一個平日 3/8 海外休市，結果變成 NaT。"""
    wanted = local_dates - pd.offsets.BDay(1)
    return pd.Series(wanted.where(wanted.isin(sessions)), index=local_dates, name="overseas_date")


def check_previous_session_mapping(mapping: pd.Series, sessions: pd.DatetimeIndex) -> None:
    """對到的必須是真的海外交易日、日期早於本地交易日，而且中間沒有漏掉更近的一場。

    NaT 只在沒有更早的海外交易日時才是對的。
    """
    for local_date, mapped in mapping.items():
        if pd.isna(mapped):
            earlier = sessions[sessions < local_date]
            if not earlier.empty:
                raise AssertionError(
                    f"missing session: {local_date.date()} maps to NaT, but overseas session "
                    f"{earlier[-1].date()} is earlier"
                )
            continue
        if mapped not in sessions:
            raise AssertionError(f"wrong session: {mapped.date()} is not an overseas session")
        if mapped >= local_date:
            raise AssertionError(f"look-ahead: {local_date.date()} maps to {mapped.date()}, which is not earlier")
        skipped = sessions[(sessions > mapped) & (sessions < local_date)]
        if not skipped.empty:
            raise AssertionError(f"stale session: {local_date.date()} skips overseas session {skipped[-1].date()}")


def test_h_mapping_check_passes_and_mapping_matches_hand_values(overseas_sessions):
    mapping = previous_session_correct(LOCAL_DATES, overseas_sessions)
    check_previous_session_mapping(mapping, overseas_sessions)
    # 手推：3/11 往回跳過海外休市的 3/8，對到 3/7；本地連休後的 3/15 對到 3/14。
    expected = pd.Series(
        pd.to_datetime(
            [
                "2024-03-01", "2024-03-04", "2024-03-05", "2024-03-06", "2024-03-07",
                "2024-03-07", "2024-03-11", "2024-03-14",
                "2024-03-15", "2024-03-18", "2024-03-19",
            ]
        ),
        index=LOCAL_DATES,
        name="overseas_date",
    )
    pd.testing.assert_series_equal(mapping, expected)


def test_h_no_earlier_session_gives_nat(overseas_sessions):
    # 位置算出 -1 時若直接拿去取值，會取到「最後一個」海外交易日；這裡確認得到的是 NaT。
    mapping = previous_session_correct(pd.to_datetime(["2024-03-01"]), overseas_sessions)
    assert mapping.isna().tolist() == [True]


def test_h_mapping_check_passes_on_nat_when_no_earlier_session(overseas_sessions):
    # 手推：3/1 之前沒有海外交易日，正確答案就是 NaT；3/4 對到 3/1。檢查不可以把這個 NaT 判成錯。
    mapping = previous_session_correct(pd.to_datetime(["2024-03-01", "2024-03-04"]), overseas_sessions)
    assert mapping.isna().tolist() == [True, False]
    check_previous_session_mapping(mapping, overseas_sessions)


@pytest.mark.parametrize(
    ("bad_mapping", "reason"),
    [
        pytest.param(
            previous_session_same_day_leaky,
            "look-ahead: 2024-03-04 maps to 2024-03-04, which is not earlier",
            id="same_day",
        ),
        pytest.param(
            previous_session_minus_one_weekday_wrong,
            "wrong session: 2024-03-08 is not an overseas session",
            id="minus_one_weekday",
        ),
        # 手推：3/11 的前一個平日 3/8 海外休市，查不到就給了 NaT；但更早的 3/7 是海外交易日。
        pytest.param(
            previous_session_exact_lookup_wrong,
            "missing session: 2024-03-11 maps to NaT, but overseas session 2024-03-07 is earlier",
            id="exact_lookup",
        ),
    ],
)
def test_h_mapping_check_detects_bad_mappings(bad_mapping, reason, overseas_sessions):
    with pytest.raises(AssertionError, match=reason + "$"):
        check_previous_session_mapping(bad_mapping(LOCAL_DATES, overseas_sessions), overseas_sessions)


def test_h_mapping_check_detects_stale_session(overseas_sessions):
    # 本地 3/13、3/14 休市時海外照常交易；3/15 若仍對到連休前的 3/12，就漏掉了 3/13、3/14。
    mapping = previous_session_correct(LOCAL_DATES, overseas_sessions)
    mapping.loc["2024-03-15"] = pd.Timestamp("2024-03-12")
    with pytest.raises(AssertionError, match="stale session: 2024-03-15 skips overseas session 2024-03-14$"):
        check_previous_session_mapping(mapping, overseas_sessions)
