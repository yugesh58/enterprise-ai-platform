from app.storage.memory.conversation_memory import add_to_memory, get_memory

add_to_memory("Show all employees", "Select * FROM employees")

print(get_memory())
