from app.services.chart_generator import generate_chart


def chart_node(state):
    chart_path = generate_chart(
        state["result"]
    )

    return {
        "chart_path": chart_path,
    }