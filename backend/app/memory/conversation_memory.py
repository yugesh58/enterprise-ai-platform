conversation_history=[]

def get_memory():
    return conversation_history

def add_to_memory(question,sql_query,summary):
    conversation_history.append({
        "question":question,
        "sql_query":sql_query,
        "summary":summary
    }
    )

    if len(conversation_history)>5:
        conversation_history.pop(0)