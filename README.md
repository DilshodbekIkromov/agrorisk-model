# AgroRisk Copilot - Agricultural Risk Model

AI-powered crop risk assessment for Uzbekistan's agricultural sector.

## 🎯 What It Does

Given a **Region + District + Crop**, the model returns:
- **Risk Score (0-100)**: Higher = better conditions, lower risk
- **Traffic Light Category**: 🟢 Green (70-100), 🟡 Yellow (40-69), 🔴 Red (0-39)
- **SHAP Explanations**: Why this score? Top 5 contributing factors
- **Alternative Crops**: Better options for current conditions

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER INPUT                          │
│            Region → District → Crop → (Month)               │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   SATELLITE DATA ENGINE                     │
│  • Google Earth Engine (NDVI, LST, precipitation)           │
│  • Real-time weather forecast (Open-Meteo API)              │
│  • Historical climate averages from satellite               │
│  • Soil moisture estimates                                  │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     FEATURE ENGINEERING                     │
│  • 28 engineered features                                   │
│  • Climate-crop matching scores                             │
│  • Region/season suitability flags                          │
│  • Drought/frost risk indicators                            │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LightGBM MODEL + SHAP                    │
│  • Trained on real satellite data                           │
│  • 180 locations × 15 crops × 8 months                      │
│  • TreeSHAP for instant explanations                        │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                          OUTPUT                             │
│  {                                                          │
│    "risk_score": 85.7,                                      │
│    "risk_category": "green",                                │
│    "top_factors": [...],                                    │
│    "recommendations": [...]                                 │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
agrorisk-model/
├── data/
│   ├── raw/
│   │   ├── uzbekistan_geography.py      # 180 districts with coordinates
│   │   ├── crops_database.py            # 15 crops with requirements
│   │   ├── satellite_data.csv           # Real satellite metrics (GEE)
│   │   └── uzbekistan_climate_data.csv
│   └── processed/
│       └── training_data_real.csv       # Processed training data
├── models/
│   ├── agrorisk_model.joblib            # Trained LightGBM model
│   ├── agrorisk_model.txt               # Model summary
│   └── model_metadata.json              # Feature info & encoders
├── src/
│   ├── gee_fetcher.py                   # Google Earth Engine integration
│   ├── climate_fetcher.py               # Real-time weather API
│   ├── feature_engineering.py           # Feature generation module
│   └── model_training.py                # LightGBM + SHAP training
├── notebooks/
│   ├── 01_data_exploration.ipynb        # Explore satellite data
│   ├── 02_feature_engineering.ipynb     # Feature generation pipeline
│   ├── 03_training_data_generation.ipynb
│   ├── 04_model_training.ipynb          # Train LightGBM with Optuna
│   └── 05_prediction_testing.ipynb      # Test predictions & visualizations
├── api/
│   └── main.py                          # FastAPI application
├── requirements.txt
└── test_pipeline.py                     # End-to-end tests
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the API
```bash
cd agrorisk-model
uvicorn api.main:app --reload --port 8000
```

### 3. Test Prediction
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"region": "Tashkent Region", "district": "Chirchiq", "crop": "cotton"}'
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | POST | Get risk prediction with explanations |
| `/regions` | GET | List all 14 regions |
| `/districts/{region}` | GET | List districts in a region |
| `/crops` | GET | List all 15 supported crops |
| `/crops/{region}` | GET | Get suitable crops for a region |
| `/batch-predict` | GET | Predict for all districts (heatmap) |

### Prediction Request
```json
{
  "region": "Samarkand",
  "district": "Samarkand City",
  "crop": "grape",
  "month": 6
}
```

### Prediction Response
```json
{
  "risk_score": 85.7,
  "risk_category": "green",
  "confidence": "high",
  "top_factors": [
    {"feature": "region_suitable", "contribution": 4.96, "direction": "increases"},
    {"feature": "ndvi_current", "contribution": 2.74, "direction": "increases"}
  ],
  "recommendations": [
    {"crop": "chickpea", "risk_score": 87.9, "risk_category": "green"},
    {"crop": "onion", "risk_score": 87.0, "risk_category": "green"}
  ],
  "location_info": {
    "climate_zone": "central",
    "current_conditions": {
      "temperature": 28.5,
      "soil_moisture": 0.32,
      "ndvi": 0.547
    }
  }
}
```

## 🌾 Supported Crops

| Crop | Uzbek Name | Category | Water Need |
|------|------------|----------|------------|
| cotton | Paxta | industrial | 700mm |
| wheat | Bug'doy | grain | 450mm |
| rice | Sholi | grain | 1200mm |
| corn | Makkajo'xori | grain | 500mm |
| grape | Uzum | fruit | 500mm |
| melon | Qovun | fruit | 400mm |
| tomato | Pomidor | vegetable | 600mm |
| potato | Kartoshka | vegetable | 500mm |
| onion | Piyoz | vegetable | 350mm |
| ... | ... | ... | ... |

## 🗺️ Coverage

- **14 Regions** (Viloyatlar)
- **180 Districts** (Tumanlar)
- **6 Climate Zones**: Fergana Valley, Tashkent, Central, Southern, Western, Desert

## 🔬 Model Performance

| Metric | Value |
|--------|-------|
| R² Score | 0.859 |
| RMSE | 5.60 |
| MAE | 4.51 |
| Training Samples | 7,200 |

### Top Feature Importance
1. Historical Soil Moisture
2. Region Suitability
3. Season Suitability
4. Current Temperature
5. NDVI (Vegetation Health)

## 🔄 Using Real Weather Data

The synthetic data generator creates realistic climate patterns. To use real weather data:

1. Uncomment the Open-Meteo API calls in `src/climate_fetcher.py`
2. The API is free and doesn't require a key
3. Run `python src/climate_fetcher.py` to fetch real data

## 🚢 Deployment

### Railway/Render
```bash
# Procfile
web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📊 Frontend Integration

The API returns JSON that's ready for your Next.js dashboard:

```typescript
// Example: Traffic light component
const TrafficLight = ({ category }: { category: string }) => {
  const colors = {
    green: 'bg-green-500',
    yellow: 'bg-yellow-500', 
    red: 'bg-red-500'
  };
  return <div className={`w-4 h-4 rounded-full ${colors[category]}`} />;
};
```

## 📝 License

MIT License - Built for Agrobank Hackathon 2024
