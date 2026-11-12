
from unittest.mock import patch

from app.workflows.sql.nodes.summarize import summarize_node


def test_empty_results_do_not_call_llm():
    state = {
        "question": "What is the salary of Ravi Kumar?",
        "result": [],
        "memory": [],
    }

    with patch(
        "app.workflows.sql.nodes.summarize.summarize_result"
    ) as mock_summarize:
        response = summarize_node(state)

    assert response["summary"] == "No matching records were found."
    mock_summarize.assert_not_called()


def test_ambiguous_results_do_not_call_llm():
    state = {
        "question": "What is the salary of Ravi Kumar?",
        "result": [
            {"employee_name": "Ravi Kumar", "salary": 100000},
            {"employee_name": "Ravi Kumar", "salary": 120000},
        ],
        "memory": [],
    }

    with patch(
        "app.workflows.sql.nodes.summarize.summarize_result"
    ) as mock_summarize:
        response = summarize_node(state)

    assert "ambiguous" in response["summary"].lower()
    mock_summarize.assert_not_called()


def test_simple_first_turn_list_uses_deterministic_formatting():
    state = {
        "question": "What are the top 5 highest paid employees?",
        "result": [
            {"employee_name": "Kavya Saxena", "salary": 250000},
            {"employee_name": "Karan Iyer", "salary": 249998},
        ],
        "memory": [],
    }

    with patch(
        "app.workflows.sql.nodes.summarize.summarize_result"
    ) as mock_summarize:
        response = summarize_node(state)

    assert "Kavya Saxena" in response["summary"]
    assert "Karan Iyer" in response["summary"]
    assert "250000" in response["summary"]
    assert "249998" in response["summary"]
    mock_summarize.assert_not_called()


def test_first_turn_deterministic_format_preserves_database_values():
    state = {
        "question": "Show the top employees by salary",
        "result": [
            {
                "employee_name": "Kavya Saxena",
                "salary": 250000,
                "department_id": 3,
            }
        ],
        "memory": [],
    }

    with patch(
        "app.workflows.sql.nodes.summarize.summarize_result"
    ) as mock_summarize:
        response = summarize_node(state)

    for value in ("Kavya Saxena", "250000", "3"):
        assert value in response["summary"]

    mock_summarize.assert_not_called()


def test_questions_with_conversation_history_use_llm():
    state = {
        "question": "Which department does he work in?",
        "result": [
            {"department_name": "Engineering"},
        ],
        "memory": [
            {
                "role": "user",
                "content": "What is the salary of Ravi Kumar?",
            },
            {
                "role": "assistant",
                "content": "Ravi Kumar earns 120000.",
            },
        ],
    }

    with patch(
        "app.workflows.sql.nodes.summarize.summarize_result",
        return_value="He works in Engineering.",
    ) as mock_summarize:
        response = summarize_node(state)

    assert response["summary"] == "He works in Engineering."
    mock_summarize.assert_called_once()


def test_complex_question_uses_llm():
    state = {
        "question": "Compare sales performance across departments.",
        "result": [
            {
                "department_name": "Engineering",
                "total_sales": 500000,
            },
            {
                "department_name": "Marketing",
                "total_sales": 300000,
            },
        ],
        "memory": [],
    }

    with patch(
        "app.workflows.sql.nodes.summarize.summarize_result",
        return_value="Sales increased across the reported departments.",
    ) as mock_summarize:
        response = summarize_node(state)

    assert response["summary"]
    mock_summarize.assert_called_once()


def test_summarization_latency_is_recorded():
    state = {
        "question": "What are the top 5 highest paid employees?",
        "result": [
            {"employee_name": "Kavya Saxena", "salary": 250000},
        ],
        "memory": [],
    }

    with patch(
        "app.workflows.sql.nodes.summarize.summarize_result"
    ):
        response = summarize_node(state)

    assert "summarization_ms" in response
    assert response["summarization_ms"] >= 0
