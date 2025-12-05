import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
import time
import os

# Make Google Earth Engine optional so the API can still run without it.
try:
    import ee
    GEE_AVAILABLE = True
except Exception as e:  # ImportError or credential issues are handled below
    ee = None
    GEE_AVAILABLE = False
    print(f"Warning: Google Earth Engine not available ({e}). Satellite data fetching disabled.")

# Initialize Google Earth Engine with project from environment when available
if GEE_AVAILABLE:
    try:
        from config import GEE_PROJECT_ID
        if GEE_PROJECT_ID:
            ee.Initialize(project=GEE_PROJECT_ID)
            print(f"✓ Google Earth Engine initialized with project: {GEE_PROJECT_ID}")
        else:
            print("Warning: GEE_PROJECT_ID not set. Satellite data fetching disabled.")
            GEE_AVAILABLE = False
    except Exception as e:
        print(f"Warning: Could not initialize Google Earth Engine: {e}")
        print("Satellite data fetching will be unavailable.")
        GEE_AVAILABLE = False

import sys
sys.path.append(str(Path(__file__).parent.parent / "data" / "raw"))
from uzbekistan_geography import get_all_locations

def get_ndvi_stats(lat, lon, start_date, end_date):
    """Get NDVI statistics over a period (mean, max, min, std)"""
    if not GEE_AVAILABLE:
        return None
    point = ee.Geometry.Point([lon, lat]).buffer(5000)
    
    modis = ee.ImageCollection('MODIS/061/MOD13Q1') \
        .filterDate(start_date, end_date) \
        .filterBounds(point) \
        .select('NDVI')
    
    count = modis.size().getInfo()
    if count == 0:
        return None
    
    def scale_ndvi(image):
        return image.multiply(0.0001)
    
    modis_scaled = modis.map(scale_ndvi)
    
    # Get multiple statistics in one call
    stats = modis_scaled.reduce(
        ee.Reducer.mean()
        .combine(ee.Reducer.max(), sharedInputs=True)
        .combine(ee.Reducer.min(), sharedInputs=True)
        .combine(ee.Reducer.stdDev(), sharedInputs=True)
    ).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=250,
        maxPixels=1e9
    )
    
    result = stats.getInfo()
    return {
        "mean": result.get("NDVI_mean"),
        "max": result.get("NDVI_max"),
        "min": result.get("NDVI_min"),
        "std": result.get("NDVI_stdDev"),
    }

def get_lst_stats(lat, lon, start_date, end_date):
    """Get Land Surface Temperature statistics"""
    if not GEE_AVAILABLE:
        return None
    point = ee.Geometry.Point([lon, lat]).buffer(5000)
    
    lst = ee.ImageCollection('MODIS/061/MOD11A2') \
        .filterDate(start_date, end_date) \
        .filterBounds(point) \
        .select('LST_Day_1km')
    
    count = lst.size().getInfo()
    if count == 0:
        return None
    
    def to_celsius(image):
        return image.multiply(0.02).subtract(273.15)
    
    lst_celsius = lst.map(to_celsius)
    
    stats = lst_celsius.reduce(
        ee.Reducer.mean()
        .combine(ee.Reducer.max(), sharedInputs=True)
        .combine(ee.Reducer.min(), sharedInputs=True)
    ).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=1000,
        maxPixels=1e9
    )
    
    result = stats.getInfo()
    return {
        "mean": result.get("LST_Day_1km_mean"),
        "max": result.get("LST_Day_1km_max"),
        "min": result.get("LST_Day_1km_min"),
    }

def get_precipitation_total(lat, lon, start_date, end_date):
    """Get total precipitation"""
    if not GEE_AVAILABLE:
        return None
    point = ee.Geometry.Point([lon, lat]).buffer(5000)
    
    chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
        .filterDate(start_date, end_date) \
        .filterBounds(point) \
        .select('precipitation')
    
    count = chirps.size().getInfo()
    if count == 0:
        return None
    
    total = chirps.sum().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=5000,
        maxPixels=1e9
    )
    
    return total.get('precipitation').getInfo()

def fetch_satellite_data_for_location(region, district, lat, lon):
    """Fetch 1 year of satellite data for a location"""
    if not GEE_AVAILABLE:
        return None, "Google Earth Engine unavailable"
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date_1y = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    try:
        # NDVI statistics for full year
        ndvi = get_ndvi_stats(lat, lon, start_date_1y, end_date)
        
        # Temperature statistics for full year
        lst = get_lst_stats(lat, lon, start_date_1y, end_date)
        
        # Annual precipitation
        precip = get_precipitation_total(lat, lon, start_date_1y, end_date)
        
        result = {
            "region": region,
            "district": district,
            "latitude": lat,
            "longitude": lon,
            "fetch_date": datetime.now().isoformat(),
            "period": "1_year",
            
            # NDVI (vegetation health)
            "ndvi_mean": round(ndvi["mean"], 4) if ndvi and ndvi.get("mean") else None,
            "ndvi_max": round(ndvi["max"], 4) if ndvi and ndvi.get("max") else None,
            "ndvi_min": round(ndvi["min"], 4) if ndvi and ndvi.get("min") else None,
            "ndvi_std": round(ndvi["std"], 4) if ndvi and ndvi.get("std") else None,
            
            # Temperature (°C)
            "lst_mean_c": round(lst["mean"], 1) if lst and lst.get("mean") else None,
            "lst_max_c": round(lst["max"], 1) if lst and lst.get("max") else None,
            "lst_min_c": round(lst["min"], 1) if lst and lst.get("min") else None,
            
            # Precipitation (mm/year)
            "precipitation_annual_mm": round(precip, 1) if precip else None,
        }
        return result, None
    
    except Exception as e:
        return None, str(e)

def fetch_all_uzbekistan_satellite_data(start_from=0):
    """Fetch satellite data for all Uzbekistan locations"""
    locations = get_all_locations()
    all_data = []
    errors = []
    
    print(f"Fetching 1-year satellite data for {len(locations)} locations...")
    print(f"Starting from index {start_from}")
    print("Estimated time: 45-60 minutes\n")
    
    for i, loc in enumerate(locations):
        if i < start_from:
            continue
            
        print(f"[{i+1}/{len(locations)}] {loc['region']} / {loc['district']}...", end=" ", flush=True)
        
        data, error = fetch_satellite_data_for_location(
            loc["region"],
            loc["district"],
            loc["latitude"],
            loc["longitude"]
        )
        
        if data and data.get('ndvi_mean'):
            all_data.append(data)
            print(f"OK (NDVI: {data['ndvi_min']:.2f}-{data['ndvi_max']:.2f}, Temp: {data['lst_mean_c']}°C)")
        elif data:
            all_data.append(data)
            print(f"PARTIAL (some data missing)")
        else:
            errors.append({"location": f"{loc['region']}/{loc['district']}", "error": error})
            print(f"ERROR: {error}")
        
        # Save checkpoint every 10 locations
        if (i + 1) % 10 == 0:
            save_satellite_data(all_data, "data/raw/satellite_data_partial.json")
            print(f"\n  Checkpoint: {len(all_data)} locations saved\n")
            time.sleep(2)
        else:
            time.sleep(0.5)
    
    return all_data, errors

def save_satellite_data(data, output_path="data/raw/satellite_data.json"):
    """Save satellite data to JSON and CSV"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    
    if data:
        df = pd.DataFrame(data)
        csv_path = output_path.replace(".json", ".csv")
        df.to_csv(csv_path, index=False)
    
    return output_path


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent.parent)
    
    # Quick test first
    print("=" * 50)
    print("TESTING WITH CHIRCHIQ (agricultural area)")
    print("=" * 50)
    test_data, test_error = fetch_satellite_data_for_location(
        "Tashkent Region", "Chirchiq", 41.4667, 69.5833
    )
    
    if test_data:
        print(f"\nTest Results:")
        print(f"  NDVI range: {test_data['ndvi_min']} - {test_data['ndvi_max']}")
        print(f"  NDVI mean:  {test_data['ndvi_mean']}")
        print(f"  Temp range: {test_data['lst_min_c']}°C - {test_data['lst_max_c']}°C")
        print(f"  Precip:     {test_data['precipitation_annual_mm']} mm/year")
    else:
        print(f"Test failed: {test_error}")
    
    print("\n")
    proceed = input("Test looks good? Start full fetch? (y/n): ")
    
    if proceed.lower() == 'y':
        print("\nStarting full fetch...\n")
        satellite_data, errors = fetch_all_uzbekistan_satellite_data(start_from=0)
        
        final_path = save_satellite_data(satellite_data, "data/raw/satellite_data.json")
        
        print("\n" + "="*50)
        print("COMPLETE")
        print("="*50)
        print(f"Successful: {len(satellite_data)} locations")
        print(f"Errors: {len(errors)}")
        print(f"Saved to: {final_path}")
        
        if satellite_data:
            df = pd.DataFrame(satellite_data)
            print(f"\n--- NDVI Summary ---")
            print(df[["ndvi_mean", "ndvi_max", "ndvi_min"]].describe().round(3))
            print(f"\n--- Temperature Summary (°C) ---")
            print(df[["lst_mean_c", "lst_max_c", "lst_min_c"]].describe().round(1))
            print(f"\n--- Precipitation (mm/year) ---")
            print(df["precipitation_annual_mm"].describe().round(1))
    else:
        print("Aborted.")