def load_data_node(state):

    df = dataset_service.load_dataset(
        state["dataset_id"]
    )

    return {
        "dataframe": df
    }