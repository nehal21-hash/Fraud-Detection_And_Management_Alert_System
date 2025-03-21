from flask import Flask, request, jsonify, render_template
import sqlite3
from flask_cors import CORS

# Initialize Flask app, set template folder to root
app = Flask(__name__, template_folder='.')
CORS(app)

# Initialize the database
def init_db():
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

init_db()

# Fetch all rules
@app.route("/rules", methods=["GET"])
def get_rules():
    conn = sqlite3.connect("rules.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fraud_rules")
    rules = [{"id": row[0], "condition": row[1], "action": row[2], "enabled": bool(row[3])} for row in cursor.fetchall()]
    conn.close()
    return jsonify(rules)

# Add a new rule
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

# Update an existing rule
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

# Delete a rule and reorder IDs
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

    # Reset the entire table and re-insert with new sequential IDs
    cursor.execute("DELETE FROM fraud_rules")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='fraud_rules'")  # Reset auto-increment

    for index, rule in enumerate(rules, start=1):
        cursor.execute("INSERT INTO fraud_rules (id, condition, action, enabled) VALUES (?, ?, ?, ?)", 
                       (index, rule[1], rule[2], rule[3]))

    conn.commit()
    conn.close()
    return jsonify({"message": "Rule deleted and IDs reordered successfully"})

# Serve the frontend
@app.route("/")
def index():
    return render_template("index.html")

# Run the app
if __name__ == "__main__":
    app.run(debug=True, port=5000)
