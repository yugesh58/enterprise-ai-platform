import os

import matplotlib.pyplot as plt
import pandas as pd


def generate_chart(result):

    if not isinstance(result, (pd.Series, pd.DataFrame)):
        return None

    os.makedirs("app/charts", exist_ok=True)

    plt.figure(figsize=(10, 5))

    if isinstance(result, pd.Series):
        result.plot(kind="bar")
    else:
        result.plot()

    plt.tight_layout()

    chart_path = "app/charts/chart.png"

    plt.savefig(chart_path)

    plt.close()

    return chart_path
