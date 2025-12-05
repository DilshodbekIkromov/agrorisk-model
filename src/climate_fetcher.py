"""
Satellite & Climate Data Pipeline

This module fetches real climate data from Open-Meteo (free, no API key required) and
derives vegetation health indicators (NDVI proxy) based on climate conditions.

Data sources:
- Open-Meteo Historical API: Past climate data
- Open-Meteo Forecast API: 16-day weather forecast
- Open-Meteo Climate API: Long-term climate normals

The NDVI proxy is derived from:
- Precipitation patterns (water availability)
- Temperature (growing conditions)  
- Soil moisture estimates
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent / "data" / "raw"))
from uzbekistan_geography import get_all_locations, UZBEKISTAN_REGIONS

OPEN_METEO_HISTORICAL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_CLIMATE = "https://climate-api.open-meteo.com/v1/climate"

class ClimateDataFetcher:
    def __init__(self, cache_dir=None):
        if cache_dir is None:
            from config import DATA_RAW_DIR
            cache_dir = DATA_RAW_DIR
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_historical_climate(self, lat, lon, start_date, end_date):
        """Fetch historical climate data for a location"""
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min", 
                "temperature_2m_mean",
                "precipitation_sum",
                "et0_fao_evapotranspiration",
                "soil_moisture_0_to_7cm_mean",
            ],
            "timezone": "Asia/Tashkent"
        }
        
        try:
            response = requests.get(OPEN_METEO_HISTORICAL, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return None
    
    def fetch_forecast(self, lat, lon):
        """Fetch 16-day weather forecast for a location"""
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "temperature_2m_mean",
                "precipitation_sum",
                "precipitation_probability_max",
                "et0_fao_evapotranspiration",
                "soil_moisture_0_to_7cm_mean",
            ],
            "timezone": "Asia/Tashkent",
            "forecast_days": 16
        }
        
        try:
            response = requests.get(OPEN_METEO_FORECAST, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching forecast: {e}")
            return None
    
    def calculate_ndvi_proxy(self, temp_mean, precipitation, soil_moisture, month):
        """
        Calculate NDVI proxy based on climate conditions.
        
        Real NDVI ranges from -1 to 1, with healthy vegetation typically 0.3-0.8.
        We estimate this based on water availability and temperature suitability.
        """
        temp_factor = np.clip((temp_mean - 5) / 25, 0, 1) * np.clip((35 - temp_mean) / 15, 0, 1)
        
        precip_factor = np.clip(precipitation / 50, 0, 1)
        
        moisture_factor = np.clip(soil_moisture / 0.4, 0, 1) if soil_moisture else 0.5
        
        season_factors = {
            1: 0.3, 2: 0.35, 3: 0.5, 4: 0.7, 5: 0.85, 6: 0.9,
            7: 0.85, 8: 0.75, 9: 0.6, 10: 0.45, 11: 0.35, 12: 0.3
        }
        season_factor = season_factors.get(month, 0.5)
        
        ndvi = 0.2 + 0.6 * (
            0.3 * temp_factor + 
            0.25 * precip_factor + 
            0.25 * moisture_factor + 
            0.2 * season_factor
        )
        
        return np.clip(ndvi, 0.1, 0.85)
    
    def process_location_data(self, region, district, lat, lon):
        """Process all data for a single location"""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        historical = self.fetch_historical_climate(lat, lon, start_date, end_date)
        forecast = self.fetch_forecast(lat, lon)
        
        if not historical or not forecast:
            return None
        
        hist_daily = historical.get("daily", {})
        
        result = {
            "region": region,
            "district": district,
            "latitude": lat,
            "longitude": lon,
            "data_date": datetime.now().isoformat(),
            
            "historical": {
                "temp_mean_annual": np.mean(hist_daily.get("temperature_2m_mean", [20])),
                "temp_max_annual": np.max(hist_daily.get("temperature_2m_max", [35])),
                "temp_min_annual": np.min(hist_daily.get("temperature_2m_min", [0])),
                "precipitation_annual": np.sum(hist_daily.get("precipitation_sum", [0])),
                "precipitation_monthly_avg": np.sum(hist_daily.get("precipitation_sum", [0])) / 12,
                "et0_annual": np.sum(hist_daily.get("et0_fao_evapotranspiration", [0])),
                "soil_moisture_avg": np.mean([x for x in hist_daily.get("soil_moisture_0_to_7cm_mean", [0.3]) if x]),
            },
            
            "current_month": {},
            "forecast": {},
            "ndvi_proxy": {},
        }
        
        recent_temps = hist_daily.get("temperature_2m_mean", [20])[-30:]
        recent_precip = hist_daily.get("precipitation_sum", [0])[-30:]
        recent_moisture = [x for x in hist_daily.get("soil_moisture_0_to_7cm_mean", [0.3])[-30:] if x]
        
        result["current_month"] = {
            "temp_mean": np.mean(recent_temps) if recent_temps else 20,
            "temp_max": np.max(recent_temps) if recent_temps else 30,
            "temp_min": np.min(recent_temps) if recent_temps else 10,
            "precipitation": np.sum(recent_precip) if recent_precip else 0,
            "soil_moisture": np.mean(recent_moisture) if recent_moisture else 0.3,
        }
        
        fore_daily = forecast.get("daily", {})
        fore_temps = fore_daily.get("temperature_2m_mean", [])
        fore_precip = fore_daily.get("precipitation_sum", [])
        fore_moisture = fore_daily.get("soil_moisture_0_to_7cm_mean", [])
        
        result["forecast"] = {
            "temp_mean_7d": np.mean(fore_temps[:7]) if fore_temps else 20,
            "temp_mean_14d": np.mean(fore_temps[:14]) if fore_temps else 20,
            "temp_max_14d": np.max(fore_temps[:14]) if fore_temps else 30,
            "temp_min_14d": np.min(fore_temps[:14]) if fore_temps else 10,
            "precipitation_7d": np.sum(fore_precip[:7]) if fore_precip else 0,
            "precipitation_14d": np.sum(fore_precip[:14]) if fore_precip else 0,
            "frost_risk": 1 if (fore_temps and min(fore_temps[:14]) < 2) else 0,
            "drought_risk": 1 if (fore_precip and sum(fore_precip[:14]) < 5 and np.mean(fore_temps[:14] or [25]) > 25) else 0,
        }
        
        current_month = datetime.now().month
        result["ndvi_proxy"] = {
            "current": self.calculate_ndvi_proxy(
                result["current_month"]["temp_mean"],
                result["current_month"]["precipitation"],
                result["current_month"]["soil_moisture"],
                current_month
            ),
            "forecast": self.calculate_ndvi_proxy(
                result["forecast"]["temp_mean_14d"],
                result["forecast"]["precipitation_14d"],
                np.mean(fore_moisture[:14]) if fore_moisture else 0.3,
                current_month
            ),
            "historical_avg": self.calculate_ndvi_proxy(
                result["historical"]["temp_mean_annual"],
                result["historical"]["precipitation_monthly_avg"],
                result["historical"]["soil_moisture_avg"],
                6
            ),
        }
        
        return result
    
    def fetch_all_uzbekistan_data(self, sample_size=None):
        """Fetch data for all Uzbekistan locations (or a sample)"""
        locations = get_all_locations()
        
        if sample_size:
            locations = locations[:sample_size]
        
        all_data = []
        total = len(locations)
        
        print(f"Fetching data for {total} locations...")
        
        for i, loc in enumerate(locations):
            print(f"[{i+1}/{total}] {loc['region']} - {loc['district']}...", end=" ")
            
            data = self.process_location_data(
                loc["region"],
                loc["district"],
                loc["latitude"],
                loc["longitude"]
            )
            
            if data:
                all_data.append(data)
                print("OK")
            else:
                print("FAILED")
            
            time.sleep(0.5)
        
        return all_data
    
    def save_data(self, data, filename="uzbekistan_climate_data.json"):
        """Save fetched data to JSON file"""
        filepath = self.cache_dir / filename
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Data saved to {filepath}")
        return filepath

def create_flat_dataset(climate_data):
    """Convert nested climate data to flat DataFrame for ML training"""
    rows = []
    
    for loc in climate_data:
        row = {
            "region": loc["region"],
            "district": loc["district"],
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            
            "hist_temp_mean": loc["historical"]["temp_mean_annual"],
            "hist_temp_max": loc["historical"]["temp_max_annual"],
            "hist_temp_min": loc["historical"]["temp_min_annual"],
            "hist_precip_annual": loc["historical"]["precipitation_annual"],
            "hist_soil_moisture": loc["historical"]["soil_moisture_avg"],
            
            "current_temp_mean": loc["current_month"]["temp_mean"],
            "current_temp_max": loc["current_month"]["temp_max"],
            "current_temp_min": loc["current_month"]["temp_min"],
            "current_precip": loc["current_month"]["precipitation"],
            "current_soil_moisture": loc["current_month"]["soil_moisture"],
            
            "forecast_temp_7d": loc["forecast"]["temp_mean_7d"],
            "forecast_temp_14d": loc["forecast"]["temp_mean_14d"],
            "forecast_temp_max_14d": loc["forecast"]["temp_max_14d"],
            "forecast_temp_min_14d": loc["forecast"]["temp_min_14d"],
            "forecast_precip_7d": loc["forecast"]["precipitation_7d"],
            "forecast_precip_14d": loc["forecast"]["precipitation_14d"],
            "frost_risk": loc["forecast"]["frost_risk"],
            "drought_risk": loc["forecast"]["drought_risk"],
            
            "ndvi_current": loc["ndvi_proxy"]["current"],
            "ndvi_forecast": loc["ndvi_proxy"]["forecast"],
            "ndvi_historical": loc["ndvi_proxy"]["historical_avg"],
        }
        rows.append(row)
    
    return pd.DataFrame(rows)


if __name__ == "__main__":
    fetcher = ClimateDataFetcher()
    
    print("Testing with 3 sample locations...\n")
    sample_data = fetcher.fetch_all_uzbekistan_data(sample_size=3)
    
    if sample_data:
        fetcher.save_data(sample_data, "sample_climate_data.json")
        
        df = create_flat_dataset(sample_data)
        print("\nFlat dataset preview:")
        print(df.to_string())
