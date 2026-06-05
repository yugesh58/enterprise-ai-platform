from app.agents.sql_agent import sql_agent_query
from app.agents.rag_agent import rag_agent_query
from app.agents.analyst_agent import analyst_agent_query

def dispatch_agent(agent,question):
    if agent == "ANALYST_AGENT":
        return analyst_agent_query(question)
    if agent == "SQL_AGENT":
        return sql_agent_query(question)
    if agent == "RAG_AGENT":
        return rag_agent_query(question)
    
    return {
        "error":"unknown agent"
    }