from app.memory.conversation_memory import(get_memory, add_to_memory)

add_to_memory(
    "Show all employees",
    "Select * FROM employees"
)

print(get_memory())