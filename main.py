import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine

from scripts import avg_col_vals, create_plots, fit_model, make_forecast

bd_password = os.environ["POSTGRES_PASSWORD"]


def initial_load(con):
    return pd.read_sql("select * from minenergo.joined", con=con)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_data(region: int, con, global_df: pd.DataFrame) -> pd.DataFrame:
    now = datetime.now()
    max_dt = global_df["ds"].max().to_pydatetime()
    if (now - max_dt) / 3600 > 1:
        query_cond = now.strftime(fmt="%Y-%m-%d %H:00:00")
        new_data = pd.read_sql(
            f"select * from minenergo.joined where ds='{query_cond}'", con=con
        )
        if new_data.shape[0] > 0:
            global_df = pd.concat([GLOBAL_DF, new_data])
    return global_df.query("region == {region}")


@app.on_event("startup")
async def load_initial_data():
    con = create_engine(
        f"postgresql://graph_main:{bd_password}@35.226.152.97:5432/minenergo"
    )
    global_df = initial_load(con)
    print(f"Loaded {global_df.shape[0]} rows of data")


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
):
    try:
        data = get_data(region, con, global_df)

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
            content=dict(
                forecast_plot=plots["forecast"],
                trend_plot=plots["trend"],
                daily_trend=plots["daily_part"],
                weekly_forecast=plots["weekly_forecast"],
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
        data = get_data(region, con, global_df)

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
