import sqlite3
import pandas as pd

# Connect to the SQLite database
db_path = "fraud_detection.db"  # Ensure this path is correct
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if transactions table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions';")
table_exists = cursor.fetchone()

if not table_exists:
    print("❌ The 'transactions' table does not exist in the database.")
else:
    # Fetch all transactions
    query = "SELECT * FROM transactions;"
    transactions = cursor.execute(query).fetchall()
    
    if transactions:
        # Get column names
        cursor.execute("PRAGMA table_info(transactions);")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Convert to pandas DataFrame for better readability
        df = pd.DataFrame(transactions, columns=columns)
        
        print(f"✅ Total Transactions: {len(df)}\n")
        print(df.to_string(index=False))  # Print table without row index
    else:
        print("📂 No transactions found in the database.")

# Close the connection
conn.close()
