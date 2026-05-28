"""
JeffCare Backend Application
Flask-based server that serves HTML pages and provides REST API endpoints
for frontend communication. Configured for CORS and environment-based settings.
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from database import init_db

# ============================================
# FLASK APP INITIALIZATION
# ============================================
# Create Flask application instance
app = Flask(__name__)
# Enable CORS to allow requests from different domains
CORS(app)

# Import API blueprint and register it under the '/api' prefix
from routes.api_routes import api_routes
app.register_blueprint(api_routes, url_prefix='/api')

# Create DB tables on startup if they don't exist yet
init_db()

# ============================================
# CONFIGURATION
# ============================================
# Set debug mode based on environment variable
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', True)

# ============================================
# PAGE ROUTES - Serve HTML Templates
# ============================================

@app.route('/')
def index():
    """Serve the main HTML page (index.html)"""
    return render_template('index.html')

@app.route('/request-certificate')
def request_certificate():
    """Serve the certificate request page (reqcrt.html)"""
    return render_template('reqcrt.html', paypal_client_id=os.getenv('PAYPAL_CLIENT_ID', ''))

@app.route('/contact')
def contact():
    """Serve the contact page (contact.html)"""
    return render_template('contact.html')

# ============================================
# API ROUTES
# ============================================
# API endpoints are defined in the `routes/api_routes.py` blueprint and
# are registered above under the `/api` URL prefix. This keeps routing
# responsibilities separated and the main app file focused on configuration
# and page-serving routes.

# ============================================
# APPLICATION ENTRY POINT
# ============================================
# Run the Flask development server when script is executed directly
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
