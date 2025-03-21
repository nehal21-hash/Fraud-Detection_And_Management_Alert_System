import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# Load dataset (update the path to where you saved transactions_train.csv)
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

print("Original class distribution:\n", y.value_counts())

# Split data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Standardize numerical features
scaler = StandardScaler()
numerical_features = ['transaction_amount', 'transaction_hour', 'transaction_day', 'transaction_month']
X_train[numerical_features] = scaler.fit_transform(X_train[numerical_features])
X_test[numerical_features] = scaler.transform(X_test[numerical_features])

# Apply SMOTE for class balancing
smote = SMOTE(random_state=42)
X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)

print("Resampled class distribution:\n", y_train_smote.value_counts())

# Train Random Forest Classifier
clf_smote = RandomForestClassifier(n_estimators=100, random_state=42)
clf_smote.fit(X_train_smote, y_train_smote)

# Evaluate on the test set
y_pred_smote = clf_smote.predict(X_test)

# Print performance metrics
print("\nConfusion Matrix:\n", confusion_matrix(y_test, y_pred_smote))
print("\nClassification Report:\n", classification_report(y_test, y_pred_smote))
