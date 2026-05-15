from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', True)

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/api/hello', methods=['GET'])
def hello():
    """Simple API endpoint"""
    return jsonify({'message': 'Hello from Python backend!'})

@app.route('/api/data', methods=['POST'])
def receive_data():
    """Receive data from frontend"""
    data = request.json
    return jsonify({'status': 'success', 'received': data})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
