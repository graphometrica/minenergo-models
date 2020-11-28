import io
from typing import Dict

import fbprophet as fbp
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def create_plots(model: fbp.Prophet, fcst: pd.DataFrame) -> Dict[str, str]:
    # Create Forecast plot
    f = plt.figure(figsize=(18, 8))
    ax = f.add_subplot()
    model.plot(fcst, ax=ax)
    ax.set_xlabel("Date")
    ax.set_ylabel("Forecast")
    bytes_ = io.StringIO()
    f.savefig(bytes_, format="svg")
    bytes_.seek(0)
    hash_trend = bytes_.buffer
    plt.close(f)

    # Trend
    f = plt.figure(figsize=(12, 8))
    ax = f.add_subplot()
    markers, caps, bars = ax.errorbar(
        x=fcst["ds"],
        y=fcst["trend"],
        yerr=np.vstack(
            [fcst["trend"] - fcst["trend_lower"], fcst["trend_upper"] - fcst["trend"]]
        ),
        fmt="-",
        label="Trend",
    )
    ax.grid()
    ax.legend()

    [bar.set_alpha(0.2) for bar in bars]
    [cap.set_alpha(0.2) for cap in caps]
    bytes_ = io.StringIO()
    f.savefig(bytes_, format="svg")
    bytes_.seek(0)
    hash_trend = bytes_.buffer
    plt.close(f)

    # Daily component
    f = plt.figure(figsize=(12, 8))
    ax = f.add_subplot()
    lower_ = pd.to_datetime(fcst["ds"].max().to_datetime64() - np.timedelta64(1, "D"))
    fcst_ = fcst[fcst["ds"] >= lower_]
    markers, caps, bars = ax.errorbar(
        x=fcst_["ds"],
        y=fcst_["daily"],
        yerr=np.vstack(
            [
                fcst_["daily"] - fcst_["daily_lower"],
                fcst_["daily_upper"] - fcst_["daily"],
            ]
        ),
        fmt="-",
        label="Daily Component",
    )
    ax.grid()
    ax.legend()
    ax.set_xlim(lower_)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H-%M"))

    [bar.set_alpha(0.2) for bar in bars]
    [cap.set_alpha(0.2) for cap in caps]
    bytes_ = io.StringIO()
    f.savefig(bytes_, format="svg")
    bytes_.seek(0)
    hash_daily = bytes_.buffer
    plt.close(f)

    # Weekly component
    f = plt.figure(figsize=(12, 8))
    ax = f.add_subplot()
    lower_ = pd.to_datetime(fcst["ds"].max().to_datetime64() - np.timedelta64(7, "D"))
    fcst_ = fcst[fcst["ds"] >= lower_]
    markers, caps, bars = ax.errorbar(
        x=fcst_["ds"],
        y=fcst_["weekly"],
        yerr=np.vstack(
            [
                fcst_["weekly"] - fcst_["weekly_lower"],
                fcst_["weekly_upper"] - fcst_["weekly"],
            ]
        ),
        fmt="-",
        label="Weekly Component",
    )
    ax.grid()
    ax.legend()
    ax.set_xlim(lower_)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%A"))

    [bar.set_alpha(0.2) for bar in bars]
    [cap.set_alpha(0.2) for cap in caps]
    bytes_ = io.StringIO()
    f.savefig(bytes_, format="svg")
    bytes_.seek(0)
    hash_weekly = bytes_.buffer
    plt.close(f)

    return dict(
        forecast=hash_forecast,
        trend=hash_trend,
        daily_part=hash_daily,
        weekly_part=hash_weekly,
    )