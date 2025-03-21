from flask import Flask, request, jsonify
import pickle
import numpy as np
import sqlite3
import pandas as pd

# Load trained model
with open("fraud_model.pkl", "rb") as model_file:
    model = pickle.load(model_file)

# Initialize Flask app
app = Flask(__name__)

# Connect to SQLite database
def get_rules():
    conn = sqlite3.connect("rules.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT condition, action, enabled FROM fraud_rules WHERE enabled=1")
    rules = cursor.fetchall()
    conn.close()
    return rules

# Define channel mapping globally
channel_mapping = {"online": 0, "mobile": 1, "pos": 2}

# Function to safely get values with default fallback
def safe_get(data, key, default=0):
    return data.get(key, default)

# Fraud Detection API
@app.route("/detect_fraud", methods=["POST"])
def detect_fraud():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid JSON request"}), 400

        transaction_id = safe_get(data, "transaction_id", "unknown")

        # Encoding categorical values (same as training)
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

        # Fetch rules dynamically
        rules = get_rules()
        for condition, action, enabled in rules:
            if enabled:
                try:
                    # Safely evaluate condition using only allowed data fields
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

        # If no rule flags fraud, use AI model
        score = model.predict_proba(features)[0][1]
        is_fraud = bool(score > 0.5)
        source = "model"
        reason = "Predicted by AI"

        # Store transaction in DB
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

# Batch Fraud Detection API
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

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True, port=5001)
