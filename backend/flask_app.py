import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from chatbot import AmbitChatbot

# Get the absolute path of the directory where this file (flask_app.py) is located
# On PythonAnywhere, this should resolve to /home/ajstuff/bitbot
base_dir = os.path.dirname(os.path.abspath(__file__))

# Explicitly define the templates folder path
template_dir = os.path.join(base_dir, 'templates')

# Initialize Flask by telling it EXACTLY where to look for HTML files
app = Flask(__name__, template_folder=template_dir)

# Enable CORS for cross-origin requests
CORS(app)

# Initialize your chatbot logic
chatbot = AmbitChatbot()


@app.route('/')
def home():
    """Renders the main interface from /templates/index.html"""
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    """Handles the chatbot communication logic"""
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({'success': False, 'error': 'No message provided'}), 400

        message = data.get('message', '')
        response = chatbot.get_response(message)

        return jsonify({
            'success': True,
            'response': response
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health')
def health():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy', 'path': base_dir})


if __name__ == '__main__':
    # Used for local testing only
    app.run(host='0.0.0.0', port=5000, debug=True)
