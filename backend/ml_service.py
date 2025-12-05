"""
ML Service - Wrapper for crop risk prediction model
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root / "data" / "raw"))

from model_training import AgroRiskModel
from feature_engineering import generate_complete_features
from uzbekistan_geography import get_coordinates
from crops_database import get_crop_info
from gee_fetcher import fetch_satellite_data_for_location


class MLService:
    """ML service for crop risk prediction"""
    
    def __init__(self):
        self.model = None
        self.sat_cache = None
        self.load_model()
        self.load_satellite_cache()
    
    def load_model(self):
        """Load the trained model"""
        try:
            model_path = Path(__file__).parent.parent / "models" / "agrorisk_model.joblib"
            if not model_path.exists():
                print(f"⚠️  Model not found at {model_path}")
                return
            
            import joblib
            loaded_model = joblib.load(model_path)
            
            if isinstance(loaded_model, dict):
                print("⚠️  Loaded model is a dictionary, wrapping in AgroRiskModel...")
                self.model = AgroRiskModel()
                self.model.model = loaded_model.get('model')
                self.model.label_encoders = loaded_model.get('label_encoders', {})
                self.model.feature_names = loaded_model.get('feature_cols', [])
                # Try to restore other attributes if available
                if 'explainer' in loaded_model:
                    self.model.explainer = loaded_model['explainer']
            else:
                self.model = loaded_model
                
            print("✅ ML model loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
    
    def load_satellite_cache(self):
        """Load cached satellite data for fallback"""
        try:
            csv_path = Path(__file__).parent.parent / "data" / "raw" / "satellite_data.csv"
            if csv_path.exists():
                self.sat_cache = pd.read_csv(csv_path)
                print(f"✅ Satellite cache loaded: {len(self.sat_cache)} rows")
        except Exception as e:
            print(f"⚠️  Could not load satellite cache: {e}")
            self.sat_cache = pd.DataFrame()
    
    def get_satellite_data(self, region, district, lat, lon):
        """Get satellite data with fallback to cache"""
        try:
            # Try real-time fetch
            satellite_data, error = fetch_satellite_data_for_location(region, district, lat, lon)
            if satellite_data is None or error:
                raise Exception(error or "No satellite data available")
            return satellite_data
        except Exception as e:
            print(f"⚠️  Using cached satellite data: {e}")
            
            # Try cache
            if self.sat_cache is not None and not self.sat_cache.empty:
                row = self.sat_cache[
                    (self.sat_cache["region"] == region) & 
                    (self.sat_cache["district"] == district)
                ]
                if not row.empty:
                    data = row.iloc[0].to_dict()
                    data.setdefault("latitude", lat)
                    data.setdefault("longitude", lon)
                    return data
            
            # Ultimate fallback
            return {
                "region": region,
                "district": district,
                "latitude": lat,
                "longitude": lon,
                "ndvi_mean": 0.3,
                "lst_mean_c": 20.0,
                "lst_min_c": 5.0,
                "lst_max_c": 35.0,
                "precipitation_annual_mm": 200.0
            }
    
    def predict_risk(self, region, district, crop):
        """
        Predict crop risk for given location and crop
        
        Returns dict with risk_score, risk_category, top_factors, etc.
        """
        try:
            if self.model is None:
                return {"error": "Model not loaded"}
            
            # Get coordinates
            coords = get_coordinates(region, district)
            if not coords:
                return {"error": "Could not get coordinates for location"}
            
            lat, lon = coords
            month = pd.Timestamp.now().month
            
            # Get satellite data
            satellite_data = self.get_satellite_data(region, district, lat, lon)
            
            # Generate features
            input_data = generate_complete_features(
                satellite_row=satellite_data,
                crop_name=crop.lower(),
                month=month,
                use_real_weather=True
            )
            
            # Make prediction
            input_df = pd.DataFrame([input_data])
            prediction = self.model.predict(input_df)[0]
            
            # Get recommendations
            recommendations = self.model.get_recommendations(input_df, crop.lower())
            
            # Get crop info
            crop_info = get_crop_info(crop.lower())
            
            return {
                "risk_score": float(prediction["risk_score"]),
                "risk_category": prediction["risk_category"],
                "confidence": prediction["confidence"],
                "top_factors": prediction.get("top_factors", []),
                "recommendations": recommendations[:3],
                "location_info": {
                    "region": region,
                    "district": district,
                    "latitude": lat,
                    "longitude": lon,
                    "climate_zone": input_data["climate_zone"],
                    "current_conditions": {
                        "temperature": round(input_data["current_temp_mean"], 1),
                        "precipitation": round(input_data["current_precip"], 1),
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
                    "name": crop,
                    "name_uz": crop_info["name_uz"],
                    "category": crop_info["category"],
                    "optimal_temp_range": f"{crop_info['optimal_temp_min']}-{crop_info['optimal_temp_max']}°C",
                    "water_need": f"{crop_info['water_need_mm']}mm/year",
                    "region_suitable": input_data["region_suitable"] == 1,
                    "season_suitable": input_data["season_suitable"] == 1,
                }
            }
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return {"error": str(e)}
    
    def calculate_financial_score(self, loan_amount, revenue, profit, assets, 
                                  debt, collateral, defaults, years_farming, ownership):
        """
        Calculate financial health score (0-100)
        
        Based on debt-to-asset ratio, profit margin, collateral coverage, 
        credit history, and farming experience
        """
        # Safe division helpers
        safe_assets = max(assets, 1)
        safe_revenue = max(revenue, 1)
        safe_loan = max(loan_amount, 1)
        
        # Calculate ratios
        debt_to_asset = (debt + loan_amount) / safe_assets
        profit_margin = profit / safe_revenue
        collateral_coverage = collateral / safe_loan
        
        # Base score
        score = 70
        
        # Debt-to-Asset impact
        if debt_to_asset > 0.7:
            score -= 30
        elif debt_to_asset > 0.5:
            score -= 15
        else:
            score += 10
        
        # Profitability
        if profit_margin < 0.1:
            score -= 10
        elif profit_margin > 0.3:
            score += 10
        
        # Collateral
        if collateral_coverage < 1.0:
            score -= 20
        elif collateral_coverage > 1.5:
            score += 10
        
        # Critical flags
        if defaults:
            score -= 50  # Previous default is major red flag
        
        if years_farming < 2:
            score -= 10  # Inexperienced farmer
        
        if ownership == 'leased_short':
            score -= 10  # Risk of losing land
        
        # Clamp to 0-100
        return max(0, min(100, score))
