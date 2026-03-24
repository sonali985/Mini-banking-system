import sqlite3
import hashlib
from datetime import datetime

# ---------------- DATABASE ----------------
conn = sqlite3.connect("smartbank.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    balance REAL DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    locked INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    type TEXT,
    amount REAL,
    time TEXT
)
""")

conn.commit()

# ---------------- UTIL ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def log_transaction(user, t_type, amount):
    time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    cursor.execute("INSERT INTO transactions (username, type, amount, time) VALUES (?, ?, ?, ?)",
                   (user, t_type, amount, time))
    conn.commit()

def get_balance(user):
    cursor.execute("SELECT balance FROM users WHERE username=?", (user,))
    return cursor.fetchone()[0]

# ---------------- AUTH ----------------
def register():
    print("\n--- REGISTER ---")
    user = input("Username: ")
    pwd = hash_password(input("Password: "))

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pwd))
        conn.commit()
        print("Account created successfully!\n")
    except:
        print("Username already exists!\n")

def login():
    print("\n--- LOGIN ---")
    user = input("Username: ")
    pwd = hash_password(input("Password: "))

    cursor.execute("SELECT password, attempts, locked FROM users WHERE username=?", (user,))
    data = cursor.fetchone()

    if not data:
        print("User not found!\n")
        return

    db_pwd, attempts, locked = data

    if locked:
        print("Account is locked!\n")
        return

    if pwd == db_pwd:
        cursor.execute("UPDATE users SET attempts=0 WHERE username=?", (user,))
        conn.commit()
        print("Login successful!\n")
        dashboard(user)
    else:
        attempts += 1
        if attempts >= 3:
            cursor.execute("UPDATE users SET attempts=?, locked=1 WHERE username=?", (attempts, user))
            print("Account locked after 3 failed attempts!\n")
        else:
            cursor.execute("UPDATE users SET attempts=? WHERE username=?", (attempts, user))
            print(f"Wrong password! Attempts left: {3 - attempts}\n")
        conn.commit()

# ---------------- BANKING ----------------
def deposit(user):
    try:
        amt = float(input("Enter amount: ₹"))
        if amt <= 0:
            print("Enter valid amount!\n")
            return
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amt, user))
        conn.commit()
        log_transaction(user, "Deposit", amt)
        print("Deposit successful!\n")
    except:
        print("Invalid input!\n")

def withdraw(user):
    try:
        amt = float(input("Enter amount: ₹"))
        bal = get_balance(user)

        if amt <= 0:
            print("Enter valid amount!\n")
        elif amt > bal:
            print("Insufficient balance!\n")
        else:
            cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amt, user))
            conn.commit()
            log_transaction(user, "Withdraw", amt)
            print("Withdrawal successful!\n")
    except:
        print("Invalid input!\n")

def transfer(user):
    try:
        receiver = input("Receiver username: ")
        amt = float(input("Amount: ₹"))
        bal = get_balance(user)

        cursor.execute("SELECT * FROM users WHERE username=?", (receiver,))
        if not cursor.fetchone():
            print("Receiver not found!\n")
            return

        if amt <= 0:
            print("Enter valid amount!\n")
        elif amt > bal:
            print("Insufficient balance!\n")
        else:
            cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amt, user))
            cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amt, receiver))
            conn.commit()

            log_transaction(user, f"Sent to {receiver}", amt)
            log_transaction(receiver, f"Received from {user}", amt)

            print("Transfer successful!\n")
    except:
        print("Invalid input!\n")

def show_balance(user):
    print(f"Current Balance: ₹{get_balance(user)}\n")

def history(user):
    print("\n--- TRANSACTION HISTORY ---")
    cursor.execute("SELECT type, amount, time FROM transactions WHERE username=?", (user,))
    rows = cursor.fetchall()

    if not rows:
        print("No transactions found.\n")
        return

    for row in rows:
        print(f"{row[2]} | {row[0]} | ₹{row[1]}")
    print()

# ---------------- ADMIN ----------------
def admin():
    print("\n--- ADMIN PANEL ---")
    cursor.execute("SELECT username, balance, locked FROM users")
    users = cursor.fetchall()

    if not users:
        print("No users found.\n")
        return

    for u in users:
        status = "Locked" if u[2] else "Active"
        print(f"{u[0]} | ₹{u[1]} | {status}")
    print()

# ---------------- DASHBOARD ----------------
def dashboard(user):
    while True:
        print(f"--- DASHBOARD ({user}) ---")
        print("1. Check Balance")
        print("2. Deposit")
        print("3. Withdraw")
        print("4. Transfer")
        print("5. Transaction History")
        print("6. Logout")

        ch = input("Choose: ")

        if ch == "1":
            show_balance(user)
        elif ch == "2":
            deposit(user)
        elif ch == "3":
            withdraw(user)
        elif ch == "4":
            transfer(user)
        elif ch == "5":
            history(user)
        elif ch == "6":
            break
        else:
            print("Invalid choice!\n")

# ---------------- MAIN ----------------
def main():
    while True:
        print("====== SMARTBANK PRO ======")
        print("1. Register")
        print("2. Login")
        print("3. Admin Panel")
        print("4. Exit")

        ch = input("Select option: ")

        if ch == "1":
            register()
        elif ch == "2":
            login()
        elif ch == "3":
            admin()
        elif ch == "4":
            print("Thank you for using SmartBank Pro!")
            break
        else:
            print("Invalid choice!\n")

if __name__ == "__main__":
    main()