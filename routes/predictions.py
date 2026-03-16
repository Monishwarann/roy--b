from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
from database import get_drug_predictions_collection, get_analysis_history_collection
from models.schemas import ToxicityInput, DrugEffectivenessInput
from models.auth import decode_access_token
from ml_models.predictor import predict_toxicity, predict_drug_effectiveness

router = APIRouter(tags=["ML Predictions"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_optional_user(token: str = Depends(oauth2_scheme)):
    if not token:
        return None
    email = decode_access_token(token)
    return 


@router.post("/predict-toxicity")
async def predict_toxicity_endpoint(
    data: ToxicityInput,
    user_email: str = Depends(get_optional_user)
):
    """Run ML toxicity prediction on molecular features"""
    try:
        result = predict_toxicity(data)

        # Save to history if user is logged in
        if user_email:
            history_col = get_analysis_history_collection()
            predictions_col = get_drug_predictions_collection()

            record = {
                "user_email": user_email,
                "analysis_type": "toxicity",
                "input_data": data.dict(),
                "result": result,
                "timestamp": datetime.utcnow()
            }
            await history_col.insert_one(record)
            await predictions_col.insert_one({**record, "model": "DNN Toxicity Classifier"})

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/predict-drug")
async def predict_drug_endpoint(
    data: DrugEffectivenessInput,
    user_email: str = Depends(get_optional_user)
):
    """Run ML drug effectiveness prediction"""
    try:
        result = predict_drug_effectiveness(data)

        # Save to history if user is logged in
        if user_email:
            history_col = get_analysis_history_collection()
            predictions_col = get_drug_predictions_collection()

            record = {
                "user_email": user_email,
                "analysis_type": "drug_effectiveness",
                "input_data": data.dict(),
                "result": result,
                "timestamp": datetime.utcnow()
            }
            await history_col.insert_one(record)
            await predictions_col.insert_one({**record, "model": "Random Forest Effectiveness"})

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.get("/history")
async def get_prediction_history(token: str = Depends(oauth2_scheme)):
    """Fetch user's prediction history"""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")

    history_col = get_analysis_history_collection()
    cursor = history_col.find(
        {"user_email": email},
        {"_id": 0}
    ).sort("timestamp", -1).limit(20)

    history = []
    async for item in cursor:
        if "timestamp" in item:
            item["timestamp"] = str(item["timestamp"])
        history.append(item)

    return {"history": history, "count": len(history)}
