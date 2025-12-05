"""
Database models for AgroRisk Copilot
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class Farmer(db.Model):
    """Farmer profile"""
    __tablename__ = 'farmers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    passport_id = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    risk_assessments = db.relationship('RiskAssessment', backref='farmer', lazy=True)
    loan_applications = db.relationship('LoanApplication', backref='farmer', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'passport_id': self.passport_id,
            'phone': self.phone,
            'created_at': self.created_at.isoformat()
        }


class RiskAssessment(db.Model):
    """Crop risk assessment record"""
    __tablename__ = 'risk_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=True)
    
    region = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    crop = db.Column(db.String(50), nullable=False)
    
    risk_score = db.Column(db.Float, nullable=False)
    risk_category = db.Column(db.String(20), nullable=False)  # green/yellow/red
    confidence = db.Column(db.String(20))
    
    top_factors = db.Column(db.Text)  # JSON string
    location_info = db.Column(db.Text)  # JSON string
    crop_info = db.Column(db.Text)  # JSON string
    recommendations = db.Column(db.Text)  # JSON string
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    loan_applications = db.relationship('LoanApplication', backref='assessment', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'farmer_id': self.farmer_id,
            'region': self.region,
            'district': self.district,
            'crop': self.crop,
            'risk_score': self.risk_score,
            'risk_category': self.risk_category,
            'confidence': self.confidence,
            'top_factors': json.loads(self.top_factors) if self.top_factors else [],
            'location_info': json.loads(self.location_info) if self.location_info else {},
            'crop_info': json.loads(self.crop_info) if self.crop_info else {},
            'recommendations': json.loads(self.recommendations) if self.recommendations else [],
            'created_at': self.created_at.isoformat()
        }


class LoanApplication(db.Model):
    """Loan application record"""
    __tablename__ = 'loan_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey('risk_assessments.id'), nullable=False)
    
    loan_amount = db.Column(db.Float, nullable=False)
    loan_term = db.Column(db.Integer)  # months
    
    land_area = db.Column(db.Float)  # hectares
    land_ownership = db.Column(db.String(20))  # owned/leased_long/leased_short
    years_farming = db.Column(db.Integer)
    
    annual_revenue = db.Column(db.Float, nullable=False)
    net_profit = db.Column(db.Float, nullable=False)
    total_assets = db.Column(db.Float, nullable=False)
    total_debt = db.Column(db.Float)
    collateral_value = db.Column(db.Float)
    previous_defaults = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    credit_decision = db.relationship('CreditDecision', backref='application', uselist=False, lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'farmer_id': self.farmer_id,
            'assessment_id': self.assessment_id,
            'loan_amount': self.loan_amount,
            'loan_term': self.loan_term,
            'land_area': self.land_area,
            'land_ownership': self.land_ownership,
            'years_farming': self.years_farming,
            'annual_revenue': self.annual_revenue,
            'net_profit': self.net_profit,
            'total_assets': self.total_assets,
            'total_debt': self.total_debt,
            'collateral_value': self.collateral_value,
            'previous_defaults': self.previous_defaults,
            'created_at': self.created_at.isoformat()
        }


class CreditDecision(db.Model):
    """Credit decision record"""
    __tablename__ = 'credit_decisions'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('loan_applications.id'), nullable=False)
    
    agro_score = db.Column(db.Float, nullable=False)
    financial_score = db.Column(db.Float, nullable=False)
    final_score = db.Column(db.Float, nullable=False)
    
    decision = db.Column(db.String(20), nullable=False)  # APPROVED/MANUAL_REVIEW/REJECTED
    decision_factors = db.Column(db.Text)  # JSON string with ratios
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'agro_score': self.agro_score,
            'financial_score': self.financial_score,
            'final_score': self.final_score,
            'decision': self.decision,
            'decision_factors': json.loads(self.decision_factors) if self.decision_factors else {},
            'created_at': self.created_at.isoformat()
        }
