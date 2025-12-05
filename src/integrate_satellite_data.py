"""
Integrate real satellite data with crop database to create training data
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent / "data" / "raw"))
from crops_database import (
    CROPS, get_all_crops, get_crop_info, get_suitable_crops_for_region,
    DROUGHT_SENSITIVITY_SCORES, FROST_SENSITIVITY_SCORES
)

def load_satellite_data():
    """Load real satellite data"""
    path = Path(__file__).parent.parent / "data" / "raw" / "satellite_data.csv"
    df = pd.read_csv(path)
    print(f"Loaded satellite data: {len(df)} locations")
    return df

def calculate_region_suitability(crop_name, region):
    """Check if crop is suitable for region"""
    crop = get_crop_info(crop_name)
    if not crop:
        return 0
    suitable = crop["suitable_regions"]
    if "all" in suitable:
        return 1
    return 1 if region in suitable else 0

def calculate_temp_match(crop_name, temp_mean, temp_max, temp_min):
    """Calculate temperature match score"""
    crop = get_crop_info(crop_name)
    if not crop:
        return 0.5
    
    opt_min = crop["optimal_temp_min"]
    opt_max = crop["optimal_temp_max"]
    crit_min = crop["critical_temp_min"]
    crit_max = crop["critical_temp_max"]
    
    score = 1.0
    
    # Penalty if extremes exceed critical thresholds
    if temp_max > crit_max:
        score -= 0.2 * min(1, (temp_max - crit_max) / 10)
    if temp_min < crit_min:
        score -= 0.2 * min(1, (crit_min - temp_min) / 10)
    
    # Score based on mean temp fit
    if opt_min <= temp_mean <= opt_max:
        pass  # Perfect
    elif temp_mean < opt_min:
        score -= 0.3 * min(1, (opt_min - temp_mean) / 10)
    else:
        score -= 0.3 * min(1, (temp_mean - opt_max) / 10)
    
    return max(0, score)

def calculate_water_match(crop_name, precipitation_mm):
    """Calculate water availability match"""
    crop = get_crop_info(crop_name)
    if not crop:
        return 0.5
    
    water_need = crop["water_need_mm"]
    drought_sens = DROUGHT_SENSITIVITY_SCORES.get(crop["drought_sensitivity"], 0.5)
    
    if precipitation_mm >= water_need:
        return 1.0
    else:
        ratio = precipitation_mm / water_need
        # Drought-tolerant crops handle low water better
        return ratio + (1 - drought_sens) * (1 - ratio) * 0.5

def calculate_ndvi_score(crop_name, ndvi_mean, ndvi_max):
    """Calculate NDVI-based vegetation potential score"""
    crop = get_crop_info(crop_name)
    if not crop:
        return 0.5
    
    ndvi_min_required = crop["ndvi_healthy_min"]
    
    # Use max NDVI as indicator of land potential during growing season
    if ndvi_max >= ndvi_min_required + 0.2:
        return 1.0
    elif ndvi_max >= ndvi_min_required:
        return 0.8
    elif ndvi_max >= ndvi_min_required * 0.7:
        return 0.6
    else:
        return 0.3 + ndvi_max

def calculate_risk_score(row, crop_name):
    """Calculate overall risk score for a location-crop pair"""
    crop = get_crop_info(crop_name)
    if not crop:
        return 50
    
    # Component scores
    region_score = calculate_region_suitability(crop_name, row["region"])
    temp_score = calculate_temp_match(
        crop_name, 
        row["lst_mean_c"], 
        row["lst_max_c"], 
        row["lst_min_c"]
    )
    water_score = calculate_water_match(crop_name, row["precipitation_annual_mm"])
    ndvi_score = calculate_ndvi_score(crop_name, row["ndvi_mean"], row["ndvi_max"])
    
    # Weighted combination
    base_score = (
        0.20 * region_score +
        0.25 * temp_score +
        0.30 * water_score +
        0.25 * ndvi_score
    )
    
    # Add realistic noise
    noise = np.random.normal(0, 0.02)
    final_score = np.clip(base_score + noise, 0, 1)
    
    return round(final_score * 100, 1)

def generate_training_data(satellite_df):
    """Generate training data combining satellite data with all crops"""
    all_crops = get_all_crops()
    rows = []
    
    print(f"Generating training data for {len(satellite_df)} locations x {len(all_crops)} crops...")
    
    for _, loc_row in satellite_df.iterrows():
        # Skip if missing critical data
        if pd.isna(loc_row["ndvi_mean"]) or pd.isna(loc_row["lst_mean_c"]):
            continue
        
        for crop_name in all_crops:
            crop = get_crop_info(crop_name)
            risk_score = calculate_risk_score(loc_row, crop_name)
            
            if risk_score >= 70:
                risk_category = "green"
            elif risk_score >= 40:
                risk_category = "yellow"
            else:
                risk_category = "red"
            
            row = {
                # Location
                "region": loc_row["region"],
                "district": loc_row["district"],
                "latitude": loc_row["latitude"],
                "longitude": loc_row["longitude"],
                
                # Satellite data (real)
                "ndvi_mean": loc_row["ndvi_mean"],
                "ndvi_max": loc_row["ndvi_max"],
                "ndvi_min": loc_row["ndvi_min"],
                "ndvi_std": loc_row["ndvi_std"],
                "lst_mean_c": loc_row["lst_mean_c"],
                "lst_max_c": loc_row["lst_max_c"],
                "lst_min_c": loc_row["lst_min_c"],
                "precipitation_annual_mm": loc_row["precipitation_annual_mm"],
                
                # Crop info
                "crop": crop_name,
                "crop_category": crop["category"],
                "crop_temp_min": crop["optimal_temp_min"],
                "crop_temp_max": crop["optimal_temp_max"],
                "crop_water_need": crop["water_need_mm"],
                "crop_ndvi_min": crop["ndvi_healthy_min"],
                "crop_drought_sens": DROUGHT_SENSITIVITY_SCORES.get(crop["drought_sensitivity"], 0.5),
                "crop_frost_sens": FROST_SENSITIVITY_SCORES.get(crop["frost_sensitivity"], 0.5),
                
                # Computed features
                "region_suitable": calculate_region_suitability(crop_name, loc_row["region"]),
                "temp_match": calculate_temp_match(crop_name, loc_row["lst_mean_c"], loc_row["lst_max_c"], loc_row["lst_min_c"]),
                "water_match": calculate_water_match(crop_name, loc_row["precipitation_annual_mm"]),
                "ndvi_score": calculate_ndvi_score(crop_name, loc_row["ndvi_mean"], loc_row["ndvi_max"]),
                
                # Target
                "risk_score": risk_score,
                "risk_category": risk_category,
            }
            rows.append(row)
    
    df = pd.DataFrame(rows)
    print(f"Generated {len(df)} training samples")
    return df

def save_training_data(df, output_dir="data/processed"):
    """Save training data"""
    output_path = Path(__file__).parent.parent / output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_path / "training_data_real.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path}")
    
    return csv_path


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent.parent)
    
    # Load satellite data
    satellite_df = load_satellite_data()
    
    print(f"\n{'='*50}")
    print("SATELLITE DATA SUMMARY")
    print(f"{'='*50}")
    print(f"Locations: {len(satellite_df)}")
    print(f"NDVI mean range: {satellite_df['ndvi_mean'].min():.3f} - {satellite_df['ndvi_mean'].max():.3f}")
    print(f"NDVI max range:  {satellite_df['ndvi_max'].min():.3f} - {satellite_df['ndvi_max'].max():.3f}")
    print(f"Temp mean range: {satellite_df['lst_mean_c'].min():.1f}°C - {satellite_df['lst_mean_c'].max():.1f}°C")
    print(f"Temp extremes:   {satellite_df['lst_min_c'].min():.1f}°C - {satellite_df['lst_max_c'].max():.1f}°C")
    print(f"Precip range:    {satellite_df['precipitation_annual_mm'].min():.0f} - {satellite_df['precipitation_annual_mm'].max():.0f} mm/year")
    
    # Generate training data
    print(f"\n{'='*50}")
    print("GENERATING TRAINING DATA")
    print(f"{'='*50}")
    training_df = generate_training_data(satellite_df)
    
    # Save
    save_training_data(training_df)
    
    # Summary
    print(f"\n{'='*50}")
    print("TRAINING DATA SUMMARY")
    print(f"{'='*50}")
    print(f"Total samples: {len(training_df)}")
    print(f"\nRisk category distribution:")
    print(training_df["risk_category"].value_counts())
    print(f"\nMean risk score by crop:")
    print(training_df.groupby("crop")["risk_score"].mean().sort_values(ascending=False).round(1))
    print(f"\nMean risk score by region (top 10):")
    print(training_df.groupby("region")["risk_score"].mean().sort_values(ascending=False).head(10).round(1))