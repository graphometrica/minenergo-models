from typing import Dict

import fbprophet as fbp
import pandas as pd
from fbprophet import plot
from plotly.io import to_html


def create_plots(model: fbp.Prophet, fcst: pd.DataFrame) -> Dict[str, str]:
    forecast = plot.plot_plotly(model, fcst, xlabel="Date", ylabel="Forecast")
    trend = plot.plot_forecast_component_plotly(model, fcst, name="trend")
    daily = plot.plot_seasonality_plotly(model, fcst, name="daily")
    weekly = plot.plot_seasonality_plotly(model, fcst, name="weekly")

    return dict(
        forecast=to_html(forecast),
        trend=to_html(trend),
        daily_part=to_html(daily),
        weekly_part=to_html(weekly),
    )
