from typing import Dict

import fbprophet as fbp
import numpy as np
import pandas as pd
from fbprophet import plot
from plotly.io import to_html


def create_plots(model: fbp.Prophet, fcst: pd.DataFrame) -> Dict[str, str]:
    forecast = plot.plot_plotly(
        model, fcst, xlabel="Date", ylabel="Forecast", figsize=(1400, 600)
    )
    trend = plot.plot_forecast_component_plotly(
        model, fcst, name="trend", figsize=(1400, 600)
    )
    lower_ = pd.to_datetime(fcst["ds"].max().to_datetime64() - np.timedelta64(1, "D"))
    daily = plot.plot_forecast_component_plotly(
        model, fcst[fcst["ds"] > lower_], name="daily", figsize=(1400, 600)
    )
    lower_ = pd.to_datetime(fcst["ds"].max().to_datetime64() - np.timedelta64(7, "D"))
    weekly = plot.plot_forecast_component_plotly(
        model, fcst[fcst["ds"] > lower_], name="weekly", figsize=(1400, 600)
    )
    lower_ = pd.to_datetime(fcst["ds"].max().to_datetime64() - np.timedelta64(30, "D"))
    monthly = plot.plot_forecast_component_plotly(
        model, fcst[fcst["ds"] > lower_], name="weekly", figsize=(1400, 600)
    )
    lower_ = pd.to_datetime(fcst["ds"].max().to_datetime64() - np.timedelta64(91, "D"))
    quarterly = plot.plot_forecast_component_plotly(
        model, fcst[fcst["ds"] > lower_], name="weekly", figsize=(1400, 600)
    )

    return dict(
        forecast=to_html(forecast),
        trend=to_html(trend),
        daily_part=to_html(daily),
        weekly_part=to_html(weekly),
        monthly_part=to_html(monthly),
        quarterly_part=to_html(quarterly),
    )
