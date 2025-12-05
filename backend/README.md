# AgroRisk Copilot - Flask Backend

Production-ready Flask backend with SQLite database persistence and PDF report generation.

## Features

- **REST API** for crop risk assessment and loan applications
- **SQLite Database** with SQLAlchemy ORM (farmers, assessments, loans, decisions)
- **ML Integration** using trained LightGBM model from `models/`
- **PDF Reports** with ReportLab (farmer profile, risk assessment, financial analysis, decision rationale)
- **CORS enabled** for frontend integration

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Initialize Database

The database will be automatically created on first request to `agrorisk.db` in the backend folder.

### 3. Start Flask Server

```bash
python app.py
```

Server runs on `http://localhost:5000`

## API Endpoints

### Health Check
```
GET /health
```

### Geography
```
GET /api/regions
GET /api/districts/<region>
GET /api/crops
```

### Crop Risk Assessment
```
POST /api/predict
Body: {
    "region": "Tashkent City",
    "district": "Chilanzar",
    "crop": "wheat",
    "farmer_id": 1  // optional
}
```

Returns risk score, category, top factors, recommendations, and `assessment_id`.

### Loan Application
```
POST /api/loan/submit
Body: {
    "assessment_id": 1,
    "farmer_name": "Alisher Karimov",
    "passport_id": "AA1234567",
    "phone": "+998901234567",
    "years_farming": 5,
    "land_area": 10.5,
    "land_ownership": "owned",
    "loan_amount": 50000000,
    "loan_term": 12,
    "annual_revenue": 120000000,
    "net_profit": 30000000,
    "total_assets": 200000000,
    "total_debt": 0,
    "collateral_value": 60000000,
    "previous_defaults": false
}
```

Returns credit decision with `application_id`.

### PDF Download
```
GET /api/loan/download/<application_id>
```

Downloads professional PDF report with all assessment details.

## Database Schema

### Farmers
- id, name, passport_id (unique), phone, created_at

### RiskAssessments
- id, farmer_id, region, district, crop
- risk_score, risk_category, confidence
- top_factors (JSON), location_info (JSON), crop_info (JSON)
- created_at

### LoanApplications
- id, farmer_id, assessment_id
- loan_amount, loan_term, land_area, land_ownership
- annual_revenue, net_profit, total_assets, total_debt, collateral_value
- previous_defaults, years_farming
- created_at

### CreditDecisions
- id, application_id
- agro_score, financial_score, final_score
- decision (APPROVED/MANUAL_REVIEW/REJECTED)
- decision_factors (JSON with ratios)
- created_at

## Credit Scoring Logic

**Final Score = (Agro Risk × 0.4) + (Financial Health × 0.6)**

### Financial Score Calculation (0-100)
- Base: 70
- Debt-to-Asset > 0.7: -30
- Debt-to-Asset > 0.5: -15
- Profit Margin < 10%: -10
- Profit Margin > 30%: +10
- Collateral < 100%: -20
- Collateral > 150%: +10
- Previous Defaults: -50
- < 2 years farming: -10
- Leased land (short): -10

### Decision Thresholds
- ≥ 70: APPROVED
- 50-69: MANUAL_REVIEW
- < 50: REJECTED

## PDF Report Contents

1. **Header**: Logo, title, application metadata
2. **Farmer Profile**: Name, passport, phone, experience, land
3. **Crop Risk Assessment**: Score, category, location, top 5 factors
4. **Financial Analysis**: Revenue, profit, assets, debt, collateral, key ratios
5. **Final Decision**: Agro/financial/combined scores, decision with color
6. **Rationale**: Detailed explanation of why approved/rejected

## Development

- Models defined in `models.py` (SQLAlchemy)
- ML service in `ml_service.py` (wraps trained model)
- PDF generator in `pdf_generator.py` (ReportLab)
- Main app in `app.py` (Flask routes)

## Production Notes

- For production, replace SQLite with PostgreSQL
- Add authentication/authorization for loan officers
- Configure CORS properly (not `allow_origins=["*"]`)
- Use environment variables for config
- Add logging and monitoring
- Deploy with Gunicorn/uWSGI behind Nginx

## Testing

```bash
# Health check
curl http://localhost:5000/health

# Get regions
curl http://localhost:5000/api/regions

# Predict risk
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"region":"Tashkent City","district":"Chilanzar","crop":"wheat"}'

# Submit loan (use assessment_id from previous response)
curl -X POST http://localhost:5000/api/loan/submit \
  -H "Content-Type: application/json" \
  -d '{"assessment_id":1,"farmer_name":"Test Farmer",...}'
```
