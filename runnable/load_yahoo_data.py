import os
from functools import reduce

import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine

symbols = {
    "oil": "CL=F",
    "al": "ALI=F",
    "gas": "NG=F",
    "copper": "HG=F",
    "gazprom": "OGZPY",
    "rusal": "RUAL.ME",
    "rub": "RUB=X",
}


def load_symbol(name, sym):
    t = yf.Ticker(sym)
    hist = t.history(period="3y")
    hist[name] = (hist["High"] + hist["Low"]) / 2

    return hist[[name]]


if __name__ == "__main__":
    list_of_frames = []

    for name, sym in symbols.items():
        list_of_frames.append(load_symbol(name, sym))

    df = reduce(lambda a, b: a.join(b), list_of_frames)
    df = df.fillna(method="ffill").reset_index(drop=False)
    df.to_sql("yahoo_finance_2", conn, schema="public", if_exists="replace")
