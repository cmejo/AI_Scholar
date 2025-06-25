#!/usr/bin/env python3
"""
Business Customization Example
Demonstrates how to customize the AI Scholar Chatbot for business use
"""

from flask import Blueprint, request, jsonify
from services.chat_service import chat_service
from services.ollama_service import ollama_service
import json
from datetime import datetime, timedelta

# Business-specific blueprint
business_bp = Blueprint('business', __name__)

# Business system prompts
BUSINESS_PROMPTS = {
    "consultant": """
    You are Alex, a senior business consultant with 20+ years of experience across multiple industries.
    
    Your expertise:
    - Strategic planning and business development
    - Market analysis and competitive intelligence
    - Financial modeling and investment analysis
    - Operations optimization and process improvement
    - Risk management and mitigation strategies
    
    Communication style:
    - Professional and data-driven
    - Provide actionable recommendations
    - Include relevant metrics and KPIs
    - Consider both short-term and long-term implications
    - Ask clarifying questions when needed
    
    Always structure your responses with:
    1. Executive Summary
    2. Analysis
    3. Recommendations
    4. Next Steps
    """,
    
    "analyst": """
    You are Morgan, a business intelligence analyst specializing in data-driven insights.
    
    Your capabilities:
    - Financial analysis and forecasting
    - Market research and trend analysis
    - Performance metrics and KPI tracking
    - Competitive benchmarking
    - ROI and cost-benefit analysis
    
    Approach:
    - Lead with data and evidence
    - Provide quantitative insights
    - Identify patterns and trends
    - Suggest measurement strategies
    - Present findings clearly and concisely
    """,
    
    "strategist": """
    You are Taylor, a strategic planning expert focused on long-term business growth.
    
    Your focus areas:
    - Vision and mission development
    - Strategic goal setting and planning
    - Innovation and growth strategies
    - Digital transformation initiatives
    - Organizational development
    
    Methodology:
    - Think strategically and systematically
    - Consider market dynamics and trends
    - Balance innovation with risk management
    - Provide frameworks and methodologies
    - Focus on sustainable competitive advantage
    """
}

# Business model configurations
BUSINESS_MODELS = {
    "consulting": {
        "model": "mistral:7b-instruct",
        "temperature": 0.4,
        "top_p": 0.9,
        "max_tokens": 2000,
        "system_prompt": BUSINESS_PROMPTS["consultant"]
    },
    "analysis": {
        "model": "llama2:13b-chat",
        "temperature": 0.3,
        "top_p": 0.9,
        "max_tokens": 1800,
        "system_prompt": BUSINESS_PROMPTS["analyst"]
    },
    "strategy": {
        "model": "llama2:7b-chat",
        "temperature": 0.5,
        "top_p": 0.9,
        "max_tokens": 2200,
        "system_prompt": BUSINESS_PROMPTS["strategist"]
    }
}

class BusinessService:
    """Service for business-specific functionality"""
    
    def __init__(self):
        self.analysis_frameworks = {
            "swot": self._swot_analysis,
            "pestle": self._pestle_analysis,
            "porter": self._porter_five_forces,
            "bcg": self._bcg_matrix,
            "ansoff": self._ansoff_matrix
        }
        
        self.financial_metrics = {
            "roi": self._calculate_roi,
            "npv": self._calculate_npv,
            "irr": self._calculate_irr,
            "payback": self._calculate_payback_period
        }
    
    def _swot_analysis(self, business_data: dict) -> dict:
        """Perform SWOT analysis"""
        return {
            "framework": "SWOT Analysis",
            "strengths": business_data.get("strengths", []),
            "weaknesses": business_data.get("weaknesses", []),
            "opportunities": business_data.get("opportunities", []),
            "threats": business_data.get("threats", []),
            "recommendations": self._generate_swot_recommendations(business_data)
        }
    
    def _pestle_analysis(self, business_data: dict) -> dict:
        """Perform PESTLE analysis"""
        factors = ["political", "economic", "social", "technological", "legal", "environmental"]
        analysis = {}
        
        for factor in factors:
            analysis[factor] = business_data.get(factor, {})
        
        return {
            "framework": "PESTLE Analysis",
            "factors": analysis,
            "impact_assessment": self._assess_pestle_impact(analysis),
            "recommendations": self._generate_pestle_recommendations(analysis)
        }
    
    def _porter_five_forces(self, business_data: dict) -> dict:
        """Perform Porter's Five Forces analysis"""
        forces = {
            "competitive_rivalry": business_data.get("competitive_rivalry", {}),
            "supplier_power": business_data.get("supplier_power", {}),
            "buyer_power": business_data.get("buyer_power", {}),
            "threat_of_substitution": business_data.get("threat_of_substitution", {}),
            "threat_of_new_entry": business_data.get("threat_of_new_entry", {})
        }
        
        return {
            "framework": "Porter's Five Forces",
            "forces": forces,
            "industry_attractiveness": self._assess_industry_attractiveness(forces),
            "strategic_implications": self._generate_porter_implications(forces)
        }
    
    def _calculate_roi(self, investment: float, returns: float) -> dict:
        """Calculate Return on Investment"""
        roi = ((returns - investment) / investment) * 100
        return {
            "metric": "ROI",
            "value": round(roi, 2),
            "interpretation": self._interpret_roi(roi)
        }
    
    def _calculate_npv(self, cash_flows: list, discount_rate: float) -> dict:
        """Calculate Net Present Value"""
        npv = 0
        for i, cf in enumerate(cash_flows):
            npv += cf / ((1 + discount_rate) ** i)
        
        return {
            "metric": "NPV",
            "value": round(npv, 2),
            "interpretation": "Positive NPV indicates profitable investment" if npv > 0 else "Negative NPV indicates unprofitable investment"
        }
    
    def generate_business_plan_outline(self, business_type: str, industry: str) -> dict:
        """Generate business plan outline"""
        outline = {
            "executive_summary": "Overview of business concept, market opportunity, and financial projections",
            "company_description": f"Detailed description of {business_type} in {industry} industry",
            "market_analysis": "Industry overview, target market, and competitive analysis",
            "organization_management": "Organizational structure and management team",
            "products_services": "Description of products/services offered",
            "marketing_sales": "Marketing strategy and sales projections",
            "funding_request": "Funding requirements and use of funds",
            "financial_projections": "Revenue, expense, and profitability forecasts",
            "appendix": "Supporting documents and additional information"
        }
        
        return {
            "business_type": business_type,
            "industry": industry,
            "outline": outline,
            "estimated_pages": self._estimate_plan_length(business_type)
        }
    
    def analyze_market_opportunity(self, market_data: dict) -> dict:
        """Analyze market opportunity"""
        market_size = market_data.get("market_size", 0)
        growth_rate = market_data.get("growth_rate", 0)
        competition_level = market_data.get("competition_level", "medium")
        
        opportunity_score = self._calculate_opportunity_score(market_size, growth_rate, competition_level)
        
        return {
            "market_size": market_size,
            "growth_rate": growth_rate,
            "competition_level": competition_level,
            "opportunity_score": opportunity_score,
            "recommendation": self._generate_market_recommendation(opportunity_score),
            "key_factors": self._identify_key_success_factors(market_data)
        }
    
    def _generate_swot_recommendations(self, data: dict) -> list:
        """Generate recommendations based on SWOT analysis"""
        return [
            "Leverage strengths to capitalize on opportunities",
            "Address weaknesses that could be exploited by threats",
            "Develop strategies to mitigate identified threats",
            "Build on strengths to create competitive advantages"
        ]
    
    def _assess_pestle_impact(self, analysis: dict) -> dict:
        """Assess impact of PESTLE factors"""
        return {
            "high_impact": ["technological", "economic"],
            "medium_impact": ["social", "political"],
            "low_impact": ["legal", "environmental"]
        }
    
    def _calculate_opportunity_score(self, size: float, growth: float, competition: str) -> float:
        """Calculate market opportunity score"""
        base_score = (size * 0.4) + (growth * 0.4)
        
        competition_multiplier = {
            "low": 1.2,
            "medium": 1.0,
            "high": 0.8
        }
        
        return base_score * competition_multiplier.get(competition, 1.0)

# Business API endpoints
@business_bp.route('/api/business/consulting-chat', methods=['POST'])
def consulting_chat():
    """Chat endpoint optimized for business consulting"""
    data = request.get_json()
    message = data.get('message', '')
    session_id = data.get('session_id')
    
    # Use consulting-optimized model configuration
    config = BUSINESS_MODELS["consulting"]
    
    try:
        for response in chat_service.generate_response(
            session_id=session_id,
            user_id=1,  # Would get from auth
            message=message,
            model=config["model"],
            parameters={
                "temperature": config["temperature"],
                "top_p": config["top_p"],
                "max_tokens": config["max_tokens"]
            },
            stream=False
        ):
            if response.is_complete:
                return jsonify({
                    "success": True,
                    "response": response.content,
                    "model": config["model"],
                    "type": "consulting_response"
                })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@business_bp.route('/api/business/swot-analysis', methods=['POST'])
def swot_analysis():
    """Perform SWOT analysis"""
    data = request.get_json()
    business_data = data.get('business_data', {})
    
    business_service = BusinessService()
    analysis = business_service._swot_analysis(business_data)
    
    return jsonify(analysis)

@business_bp.route('/api/business/financial-metrics', methods=['POST'])
def calculate_financial_metrics():
    """Calculate financial metrics"""
    data = request.get_json()
    metric_type = data.get('type', 'roi')
    parameters = data.get('parameters', {})
    
    business_service = BusinessService()
    
    if metric_type == "roi":
        investment = parameters.get('investment', 0)
        returns = parameters.get('returns', 0)
        result = business_service._calculate_roi(investment, returns)
    elif metric_type == "npv":
        cash_flows = parameters.get('cash_flows', [])
        discount_rate = parameters.get('discount_rate', 0.1)
        result = business_service._calculate_npv(cash_flows, discount_rate)
    else:
        return jsonify({"error": "Unsupported metric type"}), 400
    
    return jsonify(result)

@business_bp.route('/api/business/market-analysis', methods=['POST'])
def market_analysis():
    """Analyze market opportunity"""
    data = request.get_json()
    market_data = data.get('market_data', {})
    
    business_service = BusinessService()
    analysis = business_service.analyze_market_opportunity(market_data)
    
    return jsonify(analysis)

@business_bp.route('/api/business/business-plan', methods=['POST'])
def generate_business_plan():
    """Generate business plan outline"""
    data = request.get_json()
    business_type = data.get('business_type', '')
    industry = data.get('industry', '')
    
    business_service = BusinessService()
    plan = business_service.generate_business_plan_outline(business_type, industry)
    
    return jsonify(plan)

@business_bp.route('/api/business/competitive-analysis', methods=['POST'])
def competitive_analysis():
    """Perform competitive analysis using AI"""
    data = request.get_json()
    company = data.get('company', '')
    competitors = data.get('competitors', [])
    
    # Use analysis model for competitive analysis
    config = BUSINESS_MODELS["analysis"]
    
    prompt = f"""
    Perform a competitive analysis for {company} against the following competitors: {', '.join(competitors)}.
    
    Please provide:
    1. Market positioning comparison
    2. Strengths and weaknesses of each competitor
    3. Competitive advantages and disadvantages
    4. Market share analysis (if known)
    5. Strategic recommendations for {company}
    
    Structure your response in a clear, business-ready format.
    """
    
    try:
        result = ollama_service.generate_response(
            model=config["model"],
            prompt=prompt,
            stream=False
        )
        
        return jsonify({
            "analysis": result.get("response", ""),
            "company": company,
            "competitors": competitors,
            "model": config["model"]
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@business_bp.route('/api/business/risk-assessment', methods=['POST'])
def risk_assessment():
    """Perform business risk assessment"""
    data = request.get_json()
    business_context = data.get('context', '')
    risk_categories = data.get('categories', ['financial', 'operational', 'strategic', 'compliance'])
    
    config = BUSINESS_MODELS["consulting"]
    
    prompt = f"""
    Perform a comprehensive risk assessment for the following business context:
    {business_context}
    
    Analyze risks in these categories: {', '.join(risk_categories)}
    
    For each risk category, provide:
    1. Identified risks
    2. Probability assessment (High/Medium/Low)
    3. Impact assessment (High/Medium/Low)
    4. Risk mitigation strategies
    5. Monitoring recommendations
    
    Present your analysis in a structured, actionable format.
    """
    
    try:
        result = ollama_service.generate_response(
            model=config["model"],
            prompt=prompt,
            stream=False
        )
        
        return jsonify({
            "assessment": result.get("response", ""),
            "categories": risk_categories,
            "model": config["model"]
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

# Example usage function
def setup_business_customization(app):
    """Set up business customization for the app"""
    
    # Register business blueprint
    app.register_blueprint(business_bp)
    
    # Set business-specific configuration
    app.config.update({
        'BUSINESS_MODE': True,
        'DEFAULT_SYSTEM_PROMPT': BUSINESS_PROMPTS["consultant"],
        'ANALYTICS_ENABLED': True,
        'FINANCIAL_TOOLS': True
    })
    
    print("✅ Business customization enabled")
    print("💼 Available endpoints:")
    print("  - /api/business/consulting-chat")
    print("  - /api/business/swot-analysis")
    print("  - /api/business/financial-metrics")
    print("  - /api/business/market-analysis")
    print("  - /api/business/business-plan")
    print("  - /api/business/competitive-analysis")
    print("  - /api/business/risk-assessment")

if __name__ == "__main__":
    # Example of how to test business features
    business_service = BusinessService()
    
    # Test SWOT analysis
    sample_business = {
        "strengths": ["Strong brand", "Experienced team"],
        "weaknesses": ["Limited funding", "Small market share"],
        "opportunities": ["Growing market", "New technology"],
        "threats": ["Increased competition", "Economic downturn"]
    }
    
    print("Sample SWOT Analysis:")
    swot = business_service._swot_analysis(sample_business)
    print(json.dumps(swot, indent=2))
    
    # Test ROI calculation
    roi_result = business_service._calculate_roi(10000, 15000)
    print(f"\nROI Calculation: {roi_result}")
    
    # Test business plan outline
    plan = business_service.generate_business_plan_outline("SaaS", "Technology")
    print(f"\nBusiness Plan Outline:")
    for section, description in plan["outline"].items():
        print(f"  {section}: {description}")