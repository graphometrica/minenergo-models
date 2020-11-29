import os
import pickle
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import create_engine

from scripts import (
    avg_col_vals,
    create_fcst_df,
    create_plotly_plots,
    create_plots,
    create_svg_plots,
    fit_model,
    make_forecast,
)


class PlotType(Enum):
    FORECAST = "forecast"
    TREND = "trend"
    DAILY = "daily_part"
    WEEKLY = "weekly_part"
    MONTHLY = "monthly_part"
    QUARTERLY = "quarterly_part"


bd_password = os.environ["POSTGRES_PASSWORD"]


def initial_load():
    return pd.read_sql("select * from minenergo.joined", global_items["con"])


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

global_items = {}


def get_data(region: int, con, global_df: pd.DataFrame) -> pd.DataFrame:
    now = datetime.now()
    max_dt = global_df["ds"].max().to_pydatetime()
    if (now - max_dt).seconds / 3600 > 72:
        query_cond = now.strftime("%Y-%m-%d %H:00:00")
        new_data = pd.read_sql(
            f"select * from minenergo.joined where ds='{query_cond}'", con=con
        )
        if new_data.shape[0] > 0:
            global_items["global_df"] = pd.concat([global_df, new_data])
    return global_df.query(f"region == {region}")


@app.on_event("startup")
async def load_initial_data():
    global_items["con"] = create_engine(
        f"postgresql://graph_main:{bd_password}@35.226.152.97:5432/minenergo"
    )
    global_items["global_df"] = initial_load()
    global_items["fcst_df"] = create_fcst_df(
        global_items["global_df"].query("region == 11")
    )
    print(f"Loaded {global_items['global_df'].shape[0]} rows of data")
    print(f"Created {global_items['fcst_df'].shape[0]} rows for forecasting")


@app.options("/forecast")
async def make_options_forecast():
    return JSONResponse(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE",
            "Access-Control-Allow-Headers": "Origin, X-Requested-With, Accept, Authorization, Content-Type, Access-Control-Allow-Headers, Access-Control-Request-Method, Content-length, Access-Control-Allow-Origin",
        },
    )


@app.get("/forecast")
async def make_foreacst(
    region: int,
    oil: Optional[float] = None,
    al: Optional[float] = None,
    gas: Optional[float] = None,
    copper: Optional[float] = None,
    gazprom: Optional[float] = None,
    rusal: Optional[float] = None,
    rub: Optional[float] = None,
    temp: Optional[float] = None,
):
    try:
        data = get_data(region, global_items["con"], global_items["global_df"])

        cur_time = datetime.now()
        model_path = Path(
            f"model_{cur_time.year}_{cur_time.month}_{cur_time.day}_{region}.pickle"
        )
        if model_path.exists():
            with model_path.open("br") as file:
                model = pickle.load(file)
        else:
            model = fit_model(data)
            with model_path.open("wb") as file:
                pickle.dump(model, file)

        fcst = make_forecast(
            model=model,
            data=data,
            region=region,
            fcst_data=global_items["fcst_df"],
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
            content=dict(
                forecast_plot=plots["forecast"],
                trend_plot=plots["trend"],
                daily_trend=plots["daily_part"],
                weekly_forecast=plots["weekly_part"],
                monthly_forecast=plots["monthly_part"],
                quarterly_forecast=plots["quarterly_part"],
                data=fcst.to_dict(orient="index"),
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


@app.options("/avg_features")
async def options_average_features():
    return JSONResponse(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE",
            "Access-Control-Allow-Headers": "Origin, X-Requested-With, Accept, Authorization, Content-Type, Access-Control-Allow-Headers, Access-Control-Request-Method, Content-length, Access-Control-Allow-Origin",
        },
    )


@app.get("/avg_features")
async def average_features(region: int):
    try:
        data = get_data(region, global_items["con"], global_items["global_df"])

        return JSONResponse(
            content=avg_col_vals(data),
            headers={
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json",
                "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE",
                "Access-Control-Allow-Headers": "Origin, X-Requested-With, Accept, Authorization, Content-Type, Access-Control-Allow-Headers, Access-Control-Request-Method, Content-length, Access-Control-Allow-Origin",
            },
        )
    except Exception as e:
        return HTTPException(404, detail=str(e.with_traceback(None)))


@app.get("/forecast3", response_class=HTMLResponse)
async def make_foreacst_plotly(
    region: int,
    graph_type: PlotType,
    oil: Optional[float] = None,
    al: Optional[float] = None,
    gas: Optional[float] = None,
    copper: Optional[float] = None,
    gazprom: Optional[float] = None,
    rusal: Optional[float] = None,
    rub: Optional[float] = None,
    temp: Optional[float] = None,
):
    try:
        now = datetime.now()
        data = get_data(region, global_items["con"], global_items["global_df"])
        print(f"Data loaded in {(datetime.now() - now).seconds}")

        cur_time = datetime.now()
        model_path = Path(
            f"model_{cur_time.year}_{cur_time.month}_{cur_time.day}_{cur_time.hour}_{region}.pickle"
        )
        if model_path.exists():
            with model_path.open("br") as file:
                model = pickle.load(file)
        else:
            model = fit_model(data)
            with model_path.open("wb") as file:
                pickle.dump(model, file)
        print(f"Model loaded in {(datetime.now() - cur_time).seconds}")

        now = datetime.now()
        fcst = make_forecast(
            model=model,
            data=data,
            region=region,
            fcst_data=global_items["fcst_df"],
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
        print(f"Forecast created in {(datetime.now() - now).seconds}")

        now = datetime.now()
        plots = create_plotly_plots(model, fcst)
        print(f"Plots created in {(datetime.now() - now).seconds}")

        return plots[graph_type.value]
    except Exception as e:
        return HTTPException(404, detail=str(e.with_traceback(None)))


@app.options("/econometrics")
async def options_econometrics(reg_sys: int):
    try:
        data = get_data(region, global_items["con"], global_items["global_df"])

        return JSONResponse(
            content=avg_col_vals(data),
            headers={
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json",
                "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE",
                "Access-Control-Allow-Headers": "Origin, X-Requested-With, Accept, Authorization, Content-Type, Access-Control-Allow-Headers, Access-Control-Request-Method, Content-length, Access-Control-Allow-Origin",
            },
        )
    except Exception as e:
        return HTTPException(404, detail=str(e.with_traceback(None)))


@app.get("/econometrics", response_class=HTMLResponse)
async def econometrics(reg_sys: int):
    try:
        filepath = (
            Path(__file__)
            .paren.joinpath("resources")
            .joinpath(f"region")
            .joinpath("results.json")
        )
        with filepath.open("r", encoding="utf-8") as file:
            res = json.load(file.read())
        print(res.keys())

        return JSONResponse(
            content=res,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json",
                "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE",
                "Access-Control-Allow-Headers": "Origin, X-Requested-With, Accept, Authorization, Content-Type, Access-Control-Allow-Headers, Access-Control-Request-Method, Content-length, Access-Control-Allow-Origin",
            },
        )
    except Exception as e:
        return HTTPException(404, detail=str(e.with_traceback(None)))
