from app.services.router import route_question
from app.agents.agent_dispatcher import dispatch_agent

question="show all the employees"

router_agent=route_question(question)

result=dispatch_agent(router_agent,question)

print(router_agent)
print("\n")
print(result)