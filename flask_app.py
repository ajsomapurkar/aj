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

# --- 2. STUDENT LOGIN ---


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
                session['user_name'] = user.get('name', 'Student')
                return redirect(url_for('college_chat', college_id=college_id))
        else:
            flash("Invalid credentials", "danger")

    return render_template('login.html', college=college)


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('root'))

# --- 3. STUDENT REGISTRATION ---


@app.route('/college/<college_id>/register', methods=['GET', 'POST'])
def college_register(college_id):
    all_colleges = list(bot.db.colleges.find())
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

    return render_template('register.html', current_college=current_college, colleges=all_colleges)

# --- 4. CHAT INTERFACE ---


@app.route('/college/<college_id>/chat')
def college_chat(college_id):
    college = bot.db.colleges.find_one({'college_id': college_id})
    return render_template('college_chat.html', college=college)

# --- 5. COLLEGE ADMIN PANEL ---


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

# --- 6. ADMIN ACTIONS ---


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
    query = data.get('message', '').strip().lower()

    small_talk_responses = {
        "hi": "Hello! Welcome to the campus assistant. How can I help you today?",
        "hello": "Hi there! I'm here to answer your college-related questions.",
        "hey": "Hey! Need help with admissions, fees, or campus info? Just ask!",
        "thanks": "You're very welcome!",
        "thank you": "Happy to help! Feel free to ask more questions."
    }

    if query in small_talk_responses:
        return jsonify({'response': small_talk_responses[query]})

    response = bot.get_response(query, college_id)
    return jsonify({'response': response})


@app.route('/college/<college_id>/history')
def college_history(college_id):
    college = bot.db.colleges.find_one({'college_id': college_id})
    if not college:
        return "College not found", 404
    history = list(bot.db.unanswered_logs.find({"college_id": college_id}))
    return render_template('history.html', college=college, history=history)


@app.route('/college/<college_id>/faq')
def college_faq(college_id):
    college = bot.db.colleges.find_one({'college_id': college_id})
    if not college:
        return "College not found", 404
    faqs = list(bot.db.knowledge_base.find({"college_id": college_id}))
    return render_template('faq.html', college=college, faqs=faqs)

# --- 8. SUPER ADMIN (MERGED & UNIQUE) ---


@app.route('/super-admin', methods=['GET', 'POST'])
def super_admin():
    if request.method == 'POST':
        # Handles College Registration
        if 'college_id' in request.form:
            bot.db.colleges.insert_one({
                "college_id": request.form.get('college_id'),
                "college_name": request.form.get('college_name'),
                "college_email": request.form.get('college_email'),
                "created_at": datetime.utcnow()
            })
            flash("New College Registered!", "success")

        # Handles Resource Vault (Injecting Books)
        elif 'resource_title' in request.form:
            bot.db.resources.insert_one({
                "title": request.form.get('resource_title'),
                "category": request.form.get('category'),
                "url": request.form.get('resource_url'),
                "created_at": datetime.utcnow()
            })
            flash("Book added to Resource Library!", "success")

        return redirect(url_for('super_admin'))

    colleges = list(bot.db.colleges.find())
    return render_template('super_admin.html', colleges=colleges)

# --- 9. STUDENT RESOURCE VIEW ---


@app.route('/college/<college_id>/resources')
def resource_library(college_id):
    college = bot.db.colleges.find_one({'college_id': college_id})
    if not college:
        return "College not found", 404

    library_books = list(bot.db.resources.find().sort("created_at", -1))
    return render_template('resources.html', college=college, resources=library_books)


# --- 10. APP ENTRY POINT ---
if __name__ == '__main__':
    app.run(debug=True)
