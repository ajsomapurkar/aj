import os
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
from datetime import datetime
from bson.objectid import ObjectId
from PyPDF2 import PdfReader
from chatbot import AmbitChatbot
from flask_wtf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev_secret_123")
csrf = CSRFProtect(app)
bot = AmbitChatbot()

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ROUTES ---


@app.route('/')
def root():
    colleges = list(bot.db.colleges.find())
    return render_template('college_selector.html', colleges=colleges)


@app.route('/college/<college_id>/admin', methods=['GET', 'POST'])
def college_admin_panel(college_id):
    college = bot.db.colleges.find_one({'college_id': college_id})

    # Handle Manual Q&A Entry
    if request.method == 'POST' and request.form.get('question'):
        bot.db.knowledge_base.insert_one({
            "college_id": college_id,
            "question": request.form.get('question'),
            "answer": request.form.get('answer'),
            "type": "manual",
            "created_at": datetime.utcnow()
        })
        flash('Q&A saved!', 'success')

    # Dashboard Data
    qa_pairs = list(bot.db.knowledge_base.find({"college_id": college_id}))
    pending_users = list(bot.db.users.find(
        {"college_id": college_id, "pending": True}))
    logs = list(bot.db.unanswered_logs.find({"college_id": college_id}))

    return render_template('college_admin.html', college=college, qa_pairs=qa_pairs,
                           pending_users=pending_users, logs=logs)


@app.route('/college/<college_id>/upload', methods=['POST'])
def upload_pdf(college_id):
    if 'pdf_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)

    file = request.files['pdf_file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process PDF
        reader = PdfReader(filepath)
        text = "\n".join([page.extract_text() for page in reader.pages])

        bot.db.knowledge_base.insert_one({
            "college_id": college_id,
            "question": f"Context from {filename}",
            "answer": text,
            "type": "pdf_content",
            "source": filename,
            "created_at": datetime.utcnow()
        })
        flash(f'Successfully trained AI with {filename}!', 'success')
    return redirect(url_for('college_admin_panel', college_id=college_id))


@app.route('/approve/<college_id>/<user_id>', methods=['POST'])
def approve_user(college_id, user_id):
    bot.db.users.update_one({'_id': ObjectId(user_id)}, {
                            '$set': {'pending': False}})
    flash('Student approved!', 'success')
    return redirect(url_for('college_admin_panel', college_id=college_id))


@app.route('/reject/<college_id>/<user_id>', methods=['POST'])
def reject_user(college_id, user_id):
    bot.db.users.delete_one({'_id': ObjectId(user_id)})
    flash('Registration rejected.', 'danger')
    return redirect(url_for('college_admin_panel', college_id=college_id))


@app.route('/college/<college_id>/chat/api', methods=['POST'])
@csrf.exempt
def chat_api(college_id):
    data = request.json
    query = data.get('message', '').strip().lower()

    # Small Talk Filter
    if query in ['hi', 'hello', 'hey', 'hlo']:
        return jsonify({'response': "Hi there! How can I help you today?"})

    response = bot.get_response(query, college_id)
    return jsonify({'response': response})


if __name__ == '__main__':
    app.run(debug=True)
