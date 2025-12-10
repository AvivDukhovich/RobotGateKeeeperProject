import sqlite3

DB_NAME = "test.db"

def create_connection():
    """Creates a connection object to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    return conn

def create_table():
    """Creates a simple table called 'users'."""
    conn = create_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER
    )
    """)

    conn.commit()
    conn.close()

def insert_user(name, age):
    """Inserts a new row into the users table."""
    conn = create_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO users (name, age) VALUES (?, ?)", (name, age))

    conn.commit()
    conn.close()

def get_all_users():
    """Reads all rows in the users table."""
    conn = create_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()

    conn.close()
    return rows

def update_user_age(user_id, new_age):
    """Updates a user's age."""
    conn = create_connection()
    cur = conn.cursor()

    cur.execute("UPDATE users SET age = ? WHERE id = ?", (new_age, user_id))

    conn.commit()
    conn.close()

def delete_user(user_id):
    """Deletes a user by ID."""
    conn = create_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))

    conn.commit()
    conn.close()

# --------------------------
# TEST AREA (you can edit!)
# --------------------------

if __name__ == "__main__":
    create_table()

    insert_user("Alice", 20)
    insert_user("Bob", 25)
    insert_user("Charlie", 30)

    print("Users after insert:")
    print(get_all_users())

    update_user_age(2, 99)
    print("Users after update:")
    print(get_all_users())

    delete_user(1)
    print("Users after delete:")
    print(get_all_users())
