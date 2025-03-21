import sqlite3

# Connect to the database
conn = sqlite3.connect("fraud_detection.db")
cursor = conn.cursor()

# Manually insert a transaction
transaction_data = (
    "txn_manual_001",  # Transaction ID
    1500.75,  # Transaction Amount
    1,  # is_fraud (1 for fraud, 0 for non-fraud)
    "manual",  # fraud_source
    "Manually added transaction",  # fraud_reason
    0.85  # fraud_score (1.0 for high risk, 0.0 for low risk)
)

cursor.execute("""
    INSERT INTO transactions 
    (transaction_id, transaction_amount, is_fraud, fraud_source, fraud_reason, fraud_score) 
    VALUES (?, ?, ?, ?, ?, ?)
""", transaction_data)

# Commit and close the database connection
conn.commit()
conn.close()

print("✅ Manually added transaction:", transaction_data[0])
