"""Train/test split, metrics and simple baselines."""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.config import FORECAST_HORIZON_QUARTERS


def time_split(df, test_start="2024Q3", horizon=FORECAST_HORIZON_QUARTERS):
    """Split by time instead of at random.

    Test  = forecasts made from `test_start` onwards (rents of the most recent year).
    Train = forecasts whose answer (the rent 4 quarters later) was already known before `test_start`.
    """
    test_start = pd.Period(test_start, freq="Q")
    train = df[df["quarter"] + horizon < test_start].reset_index(drop=True)
    test = df[df["quarter"] >= test_start].reset_index(drop=True)
    print(f"train: {len(train):,} rows ({train['quarter'].min()} -> {train['quarter'].max()}) | "
          f"test: {len(test):,} rows ({test['quarter'].min()} -> {test['quarter'].max()})")
    return train, test


def regression_scores(y_true, y_pred, name):
    """MAE, RMSE (both in €/m²) and R² in one row, so models are easy to compare."""
    return {
        "model": name,
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": np.sqrt(mean_squared_error(y_true, y_pred)),
        "R2": r2_score(y_true, y_pred),
    }


def top_20_hit_rate(test, predicted_growth):
    """Of the municipalities the model ranks in the top 20% for growth (in each quarter), the share that
    really ended in the top 20%. This is the precision of the "top 20%" class. A random guess gets ~20%."""
    df = test[["quarter", "target_growth_next_year"]].copy()
    df["predicted"] = np.asarray(predicted_growth)
    real_top = df.groupby("quarter")["target_growth_next_year"].rank(ascending=False, pct=True) <= 0.2
    predicted_top = df.groupby("quarter")["predicted"].rank(ascending=False, pct=True) <= 0.2
    return float((real_top & predicted_top).sum() / predicted_top.sum())
