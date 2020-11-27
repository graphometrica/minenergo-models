from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from scripts import create_plots, fit_model, make_forecast

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_data():
    history = pd.read_csv("data/yahoo_history.csv", parse_dates=["Date"])
    consumption = pd.read_csv("data/test_data.csv", parse_dates=["date"])

    consumption["Date"] = pd.to_datetime(consumption["date"].dt.date)
    cols = [
        "date",
        "IBR_ActualConsumption",
        "oil",
        "al",
        "gas",
        "copper",
        "gazprom",
        "rusal",
        "rub",
    ]
    XX = pd.merge(consumption, history, on="Date", how="left")[cols]
    return XX


@app.get("/forecast", response_model=JSONResponse)
async def make_foreacst(
    oil: Optional[float] = None,
    al: Optional[float] = None,
    gas: Optional[float] = None,
    copper: Optional[float] = None,
    gazprom: Optional[float] = None,
    rusal: Optional[float] = None,
    rub: Optional[float] = None,
):
    try:
        data = get_data()
        model = fit_model(data)
        fcst = make_forecast(
            model=model,
            data=data,
            features=dict(
                oil=oil,
                al=al,
                gas=gas,
                copper=copper,
                gazprom=gazprom,
                rusal=rusal,
                rub=rub,
            ),
        )
        plots = create_plots(model, fcst)
        fcst["ds"] = fcst["ds"].astype(str)

        return JSONResponse(
            content=json.dumps(
                dict(
                    forecast_plot=plots["forecast"],
                    trend_plot=plots["trend"],
                    daily_trend=plots["daily_part"],
                    data=fcst.to_dict(orient="index"),
                )
            ),
            headers={
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json",
                "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE",
                "Access-Control-Allow-Headers": "Origin, X-Requested-With, Accept, Authorization, Content-Type, Access-Control-Allow-Headers, Access-Control-Request-Method, Content-length, Access-Control-Allow-Origin",
            },
        )
    except Exception as e:
        return HTTPException(404, detail=str(e.with_traceback(None)))
