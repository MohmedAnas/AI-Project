from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, EmailStr, validator
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import re
import joblib
import traceback
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load artifacts with error handling ---
try:
    # Load the classifier directly
    model = joblib.load("intent_classifier.pkl")
    # Load the ColumnTransformer (which includes OneHotEncoder and StandardScaler)
    preprocessor = joblib.load("preprocessor.pkl")
    logger.info("✅ Models and Preprocessor loaded successfully [Step 1]")

except Exception as e:
    logger.error(f"❌ Error loading models/preprocessor: {str(e)}")
    raise

logger.info("ℹ️ FastAPI app instance creation starting [Step 2]")

# --- FastAPI setup ---
# REMOVED DUPLICATE: app = FastAPI(title="Lead Scoring API", version="1.0.0")
app = FastAPI(title="Lead Scoring API", version="1.0.0") # Keep only one instance here

logger.info("✅ FastAPI app instance created [Step 3]") # This log now applies to the actual app instance

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
        "models_loaded": True,
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
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")