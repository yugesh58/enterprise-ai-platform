# app/services/test_router.py

from app.services.router import route_question

questions = [
    "Show all employees",
    "What does the leave policy say?",
    "Which region has highest profit?",
    "Show sales by country",
    "Create a chart of revenue by region"
]

for q in questions:
    print(f"\nQuestion: {q}")
    print(route_question(q))