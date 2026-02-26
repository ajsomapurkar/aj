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

# --- 1. LANDING PAGE ---


@app.route('/')
def root():
    colleges = list(bot.db.colleges.find())
    return render_template('college_selector.html', colleges=colleges)

# --- 2. STUDENT LOGIN (FIXES YOUR 404) ---


@app.route('/college/<college_id>/login', methods=['GET', 'POST'])
def college_login_gate(college_id):
    college = bot.db.colleges.find_one({'college_id': college_id})
    if not college:
        return "College not found", 404

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = bot.db.users.find_one(
            {"email": email, "college_id": college_id})

        if user and user.get('password') == password:
            if user.get('pending'):
                flash("Wait for admin approval!", "warning")
            else:
                session['user_id'] = str(user['_id'])
                return redirect(url_for('college_chat', college_id=college_id))
        else:
            flash("Invalid credentials", "danger")

    return render_template('login.html', college=college)

# --- 3. STUDENT REGISTRATION ---


@app.route('/college/<college_id>/register', methods=['GET', 'POST'])
def college_register(college_id):
    # Fetch all colleges for the dropdown
    all_colleges = list(bot.db.colleges.find())

    # Fetch the specific college the user is visiting
    # We name it 'current_college' to fix the UndefinedError
    current_college = bot.db.colleges.find_one({'college_id': college_id})

    if request.method == 'POST':
        bot.db.users.insert_one({
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "password": request.form.get('password'),
            "college_id": request.form.get('college_id'),
            "pending": True,
            "created_at": datetime.utcnow()
        })
        flash("Registration sent! Wait for approval.", "success")
        return redirect(url_for('college_login_gate', college_id=college_id))

    # CRITICAL: We pass current_college here
    return render_template('register.html', current_college=current_college, colleges=all_colleges)

# --- 4. CHAT INTERFACE ---


@app.route('/college/<college_id>/chat')
def college_chat(college_id):
    college = bot.db.colleges.find_one({'college_id': college_id})
    return render_template('college_chat.html', college=college)

# --- 5. ADMIN PANEL ---


@app.route('/college/<college_id>/admin', methods=['GET', 'POST'])
def college_admin_panel(college_id):
    college = bot.db.colleges.find_one({'college_id': college_id})
    if request.method == 'POST' and request.form.get('question'):
        bot.db.knowledge_base.insert_one({
            "college_id": college_id,
            "question": request.form.get('question'),
            "answer": request.form.get('answer'),
            "type": "manual",
            "created_at": datetime.utcnow()
        })
        flash('Q&A saved!', 'success')

    qa_pairs = list(bot.db.knowledge_base.find({"college_id": college_id}))
    pending_users = list(bot.db.users.find(
        {"college_id": college_id, "pending": True}))
    return render_template('college_admin.html', college=college, qa_pairs=qa_pairs, pending_users=pending_users)

# --- 6. ADMIN ACTIONS (APPROVE/REJECT) ---


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

# --- 7. CHAT API ---


@app.route('/college/<college_id>/chat/api', methods=['POST'])
@csrf.exempt
def chat_api(college_id):
    data = request.json
    # We use .get() to prevent errors if 'message' is missing
    query = data.get('message', '').strip().lower()

    # --- SMALL TALK FILTER ---
    small_talk_responses = {
        "hi": "Hello! Welcome to the campus assistant. How can I help you today?",
        "hello": "Hi there! I'm here to answer your college-related questions.",
        "hey": "Hey! Need help with admissions, fees, or campus info? Just ask!",
        "thanks": "You're very welcome!",
        "thank you": "Happy to help! Feel free to ask more questions."
    }

    # If the user's word is in our dictionary, return the answer immediately
    if query in small_talk_responses:
        return jsonify({'response': small_talk_responses[query]})
    # --- END SMALL TALK FILTER ---

    # If it's NOT small talk, then we run your AI/PDF search logic
    response = bot.get_response(query, college_id)
    return jsonify({'response': response})


@app.route('/college/<college_id>/history')
def college_history(college_id):
    # 1. Fetch college info for the sidebar and page headers
    college = bot.db.colleges.find_one({'college_id': college_id})

    if not college:
        return "College not found", 404

    # 2. Fetch unanswered logs specifically for this college
    # This pulls from the 'unanswered_logs' collection in your MongoDB
    history = list(bot.db.unanswered_logs.find({"college_id": college_id}))

    # 3. Render the history.html with the data we found
    return render_template('history.html', college=college, history=history)


@app.route('/college/<college_id>/faq')
def college_faq(college_id):
    # 1. Fetch the college details for the sidebar and header
    college = bot.db.colleges.find_one({'college_id': college_id})

    if not college:
        return "College not found", 404

    # 2. Fetch all Q&A pairs for this specific college
    # We filter by college_id so students only see their own college's info
    faqs = list(bot.db.knowledge_base.find({"college_id": college_id}))

    # 3. Render the page with the data
    return render_template('faq.html', college=college, faqs=faqs)


if __name__ == '__main__':
    app.run(debug=True)
