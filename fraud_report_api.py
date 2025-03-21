from flask import Flask, request, jsonify
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fraud_reporting_api")

# Initialize Flask app
app = Flask(__name__)

# Database connection function
def get_db_connection():
    return sqlite3.connect("fraud_detection.db", check_same_thread=False, timeout=10)

# Ensure fraud reporting table exists
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fraud_reporting (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE,
            reporting_entity_id TEXT,
            fraud_details TEXT,
            is_fraud_reported INTEGER DEFAULT 1,
            report_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info("✅ Fraud reporting database initialized successfully")

# Fraud Reporting API
@app.route("/fraud_report", methods=["POST"])
def fraud_report():
    try:
        data = request.json
        if not data or "transaction_id" not in data or "reporting_entity_id" not in data or "fraud_details" not in data:
            return jsonify({"error": "Missing required fields: transaction_id, reporting_entity_id, fraud_details"}), 400

        transaction_id = data["transaction_id"]
        reporting_entity_id = data["reporting_entity_id"]
        fraud_details = data["fraud_details"]

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert report into database
        cursor.execute("""
            INSERT INTO fraud_reporting (transaction_id, reporting_entity_id, fraud_details)
            VALUES (?, ?, ?)
        """, (transaction_id, reporting_entity_id, fraud_details))
        conn.commit()
        conn.close()
        logger.info(f"✅ Fraud report recorded for transaction {transaction_id}")

        return jsonify({
            "transaction_id": transaction_id,
            "reporting_acknowledged": True,
            "failure_code": 0
        })
    except sqlite3.IntegrityError:
        return jsonify({
            "transaction_id": transaction_id,
            "reporting_acknowledged": False,
            "failure_code": 1,
            "error": "Transaction already reported"
        }), 409
    except Exception as e:
        logger.error(f"❌ Error in fraud_report API: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Initialize database
init_db()

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True, port=5002)
