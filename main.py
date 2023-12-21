import sqlite3
from faker import Faker
import random
import os
import datetime
import csv

fake = Faker()

db_file = "coffee_shop.db"


if not os.path.exists(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE Customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone_number TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE Employees (
            employee_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('clerk', 'delivery', 'manager'))
        );
    """)

    cursor.execute("""
        CREATE TABLE Orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            description TEXT NOT NULL,
            order_date DATE NOT NULL,
            total_amount REAL NOT NULL,
            completion_status BOOLEAN NOT NULL DEFAULT 0,
            assigned_employee_id INTEGER,
            FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
            FOREIGN KEY (assigned_employee_id) REFERENCES Employees(employee_id)
        );
    """)

    for _ in range(400):
        cursor.execute(
            "INSERT INTO Customers (name, address, phone_number) VALUES (?, ?, ?)",
            (fake.name(), fake.address(), fake.phone_number())
        )

    employees = [
        ("John", "password1", "clerk"),
        ("Bob", "password2", "delivery"),
        ("Velma", "password3", "manager")
    ]
    for employee in employees:
        cursor.execute(
            "INSERT INTO Employees (username, password, role) VALUES (?, ?, ?)",
            employee
        )

    for _ in range(1000):
        completion_status = random.choice([0, 1])
        assigned_employee_id = random.randint(2, 3) if completion_status else None
        cursor.execute(
            "INSERT INTO Orders (customer_id, description, order_date, total_amount, completion_status, assigned_employee_id) VALUES (?, ?, ?, ?, ?, ?)",
            (
                random.randint(1, 400),
                fake.text(),
                fake.date_between(start_date="-30d", end_date="today"),
                random.randint(1, 100),
                completion_status,
                assigned_employee_id
            )
        )

    conn.commit()
    conn.close()

def login_user():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    while True:
        print("LOGIN")
        username = input("Username: ")
        password = input("Password: ")
        cursor.execute("SELECT * FROM Employees WHERE username=? AND password=?", (username, password))
        user_data = cursor.fetchone()

        if user_data:
            print(f"\nWelcome {user_data[1]}!")
            menu(user_data, cursor, conn)
        else:
            print("Invalid credentials. Please try again.")

    conn.close()

def menu(user_data, cursor, conn):
    role = user_data[3]

    if role == 'clerk':
        while True:
            print("\nCRM MENU CLERK")
            print("1. Add order")
            print("2. Add order (new customer)")
            print("3. Assign order to delivery")
            print("4. View pending orders")
            print("5. Exit")
            user_input = input("Enter choice (1-5): ")

            if user_input == '1':
                add_order(cursor, conn, user_data)
            elif user_input == '2':
                add_order_new_customer(cursor, conn, user_data)
            elif user_input == '3':
                assign_order_to_delivery(cursor, conn)
            elif user_input == '4':
                view_completed_orders(cursor)
            elif user_input == '5':
                break
            else:
                print("Invalid choice. Please try again.")

    elif role == 'delivery':
        while True:
            print("\nCRM MENU DELIVERY")
            print("1. Complete order")
            print("2. Exit")
            delivery_input = input("Enter choice (1-2): ")

            if delivery_input == '1':
                change_delivery_status(cursor, conn)
            elif delivery_input == '2':
                break
            else:
                print("Invalid choice. Please try again.")

    elif role == 'manager':
        while True:
            print("\nCRM MENU MANAGER")
            print("1. Customer profile")
            print("2. Orders on day")
            print("3. Pending orders")
            print("4. View Customers (export to csv)")
            print("5. View Employees (export to csv)")
            print("6. View Orders (export to csv)")
            print("7. Exit")
            manager_input = input("Enter choice (1-7): ")

            if manager_input == '1':
                count_orders_for_customer(cursor)
            elif manager_input == '2':
                count_orders(cursor)
            elif manager_input == '3':
                count_pending_orders(cursor)
            elif manager_input == '4':
                export_customers_to_csv(cursor, filename="customers.csv")
            elif manager_input == '5':
                export_employees_to_csv(cursor, filename="employees.csv")
            elif manager_input == '6':
                export_orders_to_csv(cursor, filename="orders.csv")
            elif manager_input == '7':
                break
            else:
                print("Invalid choice. Please try again.")
    conn.close()

def add_order(cursor, conn, user_data):
    customer_id = input("Enter customer ID (1-50): ")
    description = input("Enter order description: ")
    order_date = input("Enter order date (YYYY-MM-DD): ")
    total_amount = float(input("Enter total amount: "))
    assigned_employee_id = user_data[0]
    completion_status = 0

    cursor.execute("""
        INSERT INTO Orders (customer_id, description, order_date, total_amount, completion_status, assigned_employee_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (customer_id, description, order_date, total_amount, completion_status, assigned_employee_id))

    conn.commit()
    print("Order added successfully.")

def add_order_new_customer(cursor, conn, user_data):
    description = input("Enter order description: ")
    order_date = input("Enter order date (YYYY-MM-DD): ")
    total_amount = float(input("Enter total amount: "))

    name = input("Enter customer name: ")
    address = input("Enter customer address: ")
    phone_number = input("Enter customer phone number: ")

    cursor.execute("""
        INSERT INTO Customers (name, address, phone_number)
        VALUES (?, ?, ?)
    """, (name, address, phone_number))
    conn.commit()

    cursor.execute("SELECT last_insert_rowid();")
    customer_id = cursor.fetchone()[0]

    assigned_employee_id = user_data[0]
    completion_status = 0
    cursor.execute("""
        INSERT INTO Orders (customer_id, description, order_date, total_amount, completion_status, assigned_employee_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (customer_id, description, order_date, total_amount, completion_status, assigned_employee_id))

    conn.commit()
    print("Order added successfully.")

def assign_order_to_delivery(cursor, conn):
    order_id = input("Enter the order ID you want to assign to delivery: ")

    cursor.execute("SELECT * FROM Orders WHERE order_id=?", (order_id,))
    order_data = cursor.fetchone()

    if order_data:
        print("\nOrder Details:")
        print(f"Order ID: {order_data[0]}")
        print(f"Customer ID: {order_data[1]}")
        print(f"Description: {order_data[2]}")
        print(f"Order Date: {order_data[3]}")
        print(f"Total Amount: {order_data[4]}")
        print(f"Completion Status: {order_data[5]}")
        print(f"Assigned Employee ID: {order_data[6]}")

        assigned_employee_id = input("Enter the ID of the delivery person (or leave blank to unassign): ")

        if assigned_employee_id == "":
            assigned_employee_id = 'null'
        else:
            pass
        cursor.execute("UPDATE Orders SET assigned_employee_id=? WHERE order_id=?", (assigned_employee_id, order_id))
        conn.commit()

        print("Order assignment updated successfully.")
    else:
        print(f"Order with ID {order_id} not found.")

def view_completed_orders(cursor):
    cursor.execute("SELECT * FROM Orders WHERE completion_status=1")
    completed_orders = cursor.fetchall()

    if completed_orders:
        print("\nCompleted Orders:")
        for order in completed_orders:
            print(f"Order ID: {order[0]}")
            print(f"Customer ID: {order[1]}")
            print(f"Description: {order[2]}")
            print(f"Order Date: {order[3]}")
            print(f"Total Amount: {order[4]}")
            print(f"Assigned Employee ID: {order[6]}")
            print("---")
    else:
        print("No completed orders found.")

def change_delivery_status(cursor, conn):
    order_id = input("Enter the order ID to change completion status: ")

    cursor.execute("SELECT * FROM Orders WHERE order_id=?", (order_id,))
    order_data = cursor.fetchone()

    if order_data:
        print("\nOrder Details:")
        print(f"Order ID: {order_data[0]}")
        print(f"Customer ID: {order_data[1]}")
        print(f"Description: {order_data[2]}")
        print(f"Order Date: {order_data[3]}")
        print(f"Total Amount: {order_data[4]}")
        print(f"Completion Status: {order_data[5]}")
        print(f"Assigned Employee ID: {order_data[6]}")

        if order_data[5] == 0:
            print("This order is already complete.")
        else:
            confirmation = input("Do you want to change the completion status to 0? (y/n): ").lower()

            if confirmation == 'y':
                cursor.execute("UPDATE Orders SET completion_status=0 WHERE order_id=?", (order_id,))
                conn.commit()
                print("Completion status updated successfully.")
            else:
                print("Completion status not changed.")
    else:
        print(f"Order with ID {order_id} not found.")

def count_orders_for_customer(cursor):
    customer_id = input("Enter the ID of the customer: ")

    cursor.execute("SELECT * FROM Customers WHERE customer_id=?", (customer_id,))
    customer_data = cursor.fetchone()

    if customer_data:
        cursor.execute("SELECT COUNT(*) FROM Orders WHERE customer_id=?", (customer_id,))
        order_count = cursor.fetchone()[0]

        print("\nCustomer Details:")
        print(f"Customer ID: {customer_data[0]}")
        print(f"Customer Name: {customer_data[1]}")
        print(f"Address: {customer_data[2]}")
        print(f"Phone Number: {customer_data[3]}")
        print(f"Number of Orders: {order_count}")
    else:
        print(f"Customer with ID {customer_id} not found.")

def count_orders(cursor):
    date_str = input("Enter the date (YYYY-MM-DD): ")

    try:
        order_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return

    cursor.execute("SELECT COUNT(*) FROM Orders WHERE order_date=?", (order_date,))
    order_count = cursor.fetchone()[0]

    print(f"\nOrders on {order_date}: {order_count}")


def count_pending_orders(cursor):
    cursor.execute("SELECT COUNT(*) FROM Orders WHERE completion_status = 0")
    pending_order_count = cursor.fetchone()[0]

    print(f"\nPending Orders: {pending_order_count}")

def export_customers_to_csv(cursor, filename="customers.csv"):
    cursor.execute("SELECT * FROM Customers")
    customer_data = cursor.fetchall()

    header = ["customer_id", "name", "address", "phone_number"]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(customer_data)

    print(f"\nData exported to {filename}")

import csv

def export_employees_to_csv(cursor, filename="employees.csv"):
    cursor.execute("SELECT * FROM Employees")
    employee_data = cursor.fetchall()

    header = ["employee_id", "username", "password", "role"]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(employee_data)

    print(f"\nData exported to {filename}")

def export_orders_to_csv(cursor, filename="orders.csv"):
    cursor.execute("SELECT * FROM Orders")
    orders_data = cursor.fetchall()

    header = ["order_id", "customer_id", "description", "order_date", "total_amount", "completion_status", "assigned_employee_id"]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(orders_data)

    print(f"\nData exported to {filename}")


while True:
    login_user()