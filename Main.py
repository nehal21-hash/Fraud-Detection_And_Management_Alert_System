from flask import Flask, request, jsonify, render_template
import pickle
import numpy as np
import sqlite3
from flask_cors import CORS

# Initialize Flask app and allow cross-origin requests.
# If you prefer to use a templates folder, remove template_folder parameter and place index.html in a folder named 'templates'
app = Flask(__name__, template_folder='.')
CORS(app)

######################################
# Load Trained Model
######################################
with open("fraud_model.pkl", "rb") as model_file:
    model = pickle.load(model_file)

# Global channel mapping (used during feature encoding)
channel_mapping = {"online": 0, "mobile": 1, "pos": 2}

# Utility function to safely get a key from a dict with a default value
def safe_get(data, key, default=0):
    return data.get(key, default)

######################################
# Database Initialization Functions
######################################

def init_rules_db():
    conn = sqlite3.connect("rules.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS fraud_rules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        condition TEXT NOT NULL,
                        action TEXT NOT NULL,
                        enabled INTEGER DEFAULT 1
                     )''')
    conn.commit()
    conn.close()

def init_fraud_detection_db():
    conn = sqlite3.connect("fraud_detection.db", check_same_thread=False, timeout=10)
    cursor = conn.cursor()
    # Create transactions table
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
    # Create fraud reports table (if needed)
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
    print("✅ Fraud detection database initialized successfully!")

# Initialize both databases at startup
init_rules_db()
init_fraud_detection_db()

######################################
# Helper Function to Fetch Active Rules
######################################

def get_rules():
    conn = sqlite3.connect("rules.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT condition, action, enabled FROM fraud_rules WHERE enabled=1")
    rules = cursor.fetchall()
    conn.close()
    return rules

######################################
# Fraud Detection Endpoints
######################################

@app.route("/detect_fraud", methods=["POST"])
def detect_fraud():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid JSON request"}), 400

        transaction_id = safe_get(data, "transaction_id", "unknown")

        # Encode categorical values (e.g., transaction_channel) as done during training.
        data["transaction_channel"] = channel_mapping.get(safe_get(data, "transaction_channel"), -1)

        # Create feature vector from input data
        features = np.array([
            float(safe_get(data, "transaction_amount")), 
            int(safe_get(data, "transaction_channel")), 
            int(safe_get(data, "transaction_payment_mode_anonymous")), 
            int(safe_get(data, "payment_gateway_bank_anonymous")), 
            int(safe_get(data, "payer_browser_anonymous")), 
            int(safe_get(data, "transaction_hour")), 
            int(safe_get(data, "transaction_day")), 
            int(safe_get(data, "transaction_month"))
        ]).reshape(1, -1)

        # Check if any active fraud rule flags this transaction.
        rules = get_rules()
        for condition, action, enabled in rules:
            if enabled:
                try:
                    # Safely evaluate the condition using only the allowed fields from data.
                    if eval(condition, {"__builtins__": None}, data):
                        safe_keywords = ["safe", "approved", "all good", "verified", "trusted"]
                        is_fraud = not any(keyword in action.lower() for keyword in safe_keywords)
                        fraud_score = 1.0 if is_fraud else 0.0
                        return jsonify({
                            "transaction_id": transaction_id,
                            "is_fraud": is_fraud,
                            "fraud_source": "rule",
                            "fraud_reason": action,
                            "fraud_score": fraud_score
                        })
                except Exception as e:
                    print(f"Rule evaluation error: {e}")

        # If no rule flags fraud, use the AI model.
        score = model.predict_proba(features)[0][1]
        is_fraud = bool(score > 0.5)
        source = "model"
        reason = "Predicted by AI"

        # Store the transaction in the fraud_detection database.
        conn = sqlite3.connect("fraud_detection.db", check_same_thread=False, timeout=10)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?)",
                       (transaction_id, data["transaction_amount"], is_fraud, source, reason, round(score, 2)))
        conn.commit()
        conn.close()
        
        return jsonify({
            "transaction_id": transaction_id,
            "is_fraud": is_fraud,
            "fraud_source": source,
            "fraud_reason": reason,
            "fraud_score": round(score, 2)
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/detect_fraud_batch", methods=["POST"])
def detect_fraud_batch():
    try:
        transactions = request.json.get("transactions", [])
        results = []
        rules = get_rules()
        
        for data in transactions:
            transaction_id = safe_get(data, "transaction_id", "unknown")
            data["transaction_channel"] = channel_mapping.get(safe_get(data, "transaction_channel"), -1)

            features = np.array([
                float(safe_get(data, "transaction_amount")), 
                int(safe_get(data, "transaction_channel")), 
                int(safe_get(data, "transaction_payment_mode_anonymous")), 
                int(safe_get(data, "payment_gateway_bank_anonymous")), 
                int(safe_get(data, "payer_browser_anonymous")), 
                int(safe_get(data, "transaction_hour")), 
                int(safe_get(data, "transaction_day")), 
                int(safe_get(data, "transaction_month"))
            ]).reshape(1, -1)

            fraud_detected = False
            for condition, action, enabled in rules:
                if enabled:
                    try:
                        if eval(condition, {"__builtins__": None}, data):
                            safe_keywords = ["safe", "approved", "all good", "verified", "trusted"]
                            is_fraud = not any(keyword in action.lower() for keyword in safe_keywords)
                            fraud_score = 1.0 if is_fraud else 0.0
                            results.append({
                                "transaction_id": transaction_id,
                                "is_fraud": is_fraud,
                                "fraud_source": "rule",
                                "fraud_reason": action,
                                "fraud_score": fraud_score
                            })
                            fraud_detected = True
                            break
                    except Exception as e:
                        print(f"Rule evaluation error: {e}")

            if not fraud_detected:
                score = model.predict_proba(features)[0][1]
                is_fraud = bool(score > 0.5)
                results.append({
                    "transaction_id": transaction_id,
                    "is_fraud": is_fraud,
                    "fraud_source": "model",
                    "fraud_reason": "Predicted by AI",
                    "fraud_score": round(score, 2)
                })
        
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)})

######################################
# Rule Management Endpoints
######################################

@app.route("/rules", methods=["GET"])
def get_all_rules():
    conn = sqlite3.connect("rules.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fraud_rules")
    rules = [{"id": row[0], "condition": row[1], "action": row[2], "enabled": bool(row[3])} for row in cursor.fetchall()]
    conn.close()
    return jsonify(rules)

@app.route("/rules", methods=["POST"])
def add_rule():
    data = request.json
    conn = sqlite3.connect("rules.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO fraud_rules (condition, action, enabled) VALUES (?, ?, ?)",
                   (data["condition"], data["action"], int(data.get("enabled", 1))))
    conn.commit()
    conn.close()
    return jsonify({"message": "Rule added successfully"}), 201

@app.route("/rules/<int:rule_id>", methods=["PUT"])
def update_rule(rule_id):
    data = request.json
    conn = sqlite3.connect("rules.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE fraud_rules SET condition=?, action=?, enabled=? WHERE id=?",
                   (data["condition"], data["action"], int(data["enabled"]), rule_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Rule updated successfully"})

@app.route("/rules/<int:rule_id>", methods=["DELETE"])
def delete_rule(rule_id):
    conn = sqlite3.connect("rules.db")
    cursor = conn.cursor()

    # Delete the selected rule
    cursor.execute("DELETE FROM fraud_rules WHERE id=?", (rule_id,))
    conn.commit()

    # Retrieve remaining rules sorted by ID
    cursor.execute("SELECT * FROM fraud_rules ORDER BY id")
    rules = cursor.fetchall()

    # Reset the table and re-insert with new sequential IDs
    cursor.execute("DELETE FROM fraud_rules")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='fraud_rules'")
    for index, rule in enumerate(rules, start=1):
        cursor.execute("INSERT INTO fraud_rules (id, condition, action, enabled) VALUES (?, ?, ?, ?)", 
                       (index, rule[1], rule[2], rule[3]))
    conn.commit()
    conn.close()
    return jsonify({"message": "Rule deleted and IDs reordered successfully"})

######################################
# Frontend Endpoint
######################################

@app.route("/")
def index():
    return render_template("index.html")

######################################
# Run the Flask Application
######################################

if __name__ == "__main__":
    app.run(debug=True, port=5000)
