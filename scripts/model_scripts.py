import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import fbprophet as fbp
import numpy as np
import pandas as pd


def avg_col_vals(current_data: pd.DataFrame) -> Dict[str, float]:
    last_ = pd.to_datetime(
        current_data["ds"].max().to_datetime64() - np.timedelta64(14, "D")
    )
    res = {}
    for col in ["oil", "al", "gas", "copper", "gazprom", "rusal", "rub", "temp"]:
        res[col] = current_data.loc[current_data["ds"] > last_, col].mean()

    return res


def smooth_const_val(current: float, next_one: float) -> pd.Series:
    coeff_ = np.linspace(0, 1, 30 * 24)
    return current * (1 - coeff_) + next_one * coeff_


def create_fcst_df(current_data: pd.DataFrame) -> pd.DataFrame:
    daterange = pd.date_range(
        start=current_data["ds"].max(), periods=30 * 24, freq="1h"
    )
    columns = {"ds": daterange}
    last_ = pd.to_datetime(
        current_data["ds"].max().to_datetime64() - np.timedelta64(14, "D")
    )

    tmp_ = current_data.loc[current_data["ds"] > last_]
    last_row_ = tmp_.tail(1)
    for col in ["oil", "al", "gas", "copper", "gazprom", "rusal", "rub", "temp"]:
        columns[col] = smooth_const_val(last_row_[col].iloc[0], tmp_[col].mean())

    return pd.DataFrame(columns)


def fit_model(data: pd.DataFrame) -> fbp.Prophet:
    model = fbp.Prophet()
    model.add_country_holidays(country_name="Russia")
    model.add_seasonality(name="monthly", period=30.5, fourier_order=5)
    model.add_seasonality(name="quarterly", period=91.25, fourier_order=5)
    model.add_regressor("temp")
    model.add_regressor("oil")
    model.add_regressor("al")
    model.add_regressor("gas")
    model.add_regressor("copper")
    model.add_regressor("gazprom")
    model.add_regressor("rusal")
    model.add_regressor("rub")
    model.fit(data)

    return model


def make_forecast(
    model: fbp.Prophet,
    data: pd.DataFrame,
    fcst_data: pd.DataFrame,
    region: int,
    features: Optional[Dict[str, Optional[Any]]],
) -> pd.DataFrame:
    last_row_ = data.loc[data["ds"] == data["ds"].max()]
    dt = fcst_data.copy()
    if features:
        for f, val in features.items():
            if val:
                dt[f] = smooth_const_val(last_row_[f].iloc[0], val)

    return model.predict(dt)
