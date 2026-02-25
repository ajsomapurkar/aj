import os
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from chatbot import AmbitChatbot
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev_secret_123")
bot = AmbitChatbot()

# --- 0. ROOT (College Selector) ---


@app.route('/')
def root():
    colleges = list(bot.db.colleges.find())
    return render_template('college_selector.html', colleges=colleges)


# --- 1. SUPER ADMIN (Manage Colleges) ---


@app.route('/super-admin', methods=['GET', 'POST'])
def super_admin():
    master_pass = os.getenv("MASTER_PASS", "SuperOwner2026")

    if request.method == 'POST':
        entered_pass = request.form.get('master_pass')
        new_id = request.form.get('college_id', '').lower().strip()
        new_name = request.form.get('college_name')
        new_pass = request.form.get('college_pass')

        if entered_pass == master_pass:
            bot.db.colleges.update_one(
                {"college_id": new_id},
                {"$set": {"college_name": new_name,
                          "admin_password": new_pass, "status": "active"}},
                upsert=True
            )
            flash(f"College {new_name} registered!", "success")
        else:
            flash("Wrong Master Password!", "danger")
        return redirect('/super-admin')

    colleges = list(bot.db.colleges.find())
    return render_template('super_admin.html', colleges=colleges)


# --- Auth: register / login / logout ---


@app.route('/register', methods=['GET', 'POST'])
def register():
    colleges = list(bot.db.colleges.find())
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        college_id = request.form.get('college_id', '')

        if not (email and password and college_id):
            flash('Missing fields', 'danger')
            return redirect(url_for('register'))

        if bot.db.users.find_one({'email': email}):
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        pw_hash = generate_password_hash(password)
        user = {
            'name': name,
            'email': email,
            'password_hash': pw_hash,
            'college_id': college_id,
            'role': 'student',
            'created_at': datetime.utcnow()
        }
        bot.db.users.insert_one(user)
        flash('Registration successful — please log in', 'success')
        return redirect(url_for('root'))

    return render_template('register.html', colleges=colleges)


@app.route('/college/<college_id>/login', methods=['GET', 'POST'])
def college_login(college_id):
    college = bot.db.colleges.find_one({'college_id': college_id})
    if not college:
        return "College not found", 404

    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        user = bot.db.users.find_one(
            {'email': email, 'college_id': college_id})
        if not user or not check_password_hash(user.get('password_hash', ''), password):
            flash('Invalid credentials or not a student of this college', 'danger')
            return redirect(url_for('college_login', college_id=college_id))

        session['user_id'] = str(user['_id'])
        session['email'] = user['email']
        session['role'] = user.get('role', 'student')
        session['college_id'] = college_id
        flash(f'Logged in to {college["college_name"]}', 'success')
        return redirect(url_for('college_chat', college_id=college_id))

    return render_template('college_login.html', college=college)


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'success')
    return redirect(url_for('root'))


@app.route('/college/<college_id>/chat')
def college_chat(college_id):
    college = bot.db.colleges.find_one({'college_id': college_id})
    if not college:
        return "College not found", 404
    # Require login for student chat
    if not session.get('user_id') or session.get('college_id') != college_id:
        flash('Please log in first', 'danger')
        return redirect(url_for('college_login', college_id=college_id))
    return render_template('college_chat.html', college=college)


@app.route('/college/<college_id>/chat/api', methods=['POST'])
def chat_api(college_id):
    user_id = session.get('user_id')
    session_college = session.get('college_id')

    # Enforce college isolation:
    if not user_id or session_college != college_id:
        return jsonify({'error': 'Unauthorized'}), 401

    query = request.json.get('message', '').strip()
    if not query:
        return jsonify({'error': 'Empty message'}), 400

    response = bot.get_response(query, college_id)
    return jsonify({'response': response})

# --- 2. COLLEGE ADMIN (Manage Questions) ---


@app.route('/<college_id>/admin', methods=['GET', 'POST'])
@app.route('/college/<college_id>/admin', methods=['GET', 'POST'])
def college_admin_panel(college_id):
    college = bot.db.colleges.find_one({"college_id": college_id})
    if not college:
        return "College Not Found", 404

    # Enforce college isolation: only admins from that college or password
    is_college_admin = (session.get('role') ==
                        'admin' and session.get('college_id') == college_id)

    # Check if they're authenticated for this admin panel (via password or role)
    admin_auth_key = f"admin_auth_{college_id}"
    is_authenticated = is_college_admin or session.get(admin_auth_key)

    if request.method == 'POST':
        password_attempt = request.form.get('password', '')

        # If password field exists, validate it
        if password_attempt:
            if password_attempt != college.get('admin_password'):
                flash('Invalid admin password', 'danger')
                return redirect(url_for('college_admin_panel', college_id=college_id))
            else:
                # Password correct - set session marker
                session[admin_auth_key] = True
                is_authenticated = True
                flash('Admin access granted', 'success')

        # If trying to save Q&A, but not authenticated, reject
        if not is_authenticated and 'question' in request.form:
            flash('Please authenticate first', 'danger')
            return redirect(url_for('college_admin_panel', college_id=college_id))

        # Save Q&A if authenticated and form has question/answer
        if is_authenticated and 'question' in request.form:
            q = request.form.get('question', '').lower().strip()
            a = request.form.get('answer', '').strip()
            if q and a:
                bot.db.knowledge_base.update_one(
                    {"question": q, "college_id": college_id},
                    {"$set": {"answer": a}},
                    upsert=True
                )
                flash("Question saved!", "success")
            else:
                flash("Question and answer required", "danger")

    # If not authenticated, show password login
    if not is_authenticated and request.method == 'GET':
        return render_template('admin_login.html', college=college)

    # Authenticated - show admin panel
    logs = list(bot.db.unanswered_logs.find(
        {"college_id": college_id}).limit(10))
    return render_template('college_admin.html', college=college, logs=logs)


if __name__ == '__main__':
    app.run(debug=True)
