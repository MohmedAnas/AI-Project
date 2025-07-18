from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, EmailStr, validator
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import re
import joblib
import traceback
import logging
from typing import Optional
import os # <--- Make sure os is imported for path manipulation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load artifacts with error handling ---
try:
    # Define the base path for your models directory
    # os.path.dirname(os.path.abspath(__file__)) gets the directory of the current script (main.py)
    # Then we join 'models' to it.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(script_dir, 'models')

    # Construct the full paths to the .pkl files
    classifier_path = os.path.join(models_dir, 'intent_classifier.pkl')
    preprocessor_path = os.path.join(models_dir, 'preprocessor.pkl')

    logger.info(f"DEBUG: Current working directory during model load: {os.getcwd()}")
    logger.info(f"DEBUG: Script directory: {script_dir}")
    logger.info(f"DEBUG: Attempting to load classifier from: {classifier_path}")
    logger.info(f"DEBUG: Attempting to load preprocessor from: {preprocessor_path}")

    # Check if the models directory and files actually exist before attempting to load
    if not os.path.isdir(models_dir):
        raise FileNotFoundError(f"Models directory not found at: {models_dir}")
    if not os.path.exists(classifier_path):
        raise FileNotFoundError(f"Classifier file not found at: {classifier_path}")
    if not os.path.exists(preprocessor_path):
        raise FileNotFoundError(f"Preprocessor file not found at: {preprocessor_path}")


    # Load the classifier directly
    model = joblib.load(classifier_path)
    # Load the ColumnTransformer (which includes OneHotEncoder and StandardScaler)
    preprocessor = joblib.load(preprocessor_path)
    logger.info("✅ Models and Preprocessor loaded successfully [Step 1]")

except FileNotFoundError as fnfe: # Catch specific FileNotFoundError for clarity
    logger.error(f"❌ File not found during model loading: {fnfe}")
    logger.error(f"Full traceback: {traceback.format_exc()}")
    raise # Re-raise to stop deployment if models aren't loaded

except Exception as e:
    logger.error(f"❌ General error loading models/preprocessor: {str(e)}")
    logger.error(f"Full traceback: {traceback.format_exc()}")
    raise

logger.info("ℹ️ FastAPI app instance creation starting [Step 2]")

# --- FastAPI setup ---
app = FastAPI(title="Lead Scoring API", version="1.0.0")

logger.info("✅ FastAPI app instance created [Step 3]")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("✅ Middleware added [Step 4]")

# --- Schema ---
class Lead(BaseModel):
    phone: str
    email: EmailStr
    creditScore: int
    ageGroup: str
    maritalStatus: str
    comments: str
    consent: bool
    annualIncome: float = 0.0
    netWorth: float = 0.0
    employmentStatus: str = "Unemployed"

    @validator("phone")
    def validate_phone(cls, v):
        if not re.fullmatch(r"\+91-\d{10}", v):
            raise ValueError("Phone number must match +91-xxxxxxxxxx format")
        return v

    @validator("creditScore")
    def validate_credit_score(cls, v):
        if v < 300 or v > 850:
            raise ValueError("Credit score must be between 300 and 850")
        return v

    @validator("consent")
    def validate_consent(cls, v):
        if not v:
            raise ValueError("Consent is required")
        return v

# Keep this clean_category function consistent with how data was prepared in ML_model.ipynb
def clean_category(value: str):
    if isinstance(value, str):
        cleaned_value = value.replace("–", "-").replace("—", "-").strip()
        return cleaned_value
    return value

# --- Lead Scoring Pipeline ---
def preprocess_lead(lead: Lead):
    try:
        logger.info(f"🔄 Processing lead: {lead.email}")

        # Create a DataFrame from the lead data
        # Column names here MUST match the ones used to fit the ColumnTransformer
        df = pd.DataFrame([{
            "MaritalStatus": clean_category(lead.maritalStatus),
            "EmploymentStatus": clean_category(lead.employmentStatus),
            "AgeGroup": clean_category(lead.ageGroup),
            "CreditScore": lead.creditScore,
            "AnnualIncome": lead.annualIncome,
            "NetWorth": lead.netWorth
        }])

        # Use the loaded preprocessor (ColumnTransformer) to transform the data
        processed_data = preprocessor.transform(df)

        logger.info(f"✅ Preprocessing completed for {lead.email}")
        return processed_data

    except Exception as e:
        logger.error(f"❌ Preprocessing error for {lead.email}: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Refined map_intent_to_score to use string labels for clarity
def map_intent_to_score_str(label_str: str) -> int:
    # This mapping should be consistent with the labels you used in pkl.py
    return {"High": 90, "Medium": 50, "Low": 20}.get(label_str, 0)


def rerank_score_from_comment(score: int, comment: str) -> int:
    comment = comment.lower()
    if any(word in comment for word in ["urgent", "asap", "interested"]):
        score += 10
    elif any(word in comment for word in ["not sure", "maybe", "later"]):
        score -= 10
    elif any(word in comment for word in ["not interested", "spam", "unsubscribe"]):
        score -= 20
    return max(0, min(100, score))

# --- In-memory DB ---
leads_db = []

# --- Middleware for request logging ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"📨 {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"📤 Response: {response.status_code}")
    return response

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Lead Scoring API is running!", "status": "healthy"}

@app.post("/score")
async def score_lead(lead: Lead):
    try:
        logger.info(f"📥 Received lead data for: {lead.email}")

        # Preprocess the lead
        X_processed = preprocess_lead(lead)

        # Predict using the loaded model
        # model.predict() returns the string label directly (e.g., 'High', 'Medium', 'Low')
        predicted_intent_label = model.predict(X_processed)[0] # Correctly gets the string label

        logger.info(f"🔮 Predicted class label: {predicted_intent_label}")

        initial_score = map_intent_to_score_str(predicted_intent_label)
        reranked_score = rerank_score_from_comment(initial_score, lead.comments)

        result = {
            "initialScore": initial_score,
            "rerankedScore": reranked_score,
            "intentClass": predicted_intent_label, # Use the string label directly here
            "message": "✅ Lead scored successfully!"
        }

        # Store lead with result
        lead_data = lead.dict()
        lead_data.update(result)
        leads_db.append(lead_data)

        logger.info(f"✅ Lead {lead.email} scored successfully: {reranked_score}")
        return result

    except ValueError as ve:
        logger.error(f"❌ Validation error: {str(ve)}")
        raise HTTPException(status_code=422, detail=f"Validation error: {str(ve)}")

    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/leads")
def get_leads():
    logger.info(f"📋 Retrieving {len(leads_db)} leads")
    return {"leads": leads_db, "count": len(leads_db)}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "models_loaded": True, # This will only be true if the load block succeeds
        "leads_count": len(leads_db)
    }

# --- Error handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ Global exception: {str(exc)}")
    logger.error(traceback.format_exc())
    return HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    logger.info("🚀 Starting Uvicorn server [Step 5]")
    import uvicorn
    # Use the PORT environment variable provided by Render, default to 8000 for local testing
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
