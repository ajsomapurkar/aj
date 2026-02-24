import os
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from chatbot import AmbitChatbot
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "ambit_university_secret"  # Needed for flash messages

# Initialize the Bot
bot = AmbitChatbot()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    if not user_message:
        return jsonify({"response": "I didn't hear anything."})

    bot_response = bot.get_response(user_message)
    return jsonify({"success": True, "response": bot_response})


@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        admin_pass = request.form.get('password')
        question = request.form.get('question', '').lower().strip()
        answer = request.form.get('answer', '').strip()

        # Check password: AmbitAdmin2026
        if admin_pass == "AmbitAdmin2026":
            if question and answer:
                # This creates/updates the 'knowledge_base' collection in Atlas
                bot.db.knowledge_base.update_one(
                    {"question": question},
                    {"$set": {"answer": answer}},
                    upsert=True
                )
                flash("The bot has been updated!", "success")
            else:
                flash("Please provide both a question and an answer.", "danger")
        else:
            flash("Incorrect Admin Password!", "danger")

        return redirect(url_for('admin_panel'))

    # Show unanswered questions in the admin panel
    logs = list(bot.db.unanswered_logs.find().limit(10))
    return render_template('admin.html', logs=logs)


if __name__ == '__main__':
    app.run(debug=True)
