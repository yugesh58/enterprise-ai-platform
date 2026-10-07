import pytest

from app.agents.sql_agent import SQLAgent
from app.schemas.agent_request import AgentRequest


@pytest.fixture
def sql_agent():
    return SQLAgent()


def execute_query(agent, question, conversation_id):
    request = AgentRequest(
        question=question,
        attributes={
            "conversation_id": conversation_id,
        },
    )

    return agent.execute(request)


def assert_metrics(response):
    required_metrics = [
        "schema_retrieval_ms",
        "sql_generation_ms",
        "sql_validation_ms",
        "sql_execution_ms",
        "summarization_ms",
        "total_latency_ms",
    ]

    for metric in required_metrics:
        assert metric in response.data
        assert response.data[metric] >= 0


def test_top_5_highest_paid_employees(sql_agent):
    response = execute_query(
        sql_agent,
        "What are the top 5 highest paid employees?",
        "integration-top-employees",
    )

    assert response.answer
    assert len(response.data["result"]) == 5

    salaries = [
        row["salary"]
        for row in response.data["result"]
    ]

    assert salaries == sorted(
        salaries,
        reverse=True,
    )

    assert_metrics(response)


def test_product_sales_join(sql_agent):
    response = execute_query(
        sql_agent,
        "What are the top 5 products by total sales amount?",
        "integration-product-sales",
    )

    assert response.answer
    assert len(response.data["result"]) == 5

    assert_metrics(response)


def test_department_sales_join(sql_agent):
    response = execute_query(
        sql_agent,
        "Which departments generated the highest total sales?",
        "integration-department-sales",
    )

    assert response.answer
    assert len(response.data["result"]) >= 1

    row = response.data["result"][0]

    assert "department_name" in row
    assert "total_sales" in row

    assert_metrics(response)


def test_no_matching_records(sql_agent):
    response = execute_query(
        sql_agent,
        "What is the salary of an employee named DefinitelyNotARealEmployee999?",
        "integration-no-results",
    )

    assert response.answer == "No matching records were found."

    assert response.data["result"] == []

    assert_metrics(response)


def test_ambiguous_employee(sql_agent):
    response = execute_query(
        sql_agent,
        "What is the salary of Ravi Kumar?",
        "integration-ambiguous",
    )

    assert response.data["result"]

    if len(response.data["result"]) > 1:
        assert "ambiguous" in response.answer.lower()

    assert_metrics(response)


def test_multi_turn_conversation(sql_agent):
    conversation_id = "integration-multi-turn"

    first_response = execute_query(
        sql_agent,
        "What is the salary of Ravi Kumar?",
        conversation_id,
    )

    assert first_response.answer
    assert first_response.data["result"]

    second_response = execute_query(
        sql_agent,
        "Which department does he work in?",
        conversation_id,
    )

    assert second_response.answer
    assert second_response.data["result"]

    assert_metrics(second_response)
