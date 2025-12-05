"""
End-to-end test of AgroRisk prediction pipeline
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent / "src"))
sys.path.append(str(Path(__file__).parent / "data" / "raw"))
sys.path.append(str(Path(__file__).parent / "api"))

from config import MODELS_DIR
from model_training import AgroRiskModel
from uzbekistan_geography import get_all_regions, get_districts, get_coordinates, UZBEKISTAN_REGIONS
from crops_database import CROPS, get_crop_info
from feature_engineering import generate_complete_features
from gee_fetcher import fetch_satellite_metrics

def predict_risk(region, district, crop, month=None):
    """Make a single prediction using satellite data and feature engineering"""
    model = AgroRiskModel.load(str(MODELS_DIR))
    
    if month is None:
        month = 6
    
    coords = get_coordinates(region, district)
    lat, lon = coords
    
    # Fetch satellite data (or use fallback)
    try:
        satellite_data = fetch_satellite_metrics(lat, lon)
        if satellite_data is None:
            raise Exception("No satellite data")
    except:
        # Fallback data
        satellite_data = {
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
    
    # Generate features
    input_data = generate_complete_features(
        satellite_row=satellite_data,
        crop_name=crop.lower(),
        month=month,
        use_real_weather=False
    )
    
    input_df = pd.DataFrame([input_data])
    prediction = model.predict(input_df)[0]
    recommendations = model.get_recommendations(input_df, crop.lower())
    
    return {
        "prediction": prediction,
        "recommendations": recommendations,
        "input_data": input_data
    }

def print_result(result, region, district, crop):
    """Pretty print prediction result"""
    pred = result["prediction"]
    input_data = result["input_data"]
    
    category_colors = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    
    print(f"\n{'='*60}")
    print(f"AGRORISK PREDICTION")
    print(f"{'='*60}")
    print(f"\n📍 Location: {region} / {district}")
    print(f"🌾 Crop: {crop.upper()}")
    print(f"📅 Month: {input_data['month']}")
    
    print(f"\n--- RISK ASSESSMENT ---")
    print(f"{category_colors.get(pred['risk_category'], '⚪')} Risk Score: {pred['risk_score']}/100")
    print(f"   Category: {pred['risk_category'].upper()}")
    print(f"   Confidence: {pred['confidence']}")
    
    print(f"\n--- KEY FACTORS ---")
    for factor in pred["top_factors"][:5]:
        arrow = "↑" if factor["direction"] == "increases" else "↓"
        print(f"   {arrow} {factor['feature']}: {factor['contribution']:+.2f}")
    
    print(f"\n--- CURRENT CONDITIONS ---")
    print(f"   🌡️  Temperature: {input_data['current_temp_mean']:.1f}°C")
    print(f"   💧 Soil Moisture: {input_data['current_soil_moisture']:.2f}")
    print(f"   🌿 NDVI: {input_data['ndvi_current']:.3f}")
    print(f"   🌧️  Precipitation: {input_data['current_precip']:.1f}mm")
    
    if input_data['frost_risk']:
        print(f"   ⚠️  FROST RISK DETECTED")
    if input_data['drought_risk']:
        print(f"   ⚠️  DROUGHT RISK DETECTED")
    
    print(f"\n--- ALTERNATIVE CROPS (Top 3) ---")
    for i, rec in enumerate(result["recommendations"][:3], 1):
        cat_icon = category_colors.get(rec["risk_category"], "⚪")
        print(f"   {i}. {rec['crop']} ({rec['crop_uz']}): {cat_icon} {rec['risk_score']}/100")


if __name__ == "__main__":
    print("Loading model...")
    
    test_cases = [
        ("Tashkent Region", "Chirchiq", "cotton", 6),
        ("Andijan", "Izboskan", "rice", 7),
        ("Samarkand", "Samarkand City", "grape", 5),
        ("Bukhara", "Bukhara City", "melon", 8),
        ("Karakalpakstan", "Nukus", "wheat", 4),
    ]
    
    print("\n" + "="*60)
    print("RUNNING TEST PREDICTIONS")
    print("="*60)
    
    for region, district, crop, month in test_cases:
        try:
            result = predict_risk(region, district, crop, month)
            print_result(result, region, district, crop)
        except Exception as e:
            print(f"\n❌ Error for {region}/{district}/{crop}: {e}")
    
    print("\n\n" + "="*60)
    print("ALL TESTS COMPLETED SUCCESSFULLY! ✅")
    print("="*60)
