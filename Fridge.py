import sqlite3
from datetime import datetime, timedelta

def create_connection():
    """Create or connect to the SQLite database."""
    try:
        conn = sqlite3.connect("stock_manager.db")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def initialize_db(conn):
    """Create the fridge_items table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fridge_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            quantity INTEGER,
            threshold INTEGER,
            last_updated DATE,
            daily_usage REAL
        )
    ''')
    conn.commit() 

def add_item(conn):
    """Add a new item to the database."""
    name = input("Enter item name: ")
    qty_input = input("Enter quantity: ")
    thresh_input = input("Enter threshold: ")
    try:
        quantity = int(qty_input)
        threshold = int(thresh_input)
    except ValueError:
        print("Error: Quantity and threshold must be integers.")
        return
    last_updated = datetime.now().date().isoformat()
    daily_usage = 0.0  
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO fridge_items(name, quantity, threshold, last_updated, daily_usage) VALUES (?, ?, ?, ?, ?)",
            (name, quantity, threshold, last_updated, daily_usage)
        )
        conn.commit()  
        print(f"Item '{name}' added (Qty: {quantity}, Threshold: {threshold}).")
    except sqlite3.IntegrityError:
        print("Error: Item already exists.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")

def update_item(conn):
    """Update an existing item’s quantity and/or threshold."""
    name = input("Enter item name to update: ")
    cursor = conn.cursor()
    cursor.execute("SELECT quantity, threshold, last_updated, daily_usage FROM fridge_items WHERE name=?", (name,))
    result = cursor.fetchone()
    if result is None:
        print("Item not found.")
        return
    old_quantity, old_threshold, last_updated, old_daily_usage = result
    print(f"Current: Qty={old_quantity}, Threshold={old_threshold}, Last updated={last_updated}, Daily use={old_daily_usage:.2f}")
    new_qty_input = input("New quantity (leave blank to keep): ")
    new_thresh_input = input("New threshold (leave blank to keep): ")
    try:
        new_quantity = int(new_qty_input) if new_qty_input.strip() else old_quantity
        new_threshold = int(new_thresh_input) if new_thresh_input.strip() else old_threshold
    except ValueError:
        print("Invalid input: quantities must be integers.")
        return

    
    last_date = datetime.fromisoformat(last_updated).date()
    days_passed = (datetime.now().date() - last_date).days

    
    if days_passed > 0 and new_quantity != old_quantity:
        used_amount = old_quantity - new_quantity
        daily_usage = used_amount / days_passed
    else:
        daily_usage = old_daily_usage 

    
    updated_date = datetime.now().date().isoformat()
    try:
        cursor.execute(
            "UPDATE fridge_items SET quantity=?, threshold=?, last_updated=?, daily_usage=? WHERE name=?",
            (new_quantity, new_threshold, updated_date, daily_usage, name)
        )
        conn.commit()
        print(f"Item '{name}' updated: Qty={new_quantity}, Threshold={new_threshold}, DailyUse={daily_usage:.2f}")
        
        if new_quantity < new_threshold:
            print(f"**Alert:** '{name}' is below threshold ({new_threshold}). Consider restocking!")
    except sqlite3.Error as e:
        print(f"Database error: {e}")

def delete_item(conn):
    """Delete an item from the database."""
    name = input("Enter item name to delete: ")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fridge_items WHERE name=?", (name,))
    if cursor.rowcount == 0:
        print("Item not found.")
    else:
        conn.commit()
        print(f"Item '{name}' deleted.")

def view_items(conn):
    """Display all items, flagging any below threshold."""
    cursor = conn.cursor()
    cursor.execute("SELECT name, quantity, threshold, last_updated, daily_usage FROM fridge_items")
    rows = cursor.fetchall()
    if not rows:
        print("No items in inventory.")
        return
    print("\nName       | Qty | Threshold | Last Updated | Daily Use")
    print("------------------------------------------------------")
    for name, qty, thresh, last_upd, daily in rows:
        status = " **LOW**" if qty < thresh else ""
        print(f"{name:<10} | {qty:<3} | {thresh:<9} | {last_upd} | {daily:>5.2f}{status}")

def predict_restock(conn):
    """Predict days until an item hits its threshold."""
    name = input("Enter item name for prediction: ")
    cursor = conn.cursor()
    cursor.execute("SELECT quantity, threshold, daily_usage FROM fridge_items WHERE name=?", (name,))
    result = cursor.fetchone()
    if result is None:
        print("Item not found.")
        return
    quantity, threshold, daily_usage = result
    if daily_usage <= 0:
        print("Not enough usage data to predict restock.")
        return
    days_left = (quantity - threshold) / daily_usage
    if days_left < 0:
        print(f"'{name}' is already below its threshold!")
        return
    restock_date = datetime.now().date() + timedelta(days=int(days_left))
    print(f"Estimate: ~{int(days_left)} days until '{name}' reaches threshold.")
    print(f"    (Approx restock date: {restock_date})")

def main():
    conn = create_connection()
    if not conn:
        return
    initialize_db(conn)
    while True:
        print("\nSmart Fridge Manager:")
        print("1) Add item")
        print("2) Update item")
        print("3) Delete item")
        print("4) View items")
        print("5) Predict restock date")
        print("6) Exit")
        choice = input("Choose an option (1-6): ")
        if choice == '1':
            add_item(conn)
        elif choice == '2':
            update_item(conn)
        elif choice == '3':
            delete_item(conn)
        elif choice == '4':
            view_items(conn)
        elif choice == '5':
            predict_restock(conn)
        elif choice == '6':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-6.")
    conn.close()

if __name__ == "__main__":
    main()
