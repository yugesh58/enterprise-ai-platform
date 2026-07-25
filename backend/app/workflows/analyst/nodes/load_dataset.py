import pandas as pd


def load_data_node(state):

    df = pd.read_csv("app/uploads/sales.csv")

    return {
        "dataframe": df,
    }
