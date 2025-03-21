import sqlite3

# Function to initialize database tables
def init_db():
    conn = sqlite3.connect("fraud_detection.db", check_same_thread=False, timeout=10)
    cursor = conn.cursor()

    # Create the transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            transaction_amount REAL,
            is_fraud INTEGER,
            fraud_source TEXT,
            fraud_reason TEXT,
            fraud_score REAL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create the fraud reports table if needed
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fraud_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT,
            transaction_amount REAL,
            is_fraud INTEGER,
            fraud_source TEXT,
            fraud_reason TEXT,
            fraud_score REAL,
            report_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

# Run this script directly to initialize the database
if __name__ == "__main__":
    init_db()
