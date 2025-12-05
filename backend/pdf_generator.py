"""
PDF Report Generator for Loan Applications

Generates professional PDF reports with:
- Farmer profile
- Crop risk assessment
- Financial analysis
- Credit decision with rationale
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from pathlib import Path
import json
import tempfile


def generate_loan_pdf(application):
    """
    Generate PDF report for loan application
    
    Args:
        application: LoanApplication model instance with relationships loaded
    
    Returns:
        Path to generated PDF file
    """
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf_path = temp_file.name
    temp_file.close()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for PDF elements
    elements = []
    
    # Get related data
    farmer = application.farmer
    assessment = application.assessment
    decision = application.credit_decision
    
    # Parse JSON fields
    top_factors = json.loads(assessment.top_factors) if assessment.top_factors else []
    location_info = json.loads(assessment.location_info) if assessment.location_info else {}
    decision_factors = json.loads(decision.decision_factors) if decision.decision_factors else {}
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=16,
        fontName='Helvetica-Bold'
    )
    
    # ===== HEADER =====
    elements.append(Paragraph("🌾 AgroRisk Copilot", title_style))
    elements.append(Paragraph(
        "Agricultural Credit Assessment Report",
        subtitle_style
    ))
    elements.append(HRFlowable(
        width="100%",
        thickness=2,
        color=colors.HexColor('#ecf0f1'),
        spaceBefore=0,
        spaceAfter=20
    ))
    
    # Application metadata
    meta_data = [
        ["Application ID:", f"#{application.id}"],
        ["Report Date:", datetime.now().strftime("%B %d, %Y")],
        ["Assessment Date:", assessment.created_at.strftime("%B %d, %Y")],
    ]
    
    meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(meta_table)
    elements.append(Spacer(1, 20))
    
    # ===== FARMER PROFILE =====
    elements.append(Paragraph("Farmer Profile", heading_style))
    
    farmer_data = [
        ["Full Name:", farmer.name],
        ["Passport ID:", farmer.passport_id],
        ["Phone Number:", farmer.phone or "N/A"],
        ["Farming Experience:", f"{application.years_farming} years"],
        ["Land Area:", f"{application.land_area} hectares"],
        ["Land Ownership:", application.land_ownership.replace('_', ' ').title()],
    ]
    
    farmer_table = Table(farmer_data, colWidths=[2*inch, 4*inch])
    farmer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ecf0f1')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(farmer_table)
    elements.append(Spacer(1, 20))
    
    # ===== CROP RISK ASSESSMENT =====
    elements.append(Paragraph("Crop Risk Assessment", heading_style))
    
    # Risk score box
    risk_color = colors.HexColor('#27ae60') if assessment.risk_category == 'green' else \
                 colors.HexColor('#f39c12') if assessment.risk_category == 'yellow' else \
                 colors.HexColor('#c0392b')
    
    risk_status = "Low Risk" if assessment.risk_category == 'green' else \
                  "Medium Risk" if assessment.risk_category == 'yellow' else "High Risk"
    
    risk_data = [
        ["Location:", f"{assessment.region} / {assessment.district}"],
        ["Crop:", assessment.crop.title()],
        ["Risk Score:", f"{assessment.risk_score:.1f}/100"],
        ["Risk Level:", risk_status],
        ["Confidence:", assessment.confidence.title()],
    ]
    
    risk_table = Table(risk_data, colWidths=[2*inch, 4*inch])
    risk_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
        ('BACKGROUND', (0, 3), (-1, 3), risk_color),
        ('TEXTCOLOR', (0, 3), (-1, 3), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dfe6ee')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(risk_table)
    elements.append(Spacer(1, 12))
    
    # Top contributing factors
    if top_factors:
        elements.append(Paragraph("<b>Top Contributing Factors:</b>", styles['Normal']))
        elements.append(Spacer(1, 8))
        
        factor_rows = [["Factor", "Impact", "Direction"]]
        for factor in top_factors[:5]:
            factor_rows.append([
                factor['feature'].replace('_', ' ').title(),
                f"{factor['contribution']:+.2f}",
                "Increases" if factor['direction'] == 'increases' else "Decreases"
            ])
        
        factor_table = Table(factor_rows, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        factor_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dfe6ee')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(factor_table)
        elements.append(Spacer(1, 20))
    
    # ===== FINANCIAL ANALYSIS =====
    elements.append(Paragraph("Financial Analysis", heading_style))
    
    financial_data = [
        ["Loan Amount Requested:", f"{application.loan_amount:,.0f} UZS"],
        ["Loan Term:", f"{application.loan_term} months"],
        ["Annual Revenue:", f"{application.annual_revenue:,.0f} UZS"],
        ["Net Profit:", f"{application.net_profit:,.0f} UZS"],
        ["Total Assets:", f"{application.total_assets:,.0f} UZS"],
        ["Total Debt:", f"{application.total_debt:,.0f} UZS"],
        ["Collateral Value:", f"{application.collateral_value:,.0f} UZS"],
        ["Previous Defaults:", "Yes" if application.previous_defaults else "No"],
    ]
    
    financial_table = Table(financial_data, colWidths=[2.5*inch, 3.5*inch])
    financial_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ecf0f1')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(financial_table)
    elements.append(Spacer(1, 12))
    
    # Financial ratios
    elements.append(Paragraph("<b>Key Financial Ratios:</b>", styles['Normal']))
    elements.append(Spacer(1, 8))
    
    ratio_data = [
        ["Debt-to-Asset Ratio:", f"{decision_factors.get('debt_to_asset_ratio', 0):.1f}%"],
        ["Profit Margin:", f"{decision_factors.get('profit_margin', 0):.1f}%"],
        ["Collateral Coverage:", f"{decision_factors.get('collateral_coverage', 0):.1f}%"],
    ]
    
    ratio_table = Table(ratio_data, colWidths=[2.5*inch, 3.5*inch])
    ratio_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(ratio_table)
    elements.append(Spacer(1, 30))
    
    # ===== CREDIT DECISION =====
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#ecf0f1')))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Final Credit Decision", heading_style))
    
    # Decision box
    decision_color = colors.HexColor('#27ae60') if decision.decision == 'APPROVED' else \
                     colors.HexColor('#f39c12') if decision.decision == 'MANUAL_REVIEW' else \
                     colors.HexColor('#c0392b')
    
    decision_text = "APPROVED" if decision.decision == 'APPROVED' else \
                    "MANUAL REVIEW REQUIRED" if decision.decision == 'MANUAL_REVIEW' else \
                    "REJECTED"
    
    decision_data = [
        ["Agro Risk Score:", f"{decision.agro_score:.1f}/100"],
        ["Financial Score:", f"{decision.financial_score:.1f}/100"],
        ["Final Credit Score:", f"{decision.final_score:.1f}/100"],
        ["Decision:", decision_text],
    ]
    
    decision_table = Table(decision_data, colWidths=[2.5*inch, 3.5*inch])
    decision_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 2), 11),
        ('FONTSIZE', (0, 3), (-1, 3), 14),
        ('BACKGROUND', (0, 3), (-1, 3), decision_color),
        ('TEXTCOLOR', (0, 3), (-1, 3), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dfe6ee')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, 2), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 2), 8),
        ('TOPPADDING', (0, 3), (-1, 3), 12),
        ('BOTTOMPADDING', (0, 3), (-1, 3), 12),
    ]))
    
    elements.append(decision_table)
    elements.append(Spacer(1, 20))
    
    # Decision rationale
    elements.append(Paragraph("<b>Decision Rationale:</b>", styles['Normal']))
    elements.append(Spacer(1, 8))
    
    rationale = generate_decision_rationale(decision, application)
    
    rationale_style = ParagraphStyle(
        'Rationale',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#34495e')
    )
    
    elements.append(Paragraph(rationale, rationale_style))
    elements.append(Spacer(1, 30))
    
    # ===== FOOTER =====
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#ecf0f1')))
    elements.append(Spacer(1, 12))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#95a5a6'),
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph(
        "This report was generated by AgroRisk Copilot AI System<br/>"
        "For questions, contact your loan officer or financial institution<br/>"
        f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        footer_style
    ))
    
    # Build PDF
    doc.build(elements)
    
    return pdf_path


def generate_decision_rationale(decision, application):
    """Generate human-readable explanation for credit decision"""
    
    if decision.decision == 'APPROVED':
        return (
            f"The loan application has been <b>APPROVED</b> based on a combined assessment of agricultural "
            f"risk and financial health. The applicant's crop ({application.assessment.crop}) shows a "
            f"favorable risk profile with a score of {decision.agro_score:.1f}/100 in the selected region. "
            f"Financial analysis indicates strong repayment capacity with a profit margin of "
            f"{(application.net_profit/application.annual_revenue*100):.1f}% and adequate collateral coverage. "
            f"The final credit score of {decision.final_score:.1f}/100 meets the approval threshold."
        )
    
    elif decision.decision == 'MANUAL_REVIEW':
        return (
            f"The loan application requires <b>MANUAL REVIEW</b> by a loan officer. The final credit score of "
            f"{decision.final_score:.1f}/100 falls in the borderline range (50-69). While the agricultural risk "
            f"assessment shows a score of {decision.agro_score:.1f}/100, certain financial indicators require "
            f"further evaluation. We recommend a detailed interview with the applicant to assess: repayment "
            f"capacity, collateral quality, farming experience, and alternative income sources. Additional "
            f"documentation may be requested before final approval."
        )
    
    else:  # REJECTED
        reasons = []
        
        if decision.final_score < 50:
            reasons.append(f"The final credit score of {decision.final_score:.1f}/100 falls below the minimum threshold.")
        
        if decision.agro_score < 40:
            reasons.append("High agricultural risk for the selected crop in this region.")
        
        if application.previous_defaults:
            reasons.append("Previous loan defaults on record.")
        
        debt_ratio = (application.total_debt + application.loan_amount) / application.total_assets
        if debt_ratio > 0.7:
            reasons.append(f"Excessive debt-to-asset ratio ({debt_ratio*100:.1f}%).")
        
        collateral_ratio = application.collateral_value / application.loan_amount
        if collateral_ratio < 1.0:
            reasons.append(f"Insufficient collateral coverage ({collateral_ratio*100:.1f}%).")
        
        reason_text = " ".join(reasons) if reasons else "Multiple risk factors identified during assessment."
        
        return (
            f"The loan application has been <b>REJECTED</b>. {reason_text} "
            f"The applicant may reapply after addressing these concerns or consider alternative financing options "
            f"with lower risk profiles."
        )
