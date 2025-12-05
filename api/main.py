"""
AgroRisk API - Agricultural Risk Assessment Service

Endpoints:
- POST /predict: Get risk score for region + district + crop
- GET /regions: List all available regions
- GET /districts/{region}: List districts in a region  
- GET /crops: List all available crops
- GET /recommendations: Get alternative crop recommendations

The API fetches real-time weather data (when available) and combines
it with the trained ML model to provide risk assessments.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import shap

sys.path.append(str(Path(__file__).parent.parent / "src"))
sys.path.append(str(Path(__file__).parent.parent / "data" / "raw"))

from model_training import AgroRiskModel, format_explanation
from uzbekistan_geography import (
    get_all_regions, get_districts, get_coordinates, UZBEKISTAN_REGIONS
)
from crops_database import (
    CROPS, get_all_crops, get_crop_info, get_suitable_crops_for_region,
    DROUGHT_SENSITIVITY_SCORES, FROST_SENSITIVITY_SCORES
)
from feature_engineering import generate_complete_features
from gee_fetcher import fetch_satellite_data_for_location

app = FastAPI(
    title="AgroRisk Copilot API",
    description="AI-powered agricultural risk assessment for Uzbekistan",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path), html=True), name="static")
    print(f"Serving frontend from {frontend_path}")

MODEL_WRAPPER: Optional[AgroRiskModel] = None
SAT_CACHE = None  # Lazy-loaded satellite fallback data


def get_model() -> AgroRiskModel:
    """Load and return the trained AgroRiskModel wrapper.

    The saved artifact is the full AgroRiskModel object (not a dict), so we keep
    the original preprocessing, encoders, and SHAP explainer intact. If a legacy
    artifact is encountered, we fall back gracefully.
    """
    global MODEL_WRAPPER

    if MODEL_WRAPPER is not None:
        return MODEL_WRAPPER

    model_path = Path(__file__).parent.parent / "models" / "agrorisk_model.joblib"
    if not model_path.exists():
        raise RuntimeError(f"Model not found at {model_path}")

    import joblib

    loaded = joblib.load(model_path)

    # Preferred: persisted AgroRiskModel instance
    if isinstance(loaded, AgroRiskModel):
        MODEL_WRAPPER = loaded
        print("Model wrapper loaded (AgroRiskModel)")
    # Legacy: dict-style payload {model, label_encoders, feature_cols}
    elif isinstance(loaded, dict) and "model" in loaded:
        wrapper = AgroRiskModel()
        wrapper.model = loaded.get("model")
        wrapper.label_encoders = loaded.get("label_encoders", {})
        wrapper.feature_names = loaded.get("feature_cols") or loaded.get("feature_names")
        MODEL_WRAPPER = wrapper
        print("Model wrapper reconstructed from legacy artifact")
    else:
        raise RuntimeError("Unsupported model artifact format. Expected AgroRiskModel or dict with 'model'.")

    # Initialize SHAP explainer if missing
    if MODEL_WRAPPER and MODEL_WRAPPER.explainer is None and MODEL_WRAPPER.model is not None:
        try:
            MODEL_WRAPPER.explainer = shap.TreeExplainer(MODEL_WRAPPER.model)
            print("SHAP explainer initialized")
        except Exception as e:
            print(f"Warning: could not initialize SHAP explainer: {e}")

    return MODEL_WRAPPER


def load_cached_satellite(region: str, district: str):
    """Fallback satellite metrics from precomputed CSV when GEE is unavailable."""
    global SAT_CACHE
    if SAT_CACHE is None:
        csv_path = Path(__file__).parent.parent / "data" / "raw" / "satellite_data.csv"
        if csv_path.exists():
            try:
                SAT_CACHE = pd.read_csv(csv_path)
                print(f"Loaded cached satellite data: {len(SAT_CACHE)} rows")
            except Exception as e:
                print(f"Warning: failed to read cached satellite data: {e}")
                SAT_CACHE = pd.DataFrame()
        else:
            SAT_CACHE = pd.DataFrame()

    if SAT_CACHE.empty:
        return None

    row = SAT_CACHE[(SAT_CACHE["region"] == region) & (SAT_CACHE["district"] == district)]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


class PredictionRequest(BaseModel):
    region: str = Field(..., example="Tashkent Region")
    district: str = Field(..., example="Chirchiq")
    crop: str = Field(..., example="cotton")

class PredictionResponse(BaseModel):
    risk_score: float
    risk_category: str
    confidence: str
    top_factors: List[dict]
    recommendations: List[dict]
    location_info: dict
    crop_info: dict

class RegionResponse(BaseModel):
    regions: List[str]

class DistrictResponse(BaseModel):
    region: str
    districts: List[str]

class CropResponse(BaseModel):
    crops: List[dict]


@app.on_event("startup")
async def startup_event():
    try:
        get_model()
    except Exception as e:
        print(f"Warning: Could not load model on startup: {e}")


@app.get("/", tags=["Health"])
async def root():
    """Redirect to frontend UI"""
    return RedirectResponse(url="/static/index.html")


@app.get("/api", tags=["Health"])
async def api_info():
    """API information endpoint"""
    return {
        "service": "AgroRisk Copilot API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    model_loaded = MODEL_WRAPPER is not None
    return {
        "status": "healthy" if model_loaded else "degraded",
        "model_loaded": model_loaded
    }


@app.get("/regions", response_model=RegionResponse, tags=["Geography"])
async def list_regions():
    return {"regions": get_all_regions()}


@app.get("/districts/{region}", response_model=DistrictResponse, tags=["Geography"])
async def list_districts(region: str):
    districts = get_districts(region)
    if not districts:
        raise HTTPException(status_code=404, detail=f"Region '{region}' not found")
    return {"region": region, "districts": districts}


@app.get("/crops", response_model=CropResponse, tags=["Crops"])
async def list_crops():
    crops_list = []
    for name, info in CROPS.items():
        crops_list.append({
            "name": name,
            "name_uz": info["name_uz"],
            "category": info["category"],
            "growing_season": f"{info['growing_season_start']}-{info['growing_season_end']}",
            "water_need_mm": info["water_need_mm"],
        })
    return {"crops": crops_list}


@app.get("/crops/{region}", tags=["Crops"])
async def list_suitable_crops(region: str):
    if region not in UZBEKISTAN_REGIONS:
        raise HTTPException(status_code=404, detail=f"Region '{region}' not found")
    
    suitable = get_suitable_crops_for_region(region)
    crops_list = []
    for name in suitable:
        info = CROPS[name]
        crops_list.append({
            "name": name,
            "name_uz": info["name_uz"],
            "category": info["category"],
        })
    return {"region": region, "suitable_crops": crops_list}


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_risk(request: PredictionRequest):
    model = get_model()

    if request.region not in UZBEKISTAN_REGIONS:
        raise HTTPException(status_code=404, detail=f"Region '{request.region}' not found")
    
    districts = get_districts(request.region)
    if request.district not in districts:
        raise HTTPException(
            status_code=404, 
            detail=f"District '{request.district}' not found in {request.region}"
        )
    
    if request.crop.lower() not in CROPS:
        raise HTTPException(status_code=404, detail=f"Crop '{request.crop}' not found")
    
    coords = get_coordinates(request.region, request.district)
    if not coords:
        raise HTTPException(status_code=500, detail="Could not get coordinates")
    
    lat, lon = coords
    month = pd.Timestamp.now().month
    
    # Try to fetch real satellite data from Google Earth Engine
    try:
        satellite_data, error = fetch_satellite_data_for_location(request.region, request.district, lat, lon)
        if satellite_data is None or error:
            raise Exception(error or "No satellite data available")
    except Exception as e:
        print(f"⚠️  Satellite data fetch failed for {request.region}/{request.district}: {e}")
        cached = load_cached_satellite(request.region, request.district)
        if cached:
            satellite_data = cached
            satellite_data.setdefault("latitude", lat)
            satellite_data.setdefault("longitude", lon)
        else:
            satellite_data = {
                "region": request.region,
                "district": request.district,
                "latitude": lat,
                "longitude": lon,
                "ndvi_mean": 0.3,
                "lst_mean_c": 20.0,
                "lst_min_c": 5.0,
                "lst_max_c": 35.0,
                "precipitation_annual_mm": 200.0
            }
    
    # Generate complete features using the feature engineering module
    input_data = generate_complete_features(
        satellite_row=satellite_data,
        crop_name=request.crop.lower(),
        month=month,
        use_real_weather=True  # Fetch real-time weather from API
    )

    # Build DataFrame and run through the full model wrapper to keep preprocessing + SHAP
    input_df = pd.DataFrame([input_data])
    prediction = model.predict(input_df)[0]

    # Deterministic recommendations using the trained model
    recommendations = model.get_recommendations(input_df, request.crop.lower())

    # Get crop info for response
    crop_info = get_crop_info(request.crop.lower())

    return {
        "risk_score": float(prediction["risk_score"]),
        "risk_category": prediction["risk_category"],
        "confidence": prediction["confidence"],
        "top_factors": prediction.get("top_factors", []),
        "recommendations": recommendations[:3],
        "location_info": {
            "region": request.region,
            "district": request.district,
            "latitude": lat,
            "longitude": lon,
            "climate_zone": input_data["climate_zone"],
            "current_conditions": {
                "temperature": round(input_data["current_temp_mean"], 1),
                "precipitation": round(input_data["current_precip"], 1),
                "soil_moisture": round(input_data["current_soil_moisture"], 2),
                "ndvi": round(input_data["ndvi_current"], 3),
            },
            "forecast": {
                "temp_14d": round(input_data["forecast_temp_14d"], 1),
                "precip_14d": round(input_data["forecast_precip_14d"], 1),
                "frost_risk": bool(input_data["frost_risk"]),
                "drought_risk": bool(input_data["drought_risk"]),
            }
        },
        "crop_info": {
            "name": request.crop,
            "name_uz": crop_info["name_uz"],
            "category": crop_info["category"],
            "optimal_temp_range": f"{crop_info['optimal_temp_min']}-{crop_info['optimal_temp_max']}°C",
            "water_need": f"{crop_info['water_need_mm']}mm/year",
            "region_suitable": input_data["region_suitable"] == 1,
            "season_suitable": input_data["season_suitable"] == 1,
        }
    }


@app.get("/batch-predict", tags=["Prediction"])
async def batch_predict_region(region: str, crop: str):
    """Get risk predictions for all districts in a region (for heatmap)"""
    model = get_model()
    
    if region not in UZBEKISTAN_REGIONS:
        raise HTTPException(status_code=404, detail=f"Region '{region}' not found")
    
    if crop.lower() not in CROPS:
        raise HTTPException(status_code=404, detail=f"Crop '{crop}' not found")
    
    districts = get_districts(region)
    month = pd.Timestamp.now().month
    results = []
    
    for district in districts:
        try:
            request = PredictionRequest(
                region=region,
                district=district,
                crop=crop
            )
            prediction = await predict_risk(request)
            results.append({
                "district": district,
                "risk_score": prediction["risk_score"],
                "risk_category": prediction["risk_category"],
                "latitude": prediction["location_info"]["latitude"],
                "longitude": prediction["location_info"]["longitude"],
            })
        except Exception as e:
            results.append({
                "district": district,
                "error": str(e)
            })
    
    return {
        "region": region,
        "crop": crop,
        "districts": results
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
