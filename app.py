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

# ============================================
# FLASK APP INITIALIZATION
# ============================================
# Create Flask application instance
app = Flask(__name__)
# Enable CORS to allow requests from different domains
CORS(app)

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
    return render_template('reqcrt.html')

@app.route('/contact')
def contact():
    """Serve the contact page (contact.html)"""
    return render_template('contact.html')

# ============================================
# API ENDPOINTS - Provide Data to Frontend
# ============================================

@app.route('/api/hello', methods=['GET'])
def hello():
    """Simple GET endpoint that returns a greeting message from the backend"""
    return jsonify({'message': 'Hello from Python backend!'})

@app.route('/api/data', methods=['POST'])
def receive_data():
    """Accept JSON data from frontend and return confirmation"""
    # Extract JSON data from the request
    data = request.json
    # Return success response with the received data
    return jsonify({'status': 'success', 'received': data})

# ============================================
# APPLICATION ENTRY POINT
# ============================================
# Run the Flask development server when script is executed directly
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
