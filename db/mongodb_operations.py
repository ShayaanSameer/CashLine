import sqlite3
from .database import get_db_path

# list all the contents of the table
def get_all_categories():
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, color FROM categories")
    results = cursor.fetchall()
    connection.close()
    return results

def get_category_by_id(category_id):
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, color FROM categories WHERE id=?", (category_id,))
    result = cursor.fetchone()
    connection.close()
    return result

def get_category_by_name(name):
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, color FROM categories WHERE name=?", (name,))
    result = cursor.fetchone()
    connection.close()
    return result

def add_category_if_missing(name, color='#607D8B'):
    if not get_category_by_name(name):
        connection = sqlite3.connect(get_db_path())
        cursor = connection.cursor()
        cursor.execute("INSERT INTO categories (name, color) VALUES (?, ?)", (name, color))
        connection.commit()
        connection.close()

def get_all_budgets():
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("SELECT id, category, limit_amount, month, year FROM budget")
    results = cursor.fetchall()
    # Attach color from categories
    budgets_with_color = []
    for row in results:
        cat = get_category_by_name(row[1])
        color = cat[2] if cat else '#607D8B'
        budgets_with_color.append((row[0], row[1], row[2], row[3], row[4], color))
    connection.close()
    return budgets_with_color

def add_to_budget(category, limit_amount, month, year):
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("INSERT INTO budget (category, limit_amount, month, year) VALUES (?, ?, ?, ?)",
                   (category, float(limit_amount), month, int(year)))
    connection.commit()
    connection.close()

def update_budget_by_id(budget_id, category, limit_amount, month, year):
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("UPDATE budget SET category=?, limit_amount=?, month=?, year=? WHERE id=?",
                   (category, float(limit_amount), month, int(year), budget_id))
    connection.commit()
    connection.close()

def delete_budget_by_id(budget_id):
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("DELETE FROM budget WHERE id=?", (budget_id,))
    connection.commit()
    connection.close()

'''
    Functions for the expenses table
'''

# list all the expenses
def get_all_expenses():
    """Retrieve all expense records from the database.

    Executes a SELECT query to fetch all rows from the expenses table, returning each as a tuple.

    Returns:
        list of tuple: Each tuple contains (amount, category, description, date, currency).

    Raises:
        sqlite3.DatabaseError: If a database error occurs during the query.
    """
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("SELECT id, amount, category, description, date, currency FROM expenses")
    results = cursor.fetchall()
    connection.close()
    return results

# add to expenses
def add_expense(amount, category, description, date, currency):
    """Add a new expense record to the database.

    Inserts a new row into the expenses table with the specified details.

    Args:
        amount (float): Expense amount.
        category (str): Expense category.
        description (str): Description of the expense.
        date (str): Date of the expense (YYYY-MM-DD).
        currency (str): Currency code.

    Raises:
        sqlite3.DatabaseError: If a database error occurs during the insert.
    """
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("INSERT INTO expenses (amount, category, description, date, currency) VALUES (?, ?, ?, ?, ?)",
                   (float(amount), category, description, date, currency))
    connection.commit()
    connection.close()

# delete from expense
def delete_expense(description, date):
    """Delete an expense record from the database by description and date.

    Removes a row from the expenses table matching the given description and date.

    Args:
        description (str): Description of the expense.
        date (str): Date of the expense (YYYY-MM-DD).

    Raises:
        sqlite3.DatabaseError: If a database error occurs during the deletion.
    """
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("DELETE FROM expenses WHERE description=? AND date=?",
                   (description, date))
    connection.commit()
    connection.close()

def get_income(month, year):
    """Retrieve the income for a given month and year from the database."""
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("SELECT amount FROM income WHERE month=? AND year=?", (month, int(year)))
    result = cursor.fetchone()
    connection.close()
    return result[0] if result else None

def set_income(month, year, amount):
    """Set or update the income for a given month and year in the database."""
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("DELETE FROM income WHERE month=? AND year=?", (month, int(year)))
    cursor.execute("INSERT INTO income (month, year, amount) VALUES (?, ?, ?)", (month, int(year), float(amount)))
    connection.commit()
    connection.close()

def delete_income(month, year):
    """Delete the income record for a given month and year from the database."""
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("DELETE FROM income WHERE month=? AND year=?", (month, int(year)))
    connection.commit()
    connection.close()

def get_expense_by_id(expense_id):
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("SELECT id, amount, category, description, date, currency FROM expenses WHERE id=?", (expense_id,))
    result = cursor.fetchone()
    connection.close()
    return result

def update_expense_by_id(expense_id, amount, category, description, date, currency):
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("UPDATE expenses SET amount=?, category=?, description=?, date=?, currency=? WHERE id=?",
                   (float(amount), category, description, date, currency, expense_id))
    connection.commit()
    connection.close()

def delete_expense_by_id(expense_id):
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    connection.commit()
    connection.close()

'''
Functions for the goals table
'''
def get_all_goals():
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, target_amount, saved_amount, deadline FROM goals")
    results = cursor.fetchall()
    connection.close()
    return results

def get_goal_by_id(goal_id):
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, target_amount, saved_amount, deadline FROM goals WHERE id=?", (goal_id,))
    result = cursor.fetchone()
    connection.close()
    return result

def add_goal(name, target_amount, saved_amount, deadline):
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("INSERT INTO goals (name, target_amount, saved_amount, deadline) VALUES (?, ?, ?, ?)",
                   (name, float(target_amount), float(saved_amount), deadline))
    connection.commit()
    connection.close()

def update_goal(goal_id, name, target_amount, saved_amount, deadline):
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("UPDATE goals SET name=?, target_amount=?, saved_amount=?, deadline=? WHERE id=?",
                   (name, float(target_amount), float(saved_amount), deadline, goal_id))
    connection.commit()
    connection.close()

def delete_goal(goal_id):
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("DELETE FROM goals WHERE id=?", (goal_id,))
    connection.commit()
    connection.close()

def get_recent_expenses(limit=5):
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("SELECT amount, category, description, date, currency FROM expenses ORDER BY date DESC LIMIT ?", (limit,))
    results = cursor.fetchall()
    connection.close()
    return results 