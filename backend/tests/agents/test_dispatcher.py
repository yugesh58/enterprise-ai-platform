# app/agents/test_dispatcher.py

from app.agents.agent_dispatcher import dispatch_agent

response = dispatch_agent("analyst", "Which region has highest profit?")

print(response)
