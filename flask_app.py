from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from chatbot import AmbitChatbot

# Get the directory where this script is located
basedir = os.path.abspath(os.path.dirname(__file__))

# FIX: Point to 'templates' (where your index.html actually is)
# Instead of 'frontend', we use the standard 'templates' folder
template_dir = os.path.join(basedir, 'templates')

app = Flask(__name__, template_folder=template_dir, static_folder=template_dir)
CORS(app)

chatbot = AmbitChatbot()


@app.route('/')
def home():
    # Flask will now look inside the 'templates' folder for this file
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    response = chatbot.get_response(message)
    return jsonify({'success': True, 'response': response})


@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    # host='0.0.0.0' is good for Render; debug=True is good for local testing
    app.run(host='0.0.0.0', port=5000, debug=True)
