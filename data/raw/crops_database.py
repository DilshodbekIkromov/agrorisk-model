"""
Crop Requirements Database for Uzbekistan Agriculture

Each crop has optimal growing conditions that we'll match against:
- Satellite data (NDVI, soil moisture, land surface temperature)
- Weather forecasts
- Seasonal timing

These parameters are based on agricultural research and FAO guidelines.
"""

CROPS = {
    "cotton": {
        "name_uz": "Paxta",
        "category": "industrial",
        "optimal_temp_min": 20,
        "optimal_temp_max": 35,
        "critical_temp_min": 15,
        "critical_temp_max": 40,
        "water_need_mm": 700,
        "growing_season_start": 4,  # April
        "growing_season_end": 10,   # October
        "growing_days": 150,
        "soil_moisture_min": 0.3,
        "soil_moisture_optimal": 0.5,
        "ndvi_healthy_min": 0.4,
        "drought_sensitivity": "medium",
        "frost_sensitivity": "high",
        "suitable_regions": ["Tashkent Region", "Fergana", "Andijan", "Namangan", "Sirdaryo", "Jizzakh", "Kashkadarya", "Surkhandarya", "Bukhara", "Khorezm"],
    },
    "wheat": {
        "name_uz": "Bug'doy",
        "category": "grain",
        "optimal_temp_min": 12,
        "optimal_temp_max": 25,
        "critical_temp_min": -5,
        "critical_temp_max": 35,
        "water_need_mm": 450,
        "growing_season_start": 10, # October (winter wheat)
        "growing_season_end": 6,    # June
        "growing_days": 240,
        "soil_moisture_min": 0.25,
        "soil_moisture_optimal": 0.4,
        "ndvi_healthy_min": 0.35,
        "drought_sensitivity": "low",
        "frost_sensitivity": "low",
        "suitable_regions": ["all"],
    },
    "rice": {
        "name_uz": "Sholi",
        "category": "grain",
        "optimal_temp_min": 22,
        "optimal_temp_max": 32,
        "critical_temp_min": 15,
        "critical_temp_max": 38,
        "water_need_mm": 1200,
        "growing_season_start": 5,  # May
        "growing_season_end": 9,    # September
        "growing_days": 120,
        "soil_moisture_min": 0.6,
        "soil_moisture_optimal": 0.8,
        "ndvi_healthy_min": 0.45,
        "drought_sensitivity": "very_high",
        "frost_sensitivity": "high",
        "suitable_regions": ["Tashkent Region", "Fergana", "Khorezm", "Karakalpakstan"],
    },
    "corn": {
        "name_uz": "Makkajo'xori",
        "category": "grain",
        "optimal_temp_min": 18,
        "optimal_temp_max": 30,
        "critical_temp_min": 10,
        "critical_temp_max": 38,
        "water_need_mm": 500,
        "growing_season_start": 4,  # April
        "growing_season_end": 9,    # September
        "growing_days": 100,
        "soil_moisture_min": 0.35,
        "soil_moisture_optimal": 0.5,
        "ndvi_healthy_min": 0.4,
        "drought_sensitivity": "medium",
        "frost_sensitivity": "high",
        "suitable_regions": ["all"],
    },
    "tomato": {
        "name_uz": "Pomidor",
        "category": "vegetable",
        "optimal_temp_min": 18,
        "optimal_temp_max": 27,
        "critical_temp_min": 10,
        "critical_temp_max": 35,
        "water_need_mm": 600,
        "growing_season_start": 4,
        "growing_season_end": 9,
        "growing_days": 90,
        "soil_moisture_min": 0.4,
        "soil_moisture_optimal": 0.6,
        "ndvi_healthy_min": 0.35,
        "drought_sensitivity": "high",
        "frost_sensitivity": "high",
        "suitable_regions": ["Tashkent Region", "Samarkand", "Fergana", "Surkhandarya"],
    },
    "melon": {
        "name_uz": "Qovun",
        "category": "fruit",
        "optimal_temp_min": 24,
        "optimal_temp_max": 35,
        "critical_temp_min": 15,
        "critical_temp_max": 42,
        "water_need_mm": 400,
        "growing_season_start": 5,
        "growing_season_end": 9,
        "growing_days": 85,
        "soil_moisture_min": 0.25,
        "soil_moisture_optimal": 0.4,
        "ndvi_healthy_min": 0.3,
        "drought_sensitivity": "low",
        "frost_sensitivity": "high",
        "suitable_regions": ["Bukhara", "Samarkand", "Khorezm", "Kashkadarya", "Surkhandarya", "Navoiy"],
    },
    "watermelon": {
        "name_uz": "Tarvuz",
        "category": "fruit",
        "optimal_temp_min": 24,
        "optimal_temp_max": 35,
        "critical_temp_min": 15,
        "critical_temp_max": 40,
        "water_need_mm": 450,
        "growing_season_start": 5,
        "growing_season_end": 9,
        "growing_days": 80,
        "soil_moisture_min": 0.25,
        "soil_moisture_optimal": 0.4,
        "ndvi_healthy_min": 0.3,
        "drought_sensitivity": "low",
        "frost_sensitivity": "high",
        "suitable_regions": ["all"],
    },
    "grape": {
        "name_uz": "Uzum",
        "category": "fruit",
        "optimal_temp_min": 15,
        "optimal_temp_max": 30,
        "critical_temp_min": -15,
        "critical_temp_max": 38,
        "water_need_mm": 500,
        "growing_season_start": 4,
        "growing_season_end": 10,
        "growing_days": 150,
        "soil_moisture_min": 0.3,
        "soil_moisture_optimal": 0.45,
        "ndvi_healthy_min": 0.35,
        "drought_sensitivity": "medium",
        "frost_sensitivity": "medium",
        "suitable_regions": ["Samarkand", "Bukhara", "Tashkent Region", "Fergana", "Surkhandarya"],
    },
    "apple": {
        "name_uz": "Olma",
        "category": "fruit",
        "optimal_temp_min": 10,
        "optimal_temp_max": 25,
        "critical_temp_min": -25,
        "critical_temp_max": 35,
        "water_need_mm": 600,
        "growing_season_start": 3,
        "growing_season_end": 10,
        "growing_days": 180,
        "soil_moisture_min": 0.35,
        "soil_moisture_optimal": 0.5,
        "ndvi_healthy_min": 0.4,
        "drought_sensitivity": "medium",
        "frost_sensitivity": "low",
        "suitable_regions": ["Tashkent Region", "Samarkand", "Fergana", "Namangan"],
    },
    "potato": {
        "name_uz": "Kartoshka",
        "category": "vegetable",
        "optimal_temp_min": 15,
        "optimal_temp_max": 22,
        "critical_temp_min": 5,
        "critical_temp_max": 30,
        "water_need_mm": 500,
        "growing_season_start": 3,
        "growing_season_end": 9,
        "growing_days": 100,
        "soil_moisture_min": 0.4,
        "soil_moisture_optimal": 0.6,
        "ndvi_healthy_min": 0.35,
        "drought_sensitivity": "high",
        "frost_sensitivity": "medium",
        "suitable_regions": ["Tashkent Region", "Samarkand", "Jizzakh", "Fergana"],
    },
    "onion": {
        "name_uz": "Piyoz",
        "category": "vegetable",
        "optimal_temp_min": 12,
        "optimal_temp_max": 25,
        "critical_temp_min": -5,
        "critical_temp_max": 35,
        "water_need_mm": 350,
        "growing_season_start": 3,
        "growing_season_end": 8,
        "growing_days": 120,
        "soil_moisture_min": 0.3,
        "soil_moisture_optimal": 0.5,
        "ndvi_healthy_min": 0.3,
        "drought_sensitivity": "medium",
        "frost_sensitivity": "low",
        "suitable_regions": ["all"],
    },
    "carrot": {
        "name_uz": "Sabzi",
        "category": "vegetable",
        "optimal_temp_min": 15,
        "optimal_temp_max": 22,
        "critical_temp_min": 5,
        "critical_temp_max": 30,
        "water_need_mm": 400,
        "growing_season_start": 3,
        "growing_season_end": 10,
        "growing_days": 90,
        "soil_moisture_min": 0.35,
        "soil_moisture_optimal": 0.55,
        "ndvi_healthy_min": 0.3,
        "drought_sensitivity": "medium",
        "frost_sensitivity": "low",
        "suitable_regions": ["all"],
    },
    "alfalfa": {
        "name_uz": "Beda",
        "category": "fodder",
        "optimal_temp_min": 15,
        "optimal_temp_max": 30,
        "critical_temp_min": -10,
        "critical_temp_max": 38,
        "water_need_mm": 800,
        "growing_season_start": 3,
        "growing_season_end": 10,
        "growing_days": 200,
        "soil_moisture_min": 0.3,
        "soil_moisture_optimal": 0.5,
        "ndvi_healthy_min": 0.4,
        "drought_sensitivity": "low",
        "frost_sensitivity": "low",
        "suitable_regions": ["all"],
    },
    "chickpea": {
        "name_uz": "No'xat",
        "category": "legume",
        "optimal_temp_min": 15,
        "optimal_temp_max": 28,
        "critical_temp_min": 5,
        "critical_temp_max": 35,
        "water_need_mm": 300,
        "growing_season_start": 3,
        "growing_season_end": 7,
        "growing_days": 100,
        "soil_moisture_min": 0.2,
        "soil_moisture_optimal": 0.35,
        "ndvi_healthy_min": 0.25,
        "drought_sensitivity": "very_low",
        "frost_sensitivity": "medium",
        "suitable_regions": ["Kashkadarya", "Surkhandarya", "Jizzakh", "Samarkand"],
    },
    "sunflower": {
        "name_uz": "Kungaboqar",
        "category": "industrial",
        "optimal_temp_min": 18,
        "optimal_temp_max": 30,
        "critical_temp_min": 5,
        "critical_temp_max": 38,
        "water_need_mm": 450,
        "growing_season_start": 4,
        "growing_season_end": 9,
        "growing_days": 110,
        "soil_moisture_min": 0.25,
        "soil_moisture_optimal": 0.4,
        "ndvi_healthy_min": 0.35,
        "drought_sensitivity": "low",
        "frost_sensitivity": "high",
        "suitable_regions": ["Tashkent Region", "Jizzakh", "Sirdaryo", "Samarkand"],
    },
}

DROUGHT_SENSITIVITY_SCORES = {
    "very_low": 0.1,
    "low": 0.3,
    "medium": 0.5,
    "high": 0.7,
    "very_high": 0.9,
}

FROST_SENSITIVITY_SCORES = {
    "low": 0.2,
    "medium": 0.5,
    "high": 0.8,
}

def get_all_crops():
    return list(CROPS.keys())

def get_crop_info(crop_name):
    return CROPS.get(crop_name.lower())

def get_crops_by_category(category):
    return [name for name, info in CROPS.items() if info["category"] == category]

def get_suitable_crops_for_region(region):
    suitable = []
    for crop_name, info in CROPS.items():
        if "all" in info["suitable_regions"] or region in info["suitable_regions"]:
            suitable.append(crop_name)
    return suitable

def calculate_temp_match_score(crop_name, temperature):
    """Calculate how well temperature matches crop requirements (0-1)"""
    crop = CROPS.get(crop_name.lower())
    if not crop:
        return 0
    
    opt_min = crop["optimal_temp_min"]
    opt_max = crop["optimal_temp_max"]
    crit_min = crop["critical_temp_min"]
    crit_max = crop["critical_temp_max"]
    
    if opt_min <= temperature <= opt_max:
        return 1.0
    elif temperature < crit_min or temperature > crit_max:
        return 0.0
    elif temperature < opt_min:
        return (temperature - crit_min) / (opt_min - crit_min)
    else:
        return (crit_max - temperature) / (crit_max - opt_max)

def calculate_moisture_match_score(crop_name, soil_moisture):
    """Calculate how well soil moisture matches crop requirements (0-1)"""
    crop = CROPS.get(crop_name.lower())
    if not crop:
        return 0
    
    min_moist = crop["soil_moisture_min"]
    opt_moist = crop["soil_moisture_optimal"]
    
    if soil_moisture >= opt_moist:
        return 1.0
    elif soil_moisture < min_moist:
        return max(0, soil_moisture / min_moist * 0.5)
    else:
        return 0.5 + 0.5 * (soil_moisture - min_moist) / (opt_moist - min_moist)

if __name__ == "__main__":
    print(f"Total crops: {len(CROPS)}")
    print("\nCrops by category:")
    for cat in ["grain", "industrial", "vegetable", "fruit", "legume", "fodder"]:
        crops = get_crops_by_category(cat)
        print(f"  {cat}: {', '.join(crops)}")
    
    print("\nSuitable crops for Samarkand:")
    print(f"  {', '.join(get_suitable_crops_for_region('Samarkand'))}")
    
    print("\nTemperature match for cotton at 28°C:", calculate_temp_match_score("cotton", 28))
    print("Temperature match for cotton at 45°C:", calculate_temp_match_score("cotton", 45))
