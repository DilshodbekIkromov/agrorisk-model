"""
Flask Backend for AgroRisk Copilot
Provides REST API with database persistence and PDF generation
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sys
import os
import json
import numpy as np
from pathlib import Path

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def safe_json_dumps(obj):
    return json.dumps(obj, cls=NumpyEncoder)

# Add project paths
project_root = Path(__file__).parent.parent
FRONTEND_DIR = project_root / "frontend"
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root / "data" / "raw"))
# Add backend to path so we can import models
sys.path.append(str(Path(__file__).parent))

from models import db, Farmer, RiskAssessment, LoanApplication, CreditDecision
from ml_service import MLService
from pdf_generator import generate_loan_pdf

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agrorisk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False

# Initialize database
db.init_app(app)

# Initialize ML service
ml_service = MLService()

# Create tables within app context
with app.app_context():
    db.create_all()
    print("✅ Database tables created")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": ml_service.model is not None,
        "database": "connected"
    })


@app.route('/api/regions', methods=['GET'])
def get_regions():
    """Get all available regions"""
    from uzbekistan_geography import get_all_regions
    return jsonify({"regions": get_all_regions()})


@app.route('/api/districts/<region>', methods=['GET'])
def get_districts(region):
    """Get districts for a region"""
    from uzbekistan_geography import get_districts
    districts = get_districts(region)
    if not districts:
        return jsonify({"error": f"Region '{region}' not found"}), 404
    return jsonify({"region": region, "districts": districts})


@app.route('/api/crops', methods=['GET'])
def get_crops():
    """Get all available crops"""
    from crops_database import CROPS
    crops_list = []
    for name, info in CROPS.items():
        crops_list.append({
            "name": name,
            "name_uz": info["name_uz"],
            "category": info["category"],
            "growing_season": f"{info['growing_season_start']}-{info['growing_season_end']}",
            "water_need_mm": info["water_need_mm"],
        })
    return jsonify({"crops": crops_list})


@app.route('/api/predict', methods=['POST'])
def predict_risk():
    """
    Predict crop risk and save to database
    
    Request body:
    {
        "region": "Tashkent City",
        "district": "Chilanzar",
        "crop": "wheat",
        "farmer_id": 1  // optional, if already exists
    }
    """
    try:
        data = request.json
        region = data.get('region')
        district = data.get('district')
        crop = data.get('crop')
        farmer_id = data.get('farmer_id')
        
        if not all([region, district, crop]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Get prediction from ML service
        result = ml_service.predict_risk(region, district, crop)
        
        if result.get('error'):
            return jsonify({"error": result['error']}), 500
        
        # Save to database
        assessment = RiskAssessment(
            farmer_id=farmer_id,
            region=region,
            district=district,
            crop=crop,
            risk_score=result['risk_score'],
            risk_category=result['risk_category'],
            confidence=result['confidence'],
            top_factors=safe_json_dumps(result['top_factors']),
            location_info=safe_json_dumps(result['location_info']),
            crop_info=safe_json_dumps(result['crop_info']),
            recommendations=safe_json_dumps(result['recommendations'])
        )
        
        db.session.add(assessment)
        db.session.commit()
        
        result['assessment_id'] = assessment.id
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in predict_risk: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/batch-predict', methods=['GET'])
def batch_predict():
    """Get risk predictions for all districts in a region"""
    region = request.args.get('region')
    crop = request.args.get('crop')
    
    if not region or not crop:
        return jsonify({"error": "Missing region or crop"}), 400
        
    from uzbekistan_geography import get_districts, get_coordinates
    districts = get_districts(region)
    
    if not districts:
        return jsonify({"error": "Region not found"}), 404
        
    results = []
    for district_name in districts:
        try:
            coords = get_coordinates(region, district_name)
            # We don't save batch predictions to DB to avoid clutter
            result = ml_service.predict_risk(region, district_name, crop)
            if not result.get('error'):
                results.append({
                    "district": district_name,
                    "latitude": coords[0],
                    "longitude": coords[1],
                    "risk_score": result['risk_score'],
                    "risk_category": result['risk_category']
                })
        except Exception as e:
            print(f"Error predicting for {district_name}: {e}")
            
    return jsonify({"region": region, "crop": crop, "districts": results})


@app.route('/api/loan/submit', methods=['POST'])
def submit_loan():
    """
    Submit loan application and get credit decision
    
    Request body:
    {
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
    """
    try:
        data = request.json
        
        # Validate required fields
        required = ['assessment_id', 'farmer_name', 'passport_id', 'phone', 
                   'loan_amount', 'annual_revenue', 'net_profit', 'total_assets']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
        
        # Get or create farmer
        farmer = Farmer.query.filter_by(passport_id=data['passport_id']).first()
        if not farmer:
            farmer = Farmer(
                name=data['farmer_name'],
                passport_id=data['passport_id'],
                phone=data['phone']
            )
            db.session.add(farmer)
            db.session.flush()
        
        # Get risk assessment
        assessment = RiskAssessment.query.get(data['assessment_id'])
        if not assessment:
            return jsonify({"error": "Assessment not found"}), 404
        
        # Link farmer to assessment if not already linked
        if not assessment.farmer_id:
            assessment.farmer_id = farmer.id
        
        # Create loan application
        application = LoanApplication(
            farmer_id=farmer.id,
            assessment_id=assessment.id,
            loan_amount=data['loan_amount'],
            loan_term=data.get('loan_term', 12),
            land_area=data.get('land_area', 0),
            land_ownership=data.get('land_ownership', 'unknown'),
            years_farming=data.get('years_farming', 0),
            annual_revenue=data['annual_revenue'],
            net_profit=data['net_profit'],
            total_assets=data['total_assets'],
            total_debt=data.get('total_debt', 0),
            collateral_value=data.get('collateral_value', 0),
            previous_defaults=data.get('previous_defaults', False)
        )
        
        db.session.add(application)
        db.session.flush()
        
        # Calculate financial score
        agro_score = assessment.risk_score
        fin_score = ml_service.calculate_financial_score(
            loan_amount=application.loan_amount,
            revenue=application.annual_revenue,
            profit=application.net_profit,
            assets=application.total_assets,
            debt=application.total_debt,
            collateral=application.collateral_value,
            defaults=application.previous_defaults,
            years_farming=application.years_farming,
            ownership=application.land_ownership
        )
        
        # Calculate final credit score (40% agro, 60% financial)
        final_score = round(agro_score * 0.4 + fin_score * 0.6)
        
        # Determine decision
        if final_score >= 70:
            decision = "APPROVED"
        elif final_score >= 50:
            decision = "MANUAL_REVIEW"
        else:
            decision = "REJECTED"
        
        # Calculate factors
        debt_to_asset = (application.total_debt + application.loan_amount) / max(application.total_assets, 1)
        profit_margin = application.net_profit / max(application.annual_revenue, 1)
        collateral_coverage = application.collateral_value / max(application.loan_amount, 1)
        
        factors = {
            "debt_to_asset_ratio": round(debt_to_asset * 100, 1),
            "profit_margin": round(profit_margin * 100, 1),
            "collateral_coverage": round(collateral_coverage * 100, 1)
        }
        
        # Create credit decision
        credit_decision = CreditDecision(
            application_id=application.id,
            agro_score=agro_score,
            financial_score=fin_score,
            final_score=final_score,
            decision=decision,
            decision_factors=safe_json_dumps(factors)
        )
        
        db.session.add(credit_decision)
        db.session.commit()
        
        return jsonify({
            "application_id": application.id,
            "decision_id": credit_decision.id,
            "farmer_id": farmer.id,
            "agro_score": agro_score,
            "financial_score": fin_score,
            "final_score": final_score,
            "decision": decision,
            "factors": factors,
            "created_at": credit_decision.created_at.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in submit_loan: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/loan/download/<int:application_id>', methods=['GET'])
def download_report(application_id):
    """Generate and download PDF report for loan application"""
    try:
        application = LoanApplication.query.get(application_id)
        if not application:
            return jsonify({"error": "Application not found"}), 404
        
        # Generate PDF
        pdf_path = generate_loan_pdf(application)
        
        # Return file for download
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"agrorisk_loan_{application_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve the built frontend (SPA) from /frontend"""
    # Let API and health routes be handled by Flask handlers
    if path.startswith('api') or path == 'health':
        return jsonify({"error": "Not Found"}), 404

    full_path = FRONTEND_DIR / path
    if path and full_path.exists():
        return send_from_directory(FRONTEND_DIR, path)
    # Fallback to index.html for SPA routes
    return send_from_directory(FRONTEND_DIR, 'index.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002, use_reloader=False)
