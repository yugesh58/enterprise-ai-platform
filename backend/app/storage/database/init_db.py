
import sqlite3
from pathlib import Path

# Create database path
DB_PATH = Path(__file__).parent / "company.db"

# Connect to SQLite
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# =========================
# CREATE TABLES
# =========================

# Employees Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS employees (
    employee_id INTEGER PRIMARY KEY,
    employee_name TEXT,
    department_id INTEGER,
    salary INTEGER,
    joining_date TEXT
)
""")

# Departments Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS departments (
    department_id INTEGER PRIMARY KEY,
    department_name TEXT,
    location TEXT
)
""")

# Sales Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY,
    employee_id INTEGER,
    product_name TEXT,
    amount INTEGER,
    sale_date TEXT
)
""")

# =========================
# INSERT SAMPLE DATA
# =========================

# Departments
cursor.executemany(
    "INSERT INTO departments VALUES (?, ?, ?)",
    [
        (1, "Engineering", "Bangalore"),
        (2, "HR", "Mumbai"),
        (3, "Finance", "Delhi"),
        (4, "Sales", "Pune")
    ]
)

# Employees
cursor.executemany(
    "INSERT INTO employees VALUES (?, ?, ?, ?, ?)",
    [
        (101, "Yugesh", 1, 120000, "2023-01-15"),
        (102, "Rahul", 2, 80000, "2022-06-10"),
        (103, "Sneha", 3, 95000, "2021-03-22"),
        (104, "Anita", 4, 110000, "2020-11-01"),
        (105, "Karan", 1, 130000, "2019-07-18")
    ]
)

# Sales
cursor.executemany(
    "INSERT INTO sales VALUES (?, ?, ?, ?, ?)",
    [
        (1, 104, "Laptop", 150000, "2025-01-10"),
        (2, 104, "Monitor", 50000, "2025-01-15"),
        (3, 101, "Cloud Service", 200000, "2025-02-01"),
        (4, 105, "AI Platform", 350000, "2025-02-20")
    ]
)

# Commit changes
conn.commit()

print("Database and tables created successfully!")
print(f"Database location: {DB_PATH}")

# Close connection
conn.close()
