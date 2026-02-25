import os
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson.objectid import ObjectId
from chatbot import AmbitChatbot
from flask_wtf import CSRFProtect
from tasks import send_email_task
from mailer import send_email as send_email_sync
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev_secret_123")
bot = AmbitChatbot()
csrf = CSRFProtect(app)

# --- 1. PUBLIC ROUTES ---


@app.route('/')
def root():
    colleges = list(bot.db.colleges.find())
    return render_template('college_selector.html', colleges=colleges)


@app.route('/register', methods=['GET', 'POST'])
def register():
    colleges = list(bot.db.colleges.find())
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        user = {
            'name': request.form.get('name', '').strip(),
            'email': email,
            'password_hash': generate_password_hash(request.form.get('password', '')),
            'college_id': request.form.get('college_id', ''),
            'role': 'student',
            'pending': True,
            'created_at': datetime.utcnow()
        }
        bot.db.users.insert_one(user)
        flash('Registration received — pending admin approval.', 'success')
        return redirect(url_for('root'))
    return render_template('register.html', colleges=colleges)

# --- 2. STUDENT LOGIN & CHAT ---


@app.route('/college/<college_id>/login', methods=['GET', 'POST'])
def college_login(college_id):
    college = bot.db.colleges.find_one({'college_id': college_id})
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        user = bot.db.users.find_one(
            {'email': email, 'college_id': college_id})
        if user and not user.get('pending') and check_password_hash(user['password_hash'], request.form.get('password', '')):
            session.update(
                {'user_id': str(user['_id']), 'college_id': college_id})
            return redirect(url_for('college_chat', college_id=college_id))
        flash('Invalid credentials or pending approval', 'danger')
    return render_template('college_login.html', college=college)


@app.route('/college/<college_id>/chat')
def college_chat(college_id):
    if session.get('college_id') != college_id:
        return redirect(url_for('college_login', college_id=college_id))
    college = bot.db.colleges.find_one({'college_id': college_id})
    return render_template('college_chat.html', college=college)


@app.route('/college/<college_id>/chat/api', methods=['POST'])
@csrf.exempt
def chat_api(college_id):
    if session.get('college_id') != college_id:
        return jsonify({'error': 'Unauthorized'}), 401
    query = request.json.get('message', '').strip()
    response = bot.get_response(query, college_id)
    return jsonify({'response': response})

# --- 3. ADMIN PANEL & APPROVAL (The Fix) ---


@app.route('/college/<college_id>/admin', methods=['GET', 'POST'])
def college_admin_panel(college_id):
    college = bot.db.colleges.find_one({"college_id": college_id})
    auth_key = f"admin_auth_{college_id}"

    if request.method == 'POST' and request.form.get('password'):
        if request.form.get('password') == college.get('admin_password'):
            session[auth_key] = True

    if not session.get(auth_key):
        return render_template('admin_login.html', college=college)

    pending_users = list(bot.db.users.find(
        {"college_id": college_id, "pending": True}))
    return render_template('college_admin.html', college=college, pending_users=pending_users)

# THIS IS THE ROUTE THAT WAS MISSING OR MISSPELLED


@app.route('/approve/<college_id>/<user_id>', methods=['POST'])
def approve_user(college_id, user_id):
    # Verify the admin is actually logged in for this college
    if session.get(f"admin_auth_{college_id}"):
        bot.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'pending': False}}
        )
        flash('User approved successfully!', 'success')
    else:
        flash('Unauthorized action', 'danger')

    return redirect(url_for('college_admin_panel', college_id=college_id))

# --- 4. SUPER ADMIN ---


@app.route('/super-admin', methods=['GET', 'POST'])
def super_admin():
    if request.method == 'POST':
        if request.form.get('master_pass') == os.getenv("MASTER_PASS", "SuperOwner2026"):
            c_id = request.form.get('college_id', '').lower().strip()
            bot.db.colleges.update_one({"college_id": c_id}, {"$set": {
                "college_name": request.form.get('college_name'),
                "admin_password": request.form.get('college_pass'),
                "admin_email": request.form.get('college_email', '').lower().strip()
            }}, upsert=True)
            flash("College created!", "success")
    colleges = list(bot.db.colleges.find())
    return render_template('super_admin.html', colleges=colleges)


if __name__ == '__main__':
    app.run(debug=True)
