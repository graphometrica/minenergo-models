from typing import Any, Dict, Optional

import fbprophet as fbp
import numpy as np
import pandas as pd


def avg_col_vals(current_data: pd.DataFrame) -> Dict[str, float]:
    last_ = pd.to_datetime(
        current_data["ds"].max().to_datetime64() - np.timedelta64(14, "D")
    )
    res = {}
    for col in ["oil", "al", "gas", "copper", "gazprom", "rusal", "rub"]:
        res[col] = current_data.loc[current_data["ds"] > last_, col].mean()

    return res


def create_fcst_df(current_data: pd.DataFrame) -> pd.DataFrame:
    daterange = pd.date_range(
        start=current_data["ds"].max(), periods=30 * 24, freq="1h"
    )
    columns = {"ds": daterange}
    last_ = pd.to_datetime(
        current_data["ds"].max().to_datetime64() - np.timedelta64(14, "D")
    )
    for col in ["oil", "al", "gas", "copper", "gazprom", "rusal", "rub"]:
        columns[col] = (
            [current_data.loc[current_data["ds"] > last_, col].mean()] * 30 * 24
        )

    return pd.DataFrame(columns)


def fit_model(data: pd.DataFrame) -> fbp.Prophet:
    model = fbp.Prophet()
    model.add_country_holidays(country_name="Russia")
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
    model: fbp.Prophet, data: pd.DataFrame, features: Optional[Dict[str, Optional[Any]]]
) -> pd.DataFrame:
    fcst_data = create_fcst_df(data)
    if features:
        for f, val in features.items():
            if val:
                fcst_data[f] = val

    return model.predict(fcst_data)
