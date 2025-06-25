#!/usr/bin/env python3
"""
Production-Grade AI Scholar Application
Enhanced with rate limiting, structured logging, and comprehensive monitoring
"""

import os
import sys
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from functools import wraps

# Import production services
from services.logging_service import (
    app_logger, request_logger, security_logger, configure_logging
)
from services.rate_limiting_service import rate_limit, rate_limiter
from services.monitoring_service import metrics_collector, system_monitor, app_monitor

# Import existing application
from app_minimal import app as base_app, db, token_required

# Configure production logging
configure_logging()

# Create production app with enhanced features
app = Flask(__name__)

# Copy configuration from base app
app.config.update(base_app.config)

# Production-specific configuration
app.config['RATE_LIMITING_ENABLED'] = os.environ.get('RATE_LIMITING_ENABLED', 'true').lower() == 'true'
app.config['MONITORING_ENABLED'] = os.environ.get('MONITORING_ENABLED', 'true').lower() == 'true'
app.config['ENVIRONMENT'] = os.environ.get('ENVIRONMENT', 'production')

# Initialize database with production app
db.init_app(app)

# Enable CORS
CORS(app, origins=["http://localhost:3000", "http://localhost:80"], supports_credentials=True)

# Production middleware
@app.before_request
def before_request():
    """Production middleware for request logging and monitoring"""
    request.start_time = time.time()
    
    app_logger.info(
        "Request started",
        method=request.method,
        path=request.path,
        remote_addr=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )

@app.after_request
def after_request(response):
    """Production middleware for response logging and monitoring"""
    try:
        duration = time.time() - getattr(request, 'start_time', time.time())
        
        # Log request completion
        request_logger.log_request(request, response, duration)
        
        # Record metrics
        if app.config.get('MONITORING_ENABLED'):
            app_monitor.record_request(
                request.method,
                request.endpoint or 'unknown',
                response.status_code,
                duration
            )
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
        
    except Exception as e:
        app_logger.error("Error in after_request middleware", error=e)
        return response

# Enhanced authentication decorator
def production_token_required(f):
    """Enhanced token validation with security logging"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            security_logger.log_auth_attempt(
                username='unknown',
                success=False,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                reason='missing_token'
            )
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            # Use existing token validation logic
            return token_required(f)(*args, **kwargs)
        except Exception as e:
            security_logger.log_auth_attempt(
                username='unknown',
                success=False,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                reason=str(e)
            )
            raise
    
    return decorated

# Production monitoring endpoints
@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    try:
        return Response(
            metrics_collector.get_metrics(),
            mimetype='text/plain; version=0.0.4; charset=utf-8'
        )
    except Exception as e:
        app_logger.error("Failed to generate metrics", error=e)
        return "# Failed to generate metrics\n", 500

@app.route('/api/monitoring/status')
@production_token_required
def monitoring_status(current_user_id):
    """Get comprehensive monitoring status"""
    try:
        health_status = system_monitor.get_health_status()
        performance_summary = app_monitor.get_performance_summary()
        rate_limit_status = rate_limiter.get_rate_limit_status(current_user_id)
        
        return jsonify({
            'health': health_status,
            'performance': performance_summary,
            'rate_limits': rate_limit_status,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        app_logger.error("Failed to get monitoring status", error=e)
        return jsonify({'message': f'Failed to get monitoring status: {str(e)}'}), 500

@app.route('/api/health')
def enhanced_health_check():
    """Enhanced health check with comprehensive system status"""
    try:
        # Get system health
        health_status = system_monitor.get_health_status()
        
        # Test database
        try:
            db.session.execute('SELECT 1')
            db_status = True
        except:
            db_status = False
        
        overall_status = "healthy" if health_status['status'] == 'healthy' and db_status else "unhealthy"
        
        return jsonify({
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "system": health_status,
            "database": {
                "status": "up" if db_status else "down"
            },
            "features": {
                "rate_limiting": app.config.get('RATE_LIMITING_ENABLED'),
                "monitoring": app.config.get('MONITORING_ENABLED'),
                "structured_logging": True
            }
        })
        
    except Exception as e:
        app_logger.error("Health check failed", error=e)
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# Enhanced chat endpoint with rate limiting
@app.route('/api/chat', methods=['POST'])
@rate_limit('api_chat')
@production_token_required
def enhanced_chat_api(current_user_id):
    """Enhanced chat API with rate limiting and monitoring"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        model = data.get('model', 'llama2')
        
        if not message:
            return jsonify({
                "success": False,
                "error": "Message cannot be empty"
            }), 400
        
        # Log the chat request
        app_logger.info(
            "Chat request received",
            user_id=current_user_id,
            model=model,
            message_length=len(message)
        )
        
        # Simulate chat response (replace with actual implementation)
        response_text = f"Echo: {message} (using {model})"
        
        duration = time.time() - start_time
        
        # Record metrics
        if app.config.get('MONITORING_ENABLED'):
            app_monitor.record_model_usage(model, 'chat', duration, True)
        
        return jsonify({
            "success": True,
            "response": response_text,
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "response_time": duration
        })
        
    except Exception as e:
        duration = time.time() - start_time
        app_logger.error("Chat request failed", error=e, user_id=current_user_id)
        
        if app.config.get('MONITORING_ENABLED'):
            app_monitor.record_model_usage('unknown', 'chat', duration, False)
        
        return jsonify({
            "success": False,
            "error": f"Server Error: {str(e)}"
        }), 500

# Rate limit status endpoint
@app.route('/api/rate-limits')
@production_token_required
def get_rate_limits(current_user_id):
    """Get current rate limit status for user"""
    try:
        status = rate_limiter.get_rate_limit_status(current_user_id)
        return jsonify(status), 200
    except Exception as e:
        app_logger.error("Failed to get rate limit status", error=e)
        return jsonify({'message': 'Failed to get rate limit status'}), 500

def start_production_services():
    """Start production monitoring services"""
    try:
        if app.config.get('MONITORING_ENABLED'):
            system_monitor.start_monitoring()
            app_logger.info("System monitoring started")
        
        app_logger.info(
            "Production services started",
            rate_limiting=app.config.get('RATE_LIMITING_ENABLED'),
            monitoring=app.config.get('MONITORING_ENABLED'),
            environment=app.config.get('ENVIRONMENT')
        )
        
    except Exception as e:
        app_logger.error("Failed to start production services", error=e)

if __name__ == '__main__':
    print("Starting AI Scholar Production Application...")
    print(f"Environment: {app.config.get('ENVIRONMENT')}")
    print(f"Rate Limiting: {'Enabled' if app.config.get('RATE_LIMITING_ENABLED') else 'Disabled'}")
    print(f"Monitoring: {'Enabled' if app.config.get('MONITORING_ENABLED') else 'Disabled'}")
    
    # Initialize database
    with app.app_context():
        try:
            db.create_all()
            print("Database initialized successfully")
            app_logger.info("Database initialized successfully")
        except Exception as e:
            print(f"Database initialization failed: {e}")
            app_logger.error("Database initialization failed", error=e)
    
    # Start production services
    start_production_services()
    
    # Run application
    app.run(host='0.0.0.0', port=5000, debug=False)