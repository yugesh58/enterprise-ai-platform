import random
from datetime import date, timedelta

import psycopg

DATABASE_URL = (
    "postgresql://enterprise_user:"
    "enterprise_password@localhost:5432/enterprise_ai"
)

random.seed(42)

DEPARTMENTS = [
    ("Engineering", "Bangalore"),
    ("Human Resources", "Mumbai"),
    ("Finance", "Delhi"),
    ("Sales", "Pune"),
    ("Marketing", "Hyderabad"),
    ("Operations", "Chennai"),
    ("Product", "Bangalore"),
    ("Data Science", "Bangalore"),
    ("IT", "Hyderabad"),
    ("Legal", "Delhi"),
    ("Procurement", "Mumbai"),
    ("Customer Success", "Pune"),
    ("Research", "Bangalore"),
    ("Security", "Hyderabad"),
    ("Analytics", "Chennai"),
    ("Quality Assurance", "Pune"),
    ("Business Development", "Mumbai"),
    ("Administration", "Delhi"),
    ("Supply Chain", "Chennai"),
    ("Strategy", "Bangalore"),
]

FIRST_NAMES = [
    "Aarav", "Aditi", "Akash", "Amit", "Ananya",
    "Anil", "Anita", "Arjun", "Deepak", "Divya",
    "Isha", "Karan", "Kavya", "Manish", "Meera",
    "Mohit", "Neha", "Nikhil", "Pooja", "Rahul",
    "Ravi", "Riya", "Rohit", "Sneha", "Sonia",
    "Vikas", "Vivek", "Yugesh", "Priya", "Varun",
]

LAST_NAMES = [
    "Sharma", "Verma", "Singh", "Kumar", "Gupta",
    "Patel", "Mehta", "Joshi", "Bhat", "Reddy",
    "Nair", "Iyer", "Kapoor", "Malhotra", "Rao",
    "Bansal", "Chopra", "Mishra", "Saxena", "Das",
]

PRODUCTS = [
    "Laptop",
    "Monitor",
    "Keyboard",
    "Mouse",
    "Server",
    "Cloud Subscription",
    "Security Software",
    "Analytics Platform",
    "CRM License",
    "ERP License",
    "AI Platform",
    "Database License",
    "Mobile Device",
    "Tablet",
    "Networking Equipment",
    "Storage",
    "Consulting Service",
    "Support Contract",
    "Training",
    "Professional Services",
]

BATCH_SIZE = 5000

EMPLOYEE_COUNT = 50_000
CUSTOMER_COUNT = 50_000
PRODUCT_COUNT = 1_000
SALES_COUNT = 500_000
PROJECT_COUNT = 5_000


def random_date(start_year=2018, end_year=2026):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)

    days = (end - start).days

    return start + timedelta(
        days=random.randint(0, days)
    )


def create_tables(conn):

    with conn.cursor() as cur:

        cur.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                department_id INTEGER PRIMARY KEY,
                department_name TEXT NOT NULL,
                location TEXT
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                employee_id INTEGER PRIMARY KEY,
                employee_name TEXT NOT NULL,
                department_id INTEGER NOT NULL
                    REFERENCES departments(department_id),
                salary INTEGER NOT NULL,
                joining_date DATE NOT NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY,
                customer_name TEXT NOT NULL,
                city TEXT,
                created_date DATE NOT NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                price INTEGER NOT NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                sale_id BIGINT PRIMARY KEY,
                employee_id INTEGER NOT NULL
                    REFERENCES employees(employee_id),
                customer_id INTEGER NOT NULL
                    REFERENCES customers(customer_id),
                product_id INTEGER NOT NULL
                    REFERENCES products(product_id),
                amount INTEGER NOT NULL,
                sale_date DATE NOT NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id INTEGER PRIMARY KEY,
                project_name TEXT NOT NULL,
                department_id INTEGER NOT NULL
                    REFERENCES departments(department_id),
                employee_id INTEGER
                    REFERENCES employees(employee_id),
                budget INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE
            );
        """)

    conn.commit()


def seed_departments(conn):

    with conn.cursor() as cur:

        cur.executemany(
            """
            INSERT INTO departments
                (department_id, department_name, location)
            VALUES (%s, %s, %s)
            ON CONFLICT (department_id)
            DO UPDATE SET
                department_name = EXCLUDED.department_name,
                location = EXCLUDED.location
            """,
            [
                (i + 1, name, location)
                for i, (name, location)
                in enumerate(DEPARTMENTS)
            ],
        )

    conn.commit()


def seed_employees(conn):

    print(f"Generating {EMPLOYEE_COUNT:,} employees...")

    rows = []

    for employee_id in range(1, EMPLOYEE_COUNT + 1):

        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)

        name = f"{first} {last}"

        department_id = random.randint(
            1,
            len(DEPARTMENTS),
        )

        salary = random.randint(
            40_000,
            250_000,
        )

        joining_date = random_date(
            2015,
            2026,
        )

        rows.append(
            (
                employee_id,
                name,
                department_id,
                salary,
                joining_date,
            )
        )

        if len(rows) >= BATCH_SIZE:

            with conn.cursor() as cur:

                cur.executemany(
                    """
                    INSERT INTO employees
                        (
                            employee_id,
                            employee_name,
                            department_id,
                            salary,
                            joining_date
                        )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (employee_id) DO NOTHING
                    """,
                    rows,
                )

            conn.commit()
            rows.clear()

    if rows:

        with conn.cursor() as cur:

            cur.executemany(
                """
                INSERT INTO employees
                    (
                        employee_id,
                        employee_name,
                        department_id,
                        salary,
                        joining_date
                    )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (employee_id) DO NOTHING
                """,
                rows,
            )

        conn.commit()


def seed_customers(conn):

    print(f"Generating {CUSTOMER_COUNT:,} customers...")

    cities = [
        "Bangalore",
        "Mumbai",
        "Delhi",
        "Pune",
        "Hyderabad",
        "Chennai",
        "Kolkata",
        "Ahmedabad",
        "Jaipur",
        "Chandigarh",
    ]

    rows = []

    for customer_id in range(1, CUSTOMER_COUNT + 1):

        name = (
            f"{random.choice(FIRST_NAMES)} "
            f"{random.choice(LAST_NAMES)}"
        )

        rows.append(
            (
                customer_id,
                name,
                random.choice(cities),
                random_date(2018, 2026),
            )
        )

        if len(rows) >= BATCH_SIZE:

            with conn.cursor() as cur:

                cur.executemany(
                    """
                    INSERT INTO customers
                        (
                            customer_id,
                            customer_name,
                            city,
                            created_date
                        )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (customer_id) DO NOTHING
                    """,
                    rows,
                )

            conn.commit()
            rows.clear()

    if rows:

        with conn.cursor() as cur:

            cur.executemany(
                """
                INSERT INTO customers
                    (
                        customer_id,
                        customer_name,
                        city,
                        created_date
                    )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (customer_id) DO NOTHING
                """,
                rows,
            )

        conn.commit()


def seed_products(conn):

    print(f"Generating {PRODUCT_COUNT:,} products...")

    categories = [
        "Hardware",
        "Software",
        "Cloud",
        "Security",
        "Services",
        "Analytics",
    ]

    rows = []

    for product_id in range(1, PRODUCT_COUNT + 1):

        base_product = random.choice(PRODUCTS)

        product_name = (
            f"{base_product} {product_id}"
        )

        category = random.choice(categories)

        price = random.randint(
            500,
            500_000,
        )

        rows.append(
            (
                product_id,
                product_name,
                category,
                price,
            )
        )

    with conn.cursor() as cur:

        cur.executemany(
            """
            INSERT INTO products
                (
                    product_id,
                    product_name,
                    category,
                    price
                )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (product_id) DO NOTHING
            """,
            rows,
        )

    conn.commit()


def seed_sales(conn):

    print(f"Generating {SALES_COUNT:,} sales...")

    rows = []

    for sale_id in range(1, SALES_COUNT + 1):

        employee_id = random.randint(
            1,
            EMPLOYEE_COUNT,
        )

        customer_id = random.randint(
            1,
            CUSTOMER_COUNT,
        )

        product_id = random.randint(
            1,
            PRODUCT_COUNT,
        )

        amount = random.randint(
            500,
            1_000_000,
        )

        sale_date = random_date(
            2020,
            2026,
        )

        rows.append(
            (
                sale_id,
                employee_id,
                customer_id,
                product_id,
                amount,
                sale_date,
            )
        )

        if len(rows) >= BATCH_SIZE:

            with conn.cursor() as cur:

                cur.executemany(
                    """
                    INSERT INTO sales
                        (
                            sale_id,
                            employee_id,
                            customer_id,
                            product_id,
                            amount,
                            sale_date
                        )
                    VALUES
                        (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (sale_id) DO NOTHING
                    """,
                    rows,
                )

            conn.commit()

            print(
                f"  Sales inserted: "
                f"{sale_id:,}/{SALES_COUNT:,}"
            )

            rows.clear()

    if rows:

        with conn.cursor() as cur:

            cur.executemany(
                """
                INSERT INTO sales
                    (
                        sale_id,
                        employee_id,
                        customer_id,
                        product_id,
                        amount,
                        sale_date
                    )
                VALUES
                    (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (sale_id) DO NOTHING
                """,
                rows,
            )

        conn.commit()


def seed_projects(conn):

    print(f"Generating {PROJECT_COUNT:,} projects...")

    rows = []

    for project_id in range(
        1,
        PROJECT_COUNT + 1,
    ):

        department_id = random.randint(
            1,
            len(DEPARTMENTS),
        )

        employee_id = random.randint(
            1,
            EMPLOYEE_COUNT,
        )

        start_date = random_date(
            2020,
            2026,
        )

        end_date = (
            start_date
            + timedelta(
                days=random.randint(
                    30,
                    900,
                )
            )
        )

        rows.append(
            (
                project_id,
                f"Project {project_id}",
                department_id,
                employee_id,
                random.randint(
                    100_000,
                    10_000_000,
                ),
                start_date,
                end_date,
            )
        )

    with conn.cursor() as cur:

        cur.executemany(
            """
            INSERT INTO projects
                (
                    project_id,
                    project_name,
                    department_id,
                    employee_id,
                    budget,
                    start_date,
                    end_date
                )
            VALUES
                (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (project_id) DO NOTHING
            """,
            rows,
        )

    conn.commit()


def create_indexes(conn):

    print("Creating indexes...")

    indexes = [
        """
        CREATE INDEX IF NOT EXISTS
        idx_employees_department
        ON employees(department_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS
        idx_employees_salary
        ON employees(salary)
        """,
        """
        CREATE INDEX IF NOT EXISTS
        idx_employees_joining_date
        ON employees(joining_date)
        """,
        """
        CREATE INDEX IF NOT EXISTS
        idx_sales_employee
        ON sales(employee_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS
        idx_sales_customer
        ON sales(customer_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS
        idx_sales_product
        ON sales(product_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS
        idx_sales_date
        ON sales(sale_date)
        """,
        """
        CREATE INDEX IF NOT EXISTS
        idx_projects_department
        ON projects(department_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS
        idx_projects_employee
        ON projects(employee_id)
        """,
    ]

    with conn.cursor() as cur:

        for index in indexes:
            cur.execute(index)

    conn.commit()


def main():

    print("=" * 80)
    print("ENTERPRISE AI PLATFORM - DATABASE SEED")
    print("=" * 80)

    with psycopg.connect(DATABASE_URL) as conn:

        create_tables(conn)

        seed_departments(conn)

        seed_employees(conn)

        seed_customers(conn)

        seed_products(conn)

        seed_sales(conn)

        seed_projects(conn)

        create_indexes(conn)

    print()
    print("=" * 80)
    print("DATABASE SEED COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()