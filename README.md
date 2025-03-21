# Fraud Detection System

This repository contains a fraud detection system that uses a combination of **Random Forest machine learning model** and **rule-based detection** to identify fraudulent transactions. The system is built using **Flask**, **SQLite**, and **Python-based machine learning libraries**.

## Features
- **Machine Learning Model (Random Forest)** for fraud detection.
- **Rule-Based Fraud Detection** using configurable conditions.
- **Web Interface** to manually add rules and analyze transactions.
- **API Endpoints** for processing and reporting fraud cases.

## Technology Stack

### **Frontend:**
- **HTML, CSS, JavaScript** – For UI and data visualization.
- **Live Server** – To run the frontend locally.

### **Backend:**
- **Python (Flask)** – Handles API requests and ML model execution.
- **SQLite** – Stores transactions and fraud detection results.

### **Machine Learning & Fraud Detection:**
- **Random Forest Classifier** – Used for fraud detection.
- **Scikit-learn** – Model training and evaluation.
- **Rule-Based System** – Identifies fraudulent transactions using defined conditions.

### **Other Tools & Libraries:**
- **Pandas & NumPy** – Data processing.
- **Pickle** – Model storage and loading.
- **Curl / Postman** – API testing.

## Installation Requirements

### **Prerequisites:**
Ensure you have **Python 3.8+** installed along with the following dependencies:

```bash
pip install flask pandas numpy scikit-learn pickle-mixin
```

## Steps to Run Locally

Follow these steps to set up and run the fraud detection system locally:

### **1) Train the Machine Learning Model**
Run the following script to train the fraud detection model:

```bash
python train_fraud_model.py
```

### **2) Start Rule Manager**
This script allows manual addition of fraud detection rules:

```bash
python rule_manager.py
```

### **3) Open the Web Interface**
- Open the **index.html** file in a browser.
- If using **Live Server**, right-click on **index.html** and select `Open with Live Server`.

### **4) Add Fraud Detection Rules Manually**
In the web UI, manually enter the following fraud detection rules:

| Condition | Action |
|-----------|--------|
| `transaction_amount > 1000000` | High-value transaction flagged |
| `transaction_hour < 5 or transaction_hour > 23` | Suspicious transaction time detected |
| `transaction_payment_mode_anonymous in [3, 6, 7]` | Uncommon payment mode used |
| `payer_browser_anonymous > 5` | Unusual browser detected |
| `payment_gateway_bank_anonymous in [5, 9, 12]` | Suspicious bank gateway used |

### **5) Start Fraud Detection API**
Run the Flask API that processes transactions and applies fraud detection:

```bash
python fraud_detection_api.py
```

### **6) Add Transactions**
Run the script to add transactions to the system:

```bash
python trans_add.py
```

## API Endpoints

### **1. Detect Fraudulent Transactions**
#### **Endpoint:**
```http
POST /detect_fraud
```
#### **Request Body (JSON Format):**
```json
{
  "transaction_id": "txn_1234",
  "amount": 50000,
  "hour": 23,
  "payment_mode": 6,
  "browser_id": 7,
  "bank_gateway": 9
}
```
#### **Response:**
```json
{
  "transaction_id": "txn_1234",
  "fraud_status": "Fraudulent",
  "fraud_score": 0.85,
  "reason": "Uncommon payment mode used"
}
```

### **2. Get Fraud Reports**
#### **Endpoint:**
```http
GET /fraud_report
```
#### **Response:**
```json
{
  "total_transactions": 11,
  "total_fraudulent": 7,
  "total_fraud_amount": 3260000.75,
  "avg_fraud_score": 0.52
}
```

## Future Enhancements
- **Improve ML Model** by fine-tuning and adding more features.
- **Database Integration** to allow real-time tracking.
- **Admin Panel** for better rule management.

---
Feel free to contribute by submitting pull requests or opening issues!
