from typing import Any

import pandas as pd
from typing_extensions import TypedDict


class AnalystState(TypedDict):
    question: str

    dataframe: pd.DataFrame

    pandas_code: str

    result: Any

    chart_path: str | None

    summary: str
