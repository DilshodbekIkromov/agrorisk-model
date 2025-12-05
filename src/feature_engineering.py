"""
Feature Engineering Module for AgroRisk Model

This module provides feature generation functions for creating complete
feature sets from satellite data and real-time weather for crop risk assessment.

Functions:
    - estimate_soil_moisture: Estimate soil moisture from satellite metrics
    - classify_climate_zone: Classify climate zone by region
    - calculate_seasonal_suitability: Check crop-season compatibility
    - calculate_region_suitability: Check crop-region compatibility
    - calculate_risk_flags: Identify frost and drought risks
    - fetch_real_time_weather: Get real-time weather from API
    - generate_complete_features: Generate all 28 features for prediction
"""

import numpy as np
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path
import sys

# Add data paths
sys.path.append(str(Path(__file__).parent.parent / "data" / "raw"))

from crops_database import get_crop_info, CROPS, DROUGHT_SENSITIVITY_SCORES, FROST_SENSITIVITY_SCORES


def estimate_soil_moisture(precip_mm, temp_mean_c, ndvi_mean):
    """
    Estimate soil moisture from satellite data.
    
    Args:
        precip_mm: Annual precipitation (mm)
        temp_mean_c: Mean land surface temperature (°C)
        ndvi_mean: Mean NDVI (vegetation index)
    
    Returns:
        float: Estimated soil moisture (0-1 scale)
    """
    # Base moisture from precipitation (500mm = optimal)
    precip_factor = min(precip_mm / 500, 1.0)
    
    # Temperature penalty (hotter = drier soil)
    temp_penalty = max(0, (temp_mean_c - 15) / 40)  # 15-35°C range
    
    # Vegetation boost (more vegetation = better moisture retention)
    ndvi_boost = ndvi_mean * 0.5
    
    # Combine factors
    base_moisture = 0.3 + (precip_factor * 0.4)
    adjusted = base_moisture * (1 - temp_penalty * 0.3) * (1 + ndvi_boost)
    
    return np.clip(adjusted, 0.1, 0.9)


def classify_climate_zone(region):
    """
    Classify climate zone based on region.
    
    Args:
        region: Region name
    
    Returns:
        str: Climate zone identifier
    """
    zones = {
        "tashkent": ["Tashkent City", "Tashkent Region"],
        "fergana": ["Fergana", "Andijan", "Namangan"],
        "bukhara": ["Bukhara", "Navoiy"],
        "karakalpakstan": ["Karakalpakstan"],
        "samarkand": ["Samarkand", "Jizzakh"],
        "south": ["Kashkadarya", "Surkhandarya"],
        "khorezm": ["Khorezm"],
        "sirdaryo": ["Sirdaryo"]
    }
    
    for zone, regions in zones.items():
        if region in regions:
            return zone
    return "other"


def calculate_seasonal_suitability(crop_name, month):
    """
    Check if month is within crop's growing season.
    
    Args:
        crop_name: Name of the crop
        month: Month number (1-12)
    
    Returns:
        int: 1 if suitable season, 0 otherwise
    """
    crop = get_crop_info(crop_name)
    start = crop["growing_season_start"]
    end = crop["growing_season_end"]
    
    if start <= end:  # Normal season (e.g., April-October)
        return 1 if start <= month <= end else 0
    else:  # Wraparound season (e.g., October-June for wheat)
        return 1 if month >= start or month <= end else 0


def calculate_region_suitability(crop_name, region):
    """
    Check if crop is suitable for the region.
    
    Args:
        crop_name: Name of the crop
        region: Region name
    
    Returns:
        int: 1 if suitable, 0 otherwise
    """
    crop = get_crop_info(crop_name)
    suitable_regions = crop.get("suitable_regions", [])
    return 1 if region in suitable_regions else 0


def calculate_risk_flags(crop_name, lst_min, lst_max, precip, temp_mean):
    """
    Calculate frost and drought risk flags.
    
    Args:
        crop_name: Name of the crop
        lst_min: Minimum land surface temperature (°C)
        lst_max: Maximum land surface temperature (°C)
        precip: Annual precipitation (mm)
        temp_mean: Mean temperature (°C)
    
    Returns:
        tuple: (frost_risk, drought_risk) as 0 or 1
    """
    crop = get_crop_info(crop_name)
    
    # Frost risk: minimum temperature below crop's critical threshold
    frost_risk = 1 if lst_min < (crop["optimal_temp_min"] - 5) else 0
    
    # Drought risk: low precipitation AND high temperatures
    water_stress = precip < (crop["water_need_mm"] * 0.6)
    heat_stress = temp_mean > crop["optimal_temp_max"]
    drought_risk = 1 if (water_stress and heat_stress) else 0
    
    return frost_risk, drought_risk


def fetch_real_time_weather(lat, lon):
    """
    Fetch real-time and forecast weather from Open-Meteo API (FREE, no API key needed).
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        dict: Weather data with current and forecast conditions
    """
    try:
        # Open-Meteo API - FREE and reliable
        url = "https://api.open-meteo.com/v1/forecast"
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,precipitation",
            "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum",
            "timezone": "Asia/Tashkent",
            "past_days": 7,  # Get last 7 days for historical context
            "forecast_days": 14  # Get 14-day forecast
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract current conditions
        current = data.get("current", {})
        daily = data.get("daily", {})
        
        # Calculate 7-day historical averages
        hist_temp_mean = np.mean(daily["temperature_2m_mean"][:7]) if len(daily["temperature_2m_mean"]) >= 7 else current.get("temperature_2m", 15)
        hist_precip = np.sum(daily["precipitation_sum"][:7]) if len(daily["precipitation_sum"]) >= 7 else 0
        
        # Calculate 14-day forecast averages
        forecast_temp = np.mean(daily["temperature_2m_mean"][7:]) if len(daily["temperature_2m_mean"]) > 7 else hist_temp_mean
        forecast_precip = np.sum(daily["precipitation_sum"][7:]) if len(daily["precipitation_sum"]) > 7 else 0
        
        # Estimate soil moisture from precipitation and temperature
        # Higher precip = higher moisture, higher temp = lower moisture
        hist_soil_moisture = min(0.9, 0.3 + (hist_precip / 100) * 0.4) * (1 - (hist_temp_mean - 15) / 100)
        hist_soil_moisture = max(0.1, hist_soil_moisture)
        
        current_soil_moisture = hist_soil_moisture  # Use historical estimate
        
        return {
            "historical": {
                "temp_mean_7d": hist_temp_mean,
                "precipitation_7d": hist_precip,
                "soil_moisture_7d": hist_soil_moisture
            },
            "current": {
                "temp_mean": current.get("temperature_2m", hist_temp_mean),
                "precipitation": current.get("precipitation", 0),
                "soil_moisture": current_soil_moisture
            },
            "forecast": {
                "temp_mean_14d": forecast_temp,
                "precipitation_14d": forecast_precip,
            },
            "success": True
        }
        
    except Exception as e:
        print(f"⚠️  Weather API error for ({lat}, {lon}): {e}")
        # Return fallback values based on historical satellite data
        return {
            "historical": {"temp_mean_7d": 20, "precipitation_7d": 10, "soil_moisture_7d": 0.3},
            "current": {"temp_mean": 20, "precipitation": 0, "soil_moisture": 0.3},
            "forecast": {"temp_mean_14d": 20, "precipitation_14d": 10},
            "success": False
        }


def generate_complete_features(satellite_row, crop_name, month=None, use_real_weather=True):
    """
    Generate all 28 features needed for model prediction.
    
    Args:
        satellite_row: Row from satellite data DataFrame or dict with satellite metrics
        crop_name: Name of the crop
        month: Month number (1-12), defaults to current month
        use_real_weather: Whether to fetch real-time weather (True) or use historical estimates (False)
    
    Returns:
        dict: Complete feature dictionary ready for model
    """
    if month is None:
        month = datetime.now().month
    
    # Get crop information
    crop = get_crop_info(crop_name)
    
    # Basic geospatial features
    region = satellite_row['region']
    district = satellite_row['district']
    lat = satellite_row['latitude']
    lon = satellite_row['longitude']
    
    # Satellite-derived features with safe fallbacks so API keeps working without GEE
    ndvi_mean = float(satellite_row.get('ndvi_mean', 0.3) or 0.3)
    ndvi_max = float(satellite_row.get('ndvi_max', ndvi_mean + 0.05) or ndvi_mean + 0.05)
    ndvi_min = float(satellite_row.get('ndvi_min', max(0.0, ndvi_mean - 0.05)) or max(0.0, ndvi_mean - 0.05))
    ndvi_std = float(satellite_row.get('ndvi_std', 0.05) or 0.05)
    lst_mean = float(satellite_row.get('lst_mean_c', 20.0) or 20.0)
    lst_min = float(satellite_row.get('lst_min_c', lst_mean - 5.0) or lst_mean - 5.0)
    lst_max = float(satellite_row.get('lst_max_c', lst_mean + 5.0) or lst_mean + 5.0)
    precip_annual = float(satellite_row.get('precipitation_annual_mm', 200.0) or 200.0)
    
    # Feature engineering
    climate_zone = classify_climate_zone(region)
    region_suitable = calculate_region_suitability(crop_name, region)
    season_suitable = calculate_seasonal_suitability(crop_name, month)
    frost_risk, drought_risk = calculate_risk_flags(crop_name, lst_min, lst_max, precip_annual, lst_mean)

    # Suitability scores expected by the production model
    crop_ndvi_min = float(crop.get("ndvi_healthy_min", 0.3) or 0.3)
    temp_mid = (crop["optimal_temp_min"] + crop["optimal_temp_max"]) / 2
    temp_span = max(1.0, crop["optimal_temp_max"] - crop["optimal_temp_min"])
    temp_match = np.clip(1 - abs(lst_mean - temp_mid) / (temp_span / 2 + 5), 0, 1)
    water_match = np.clip(precip_annual / max(1.0, crop["water_need_mm"]), 0, 1.5)
    ndvi_score = np.clip(ndvi_mean / max(0.1, crop_ndvi_min), 0, 2)
    
    # Soil moisture estimation
    hist_soil_moisture = estimate_soil_moisture(precip_annual, lst_mean, ndvi_mean)
    
    # Weather data (real-time or historical)
    if use_real_weather:
        weather = fetch_real_time_weather(lat, lon)
        hist_temp_mean = weather["historical"]["temp_mean_7d"]
        hist_precip_annual = precip_annual  # Use satellite annual precip as baseline
        current_temp_mean = weather["current"]["temp_mean"]
        current_precip = weather["current"]["precipitation"]
        current_soil_moisture = weather["current"]["soil_moisture"]
        forecast_temp_14d = weather["forecast"]["temp_mean_14d"]
        forecast_precip_14d = weather["forecast"]["precipitation_14d"]
    else:
        # Use historical satellite data as proxy
        hist_temp_mean = lst_mean
        hist_precip_annual = precip_annual
        current_temp_mean = lst_mean
        current_precip = precip_annual / 365 * 30  # Monthly estimate
        current_soil_moisture = hist_soil_moisture
        forecast_temp_14d = lst_mean
        forecast_precip_14d = precip_annual / 365 * 14  # 14-day estimate
    
    # NDVI proxy for current and forecast
    ndvi_current = ndvi_mean
    ndvi_forecast = ndvi_mean * 0.95  # Slight decrease as proxy
    
    # Get sensitivity scores
    drought_sens = DROUGHT_SENSITIVITY_SCORES.get(crop["drought_sensitivity"], 0.5)
    frost_sens = FROST_SENSITIVITY_SCORES.get(crop["frost_sensitivity"], 0.5)
    
    # Compile all features (28 total)
    features = {
        # Geospatial
        "region": region,
        "district": district,
        "latitude": lat,
        "longitude": lon,
        "climate_zone": climate_zone,
        "month": month,
        
        # Historical climate
        "hist_temp_mean": hist_temp_mean,
        "hist_precip_annual": hist_precip_annual,
        "hist_soil_moisture": hist_soil_moisture,
        
        # Current conditions
        "current_temp_mean": current_temp_mean,
        "current_precip": current_precip,
        "current_soil_moisture": current_soil_moisture,
        
        # Forecast
        "forecast_temp_14d": forecast_temp_14d,
        "forecast_precip_14d": forecast_precip_14d,
        
        # Risk flags
        "frost_risk": frost_risk,
        "drought_risk": drought_risk,
        
        # NDVI
        "ndvi_current": ndvi_current,
        "ndvi_forecast": ndvi_forecast,
        "ndvi_mean": ndvi_mean,
        "ndvi_max": ndvi_max,
        "ndvi_min": ndvi_min,
        "ndvi_std": ndvi_std,
        
        # Crop features
        "crop": crop_name,
        "crop_category": crop["category"],
        "crop_temp_min": crop["optimal_temp_min"],
        "crop_temp_max": crop["optimal_temp_max"],
        "crop_water_need": crop["water_need_mm"],
        "crop_moisture_min": crop["soil_moisture_min"],
        "crop_ndvi_min": crop_ndvi_min,
        "crop_drought_sens": drought_sens,
        "crop_frost_sens": frost_sens,
        
        # Suitability flags
        "region_suitable": region_suitable,
        "season_suitable": season_suitable,
        "temp_match": temp_match,
        "water_match": water_match,
        "ndvi_score": ndvi_score,

        # Legacy climate fields used by model artifact
        "lst_mean_c": lst_mean,
        "lst_max_c": lst_max,
        "lst_min_c": lst_min,
        "precipitation_annual_mm": precip_annual,
    }
    
    return features
