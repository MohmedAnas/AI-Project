import pandas as pd
import joblib
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

# 🔹 Step 1: Load Prepared Dataset
df = pd.read_csv(r'E:\AI Lead\Dataset\AI_lead_Dataset_prepared.csv')

# 🔹 Step 2: Define Features and Target
target_col = 'RiskScore'
cat_features = ['MaritalStatus', 'EmploymentStatus', 'AgeGroup']
num_features = ['CreditScore', 'AnnualIncome', 'NetWorth']

# X = Input features, y = Target
X = df[cat_features + num_features]
y_continuous = df[target_col]

# 🔹 NEW: Convert continuous RiskScore to discrete classes
# Method 1: Using quantiles (equal frequency bins)
y = pd.qcut(y_continuous, q=3, labels=['Low', 'Medium', 'High'])

# Check the distribution
print("Risk Score Distribution:")
print(y.value_counts())
print(f"Original continuous range: {y_continuous.min():.2f} to {y_continuous.max():.2f}")

# 🔹 Step 3: Create Preprocessing Pipeline (ColumnTransformer)
# IMPORTANT: This preprocessor is *fitted* as part of the main pipeline.
# It uses handle_unknown='ignore' as you already have, which is good.
preprocessor = ColumnTransformer(transformers=[
    ('cat', OneHotEncoder(sparse_output=False, handle_unknown='ignore'), cat_features),
    ('num', StandardScaler(), num_features)
])

# 🔹 Step 4: Build Preprocessing + Classifier Pipeline
pipeline = Pipeline(steps=[
    ('preprocessing', preprocessor), # This is your ColumnTransformer
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
])

# 🔹 Step 5: Split Data and Train
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
pipeline.fit(X_train, y_train)

# 🔹 Step 6: Save the ENTIRE Pipeline OR its fitted components
# OPTION A: Save the full pipeline (Recommended for simplicity)
joblib.dump(pipeline, 'full_prediction_pipeline.pkl')
print("✅ 'full_prediction_pipeline.pkl' saved successfully.")

# OPTION B: Save the fitted preprocessor and the classifier separately (to match your main.py loading pattern)
# Access the fitted preprocessor and classifier from the *fitted* pipeline
fitted_preprocessor = pipeline.named_steps['preprocessing']
fitted_classifier = pipeline.named_steps['classifier']

joblib.dump(fitted_preprocessor, 'preprocessor.pkl')
joblib.dump(fitted_classifier, 'intent_classifier.pkl')
print("✅ 'preprocessor.pkl' and 'intent_classifier.pkl' saved successfully.")

# You no longer need to save individual encoder, scaler, or feature_names.pkl
# The fitted_preprocessor contains the fitted encoder and scaler within it.
# The feature names are implicitly handled by the ColumnTransformer's transformation.

# 🔹 Test the model (using the pipeline)
accuracy = pipeline.score(X_test, y_test)
print(f"✅ Classification Accuracy: {accuracy:.3f}")