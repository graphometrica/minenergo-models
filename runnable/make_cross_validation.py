import os

import fbprohet as fbp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from fbprophet.diagnostics import cross_validation
from sqlalchemy import create_engine

if __name__ == "__main__":
    bd_password = os.environ["POSTGRES_PASSWORD"]
    conn = create_engine(
        f"postgresql://graph_main:{bd_password}@35.226.152.97:5432/minenergo"
    )
    data = pd.read_sql("select * from minenergo.joined", con=conn)

    def make_cv(region, horizon="30 days", period="30 days"):
        model = fbp.Prophet()
        model.add_country_holidays(country_name="Russia")
        model.add_regressor("oil")
        model.add_regressor("al")
        model.add_regressor("gas")
        model.add_regressor("copper")
        model.add_regressor("gazprom")
        model.add_regressor("rusal")
        model.add_regressor("rub")
        model.add_regressor("temp")

        model.fit(data.query(f"region == {region}"))
        cv_data = cross_validation(
            model=model, horizon="30 days", parallel="processes", period="30 days"
        )
        f = plt.figure(figsize=(18, 6))
        ax = f.add_subplot()
        model.plot(cv_data, ax=ax)
        ax.set_xlabel("Date")
        ax.set_ylabel("Consumption")
        mape = np.mean(np.abs(cv_data["y"] - cv_data["yhat"]) / cv_data["y"]) * 100
        msg = f"Cross-validataion results:\nPeriod: {period}\nHorizon: {horizon}\nMAPE: {mape:.2f}%\n"
        ax.text(cv_data.iloc[-3000]["ds"], cv_data["yhat"].max() * 0.95, msg)
        f.savefig(f"plots/region_{region}.png", dpi=300)
        plt.close(f)

    for region in data["region"].unique():
        make_cv(region)
