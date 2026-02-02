import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import matplotlib.pyplot as plt
from tkcalendar import DateEntry


# ---------------- DATABASE ----------------
conn = sqlite3.connect("expense.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    date TEXT,
    category TEXT,
    amount REAL,
    description TEXT
)
""")
conn.commit()
cur.execute("""
CREATE TABLE IF NOT EXISTS user_settings (
    username TEXT PRIMARY KEY,
    budget REAL
)
""")
conn.commit()


# ---------------- GLOBAL VARIABLES ----------------
THEME = {}
username = ""
monthly_budget = 0

# ---------------- CORE FUNCTIONS ----------------
def add_expense():
    d = date_entry.get()
    c = category_box.get()
    a = amount_entry.get()
    desc = desc_entry.get()

    if d == "" or c == "" or a == "":
        messagebox.showerror("Error", "Please fill all required fields")
        return

    cur.execute(
        "INSERT INTO expenses VALUES (NULL, ?, ?, ?, ?, ?)",
        (username, d, c, float(a), desc)
    )
    conn.commit()

    date_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)
    desc_entry.delete(0, tk.END)

    update_total()
    check_budget()
    messagebox.showinfo("Success", "Expense Added Successfully!")

def get_total():
    cur.execute(
        "SELECT SUM(amount) FROM expenses WHERE username = ?",
        (username,)
    )
    total = cur.fetchone()[0]
    return total if total else 0

def update_total():
    total_label.config(text=f"Total this month: ₹{get_total()}")

def check_budget():
    if monthly_budget > 0 and get_total() > monthly_budget:
        messagebox.showwarning(
            "Budget Alert ⚠",
            "You have exceeded your monthly budget!"
        )

def view_expenses():
    win = tk.Toplevel(root)
    win.title("All Expenses")
    win.geometry("520x300")

    tree = ttk.Treeview(
        win,
        columns=("Date", "Category", "Amount", "Description"),
        show="headings"
    )
    tree.pack(fill=tk.BOTH, expand=True)

    for col in tree["columns"]:
        tree.heading(col, text=col)

    cur.execute(
        "SELECT date, category, amount, description FROM expenses WHERE username = ?",
        (username,)
    )
    for row in cur.fetchall():
        tree.insert("", tk.END, values=row)

def pie_chart():
    cur.execute(
        "SELECT category, SUM(amount) FROM expenses WHERE username = ? GROUP BY category",
        (username,)
    )
    data = cur.fetchall()

    if not data:
        messagebox.showinfo("Info", "No data available")
        return

    labels = [i[0] for i in data]
    values = [i[1] for i in data]

    plt.pie(values, labels=labels, autopct="%1.1f%%")
    plt.title("Category-wise Expense")
    plt.show()

def bar_chart():
    cur.execute(
        """
        SELECT strftime('%m', date), SUM(amount)
        FROM expenses WHERE username = ?
        GROUP BY strftime('%m', date)
        """,
        (username,)
    )
    data = cur.fetchall()
    if not data:
        messagebox.showinfo("Info", "No data available")
        return

    months = [d[0] for d in data]
    amounts = [d[1] for d in data]

    plt.bar(months, amounts)
    plt.xlabel("Month")
    plt.ylabel("Amount")
    plt.title("Monthly Expense Overview")
    plt.show()

# ---------------- MAIN APP ----------------
def launch_app():
    app = tk.Toplevel(root)
    app.title("Expense Tracker")
    app.geometry("450x580")
    app.configure(bg=THEME["bg"])

    tk.Label(
        app,
        text=f"Welcome, {username} 💸",
        font=("Comic Sans MS", 22, "bold"),
        bg=THEME["bg"],
        fg=THEME["title"]
    ).pack(pady=15)

#comment added

    frame = tk.Frame(app, bg=THEME["frame"])
    frame.pack(padx=20, pady=10, fill="both")

    def label(text):
        return tk.Label(
            frame,
            text=text,
            font=("Comic Sans MS", 11),
            bg=THEME["frame"]
        )

    global date_entry, category_box, amount_entry, desc_entry, total_label

    label("Select Date").pack(pady=(10, 0))
    date_entry = DateEntry(
        frame,
        width=18,
        background=THEME["button"],
        foreground="white",
        borderwidth=2,
        date_pattern="yyyy-mm-dd"
    )
    date_entry.pack(pady=5)

    label("Category").pack()
    category_box = ttk.Combobox(frame, values=[
        "Food", "Travel", "Rent",
        "Shopping", "Education",
        "Entertainment", "Others"
    ])
    category_box.current(0)
    category_box.pack(pady=5)

    label("Amount").pack()
    amount_entry = tk.Entry(frame)
    amount_entry.pack(pady=5)

    label("Description").pack()
    desc_entry = tk.Entry(frame)
    desc_entry.pack(pady=5)

    btn = {
        "font": ("Comic Sans MS", 11, "bold"),
        "width": 20,
        "bd": 0,
        "bg": THEME["button"],
        "fg": "white"
    }

    tk.Button(app, text="Add Expense", command=add_expense, **btn).pack(pady=5)
    tk.Button(app, text="View Expenses", command=view_expenses, **btn).pack(pady=5)
    tk.Button(app, text="Pie Chart", command=pie_chart, **btn).pack(pady=5)
    tk.Button(app, text="Monthly Chart", command=bar_chart, **btn).pack(pady=5)

    total_label = tk.Label(
        app,
        text=f"Total this month: ₹{get_total()}",
        font=("Comic Sans MS", 12, "bold"),
        bg=THEME["bg"]
    )
    total_label.pack(pady=10)

# ---------------- USER INPUT WINDOWS ----------------
def ask_name():
    win = tk.Toplevel(root)
    win.title("Your Name")
    win.geometry("300x180")

    def submit():
        global username
        username = entry.get()
        if username.strip() == "":
            messagebox.showerror("Error", "Enter your name")
            return
        win.destroy()
        ask_budget()


    tk.Label(
        win,
        text="Enter your name 😊",
        font=("Comic Sans MS", 14, "bold")
    ).pack(pady=15)

    entry = tk.Entry(win)
    entry.pack(pady=10)

    tk.Button(win, text="Continue", command=submit).pack(pady=10)

def ask_budget():
    global monthly_budget

    # Check if budget already exists for this user
    cur.execute(
        "SELECT budget FROM user_settings WHERE username = ?",
        (username,)
    )
    row = cur.fetchone()

    if row:
        monthly_budget = row[0]
        launch_app()
        return

    # If no budget found, ask user
    win = tk.Toplevel(root)
    win.title("Monthly Budget")
    win.geometry("300x180")

    def submit():
        global monthly_budget
        try:
            monthly_budget = float(entry.get())
        except:
            monthly_budget = 0

        # Save budget for this user
        cur.execute(
            "INSERT INTO user_settings VALUES (?, ?)",
            (username, monthly_budget)
        )
        conn.commit()

        win.destroy()
        launch_app()

    tk.Label(
        win,
        text="Set monthly budget ₹",
        font=("Comic Sans MS", 13, "bold")
    ).pack(pady=15)

    entry = tk.Entry(win)
    entry.pack(pady=10)

    tk.Button(win, text="Continue", command=submit).pack(pady=10)


# ---------------- GENDER SELECTION (ROOT) ----------------
def select_gender(g):
    global THEME
    # Hide gender selection window permanently
    root.withdraw()

    if g == "boy":
        THEME = {
            "bg": "#E3F2FD",
            "frame": "#BBDEFB",
            "button": "#2196F3",
            "title": "#0D47A1"
        }
    else:
        THEME = {
            "bg": "#FFE4E1",
            "frame": "#FFF0F5",
            "button": "#FF69B4",
            "title": "#FF1493"
        }
    ask_name()

# ---------------- ROOT WINDOW ----------------
root = tk.Tk()
root.title("Select User")
root.geometry("350x220")

tk.Label(
    root,
    text="Who is using the app?",
    font=("Comic Sans MS", 16, "bold")
).pack(pady=20)

tk.Button(
    root,
    text="Boy 💙",
    font=("Comic Sans MS", 12, "bold"),
    bg="#2196F3",
    fg="white",
    width=15,
    command=lambda: select_gender("boy")
).pack(pady=10)

tk.Button(
    root,
    text="Girl 💖",
    font=("Comic Sans MS", 12, "bold"),
    bg="#FF69B4",
    fg="white",
    width=15,
    command=lambda: select_gender("girl")
).pack(pady=5)

root.mainloop()



