from app.agents.agent_dispatcher import dispatch_agent
from app.services.router import route_question

question = "show all employees"

agent = route_question(question)

result = dispatch_agent(
    agent,
    question
)

print(result)