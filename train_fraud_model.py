import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier

# Load dataset
df = pd.read_csv("transactions_train.csv")

# Fill missing values and drop sparse column
df['transaction_amount'].fillna(df['transaction_amount'].median(), inplace=True)
df.drop(columns=['payer_mobile_anonymous'], inplace=True)

# Extract date-time features
df['transaction_date'] = pd.to_datetime(df['transaction_date'])
df['transaction_hour'] = df['transaction_date'].dt.hour
df['transaction_day'] = df['transaction_date'].dt.day
df['transaction_month'] = df['transaction_date'].dt.month
df.drop(columns=['transaction_date'], inplace=True)

# Encode categorical features
categorical_features = ['transaction_channel', 'payer_browser_anonymous', 'transaction_payment_mode_anonymous', 'payment_gateway_bank_anonymous']
label_encoders = {col: LabelEncoder() for col in categorical_features}
for col in categorical_features:
    df[col] = label_encoders[col].fit_transform(df[col])

# Drop non-informative columns
df.drop(columns=['transaction_id_anonymous', 'payee_id_anonymous', 'payer_email_anonymous', 'payee_ip_anonymous'], inplace=True)

# Define features and target
X = df.drop(columns=['is_fraud'])
y = df['is_fraud']

# Split data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Standardize numerical features
scaler = StandardScaler()
numerical_features = ['transaction_amount', 'transaction_hour', 'transaction_day', 'transaction_month']
X_train[numerical_features] = scaler.fit_transform(X_train[numerical_features])
X_test[numerical_features] = scaler.transform(X_test[numerical_features])

# Undersampling: take all fraud cases and equal number of non-fraud cases from training set
fraud_indices = y_train[y_train == 1].index
nonfraud_indices = y_train[y_train == 0].index

n_frauds = len(fraud_indices)
nonfraud_sample_indices = np.random.choice(nonfraud_indices, n_frauds, replace=False)
undersample_indices = np.concatenate([fraud_indices, nonfraud_sample_indices])

X_train_under = X_train.loc[undersample_indices]
y_train_under = y_train.loc[undersample_indices]

# Train Random Forest model
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train_under, y_train_under)

# Save model
with open("fraud_model.pkl", "wb") as model_file:
    pickle.dump(clf, model_file)

print("Model training complete. Saved as fraud_model.pkl")
