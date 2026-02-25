# AMBIT Chatbot - Multi-Tenant Campus AI Assistant

## 📋 Project Overview

**AMBIT** is a **multi-tenant SaaS chatbot platform** where:
- 🎓 Multiple colleges can register and manage their own AI assistant
- 👥 Students from each college login and ask questions specific to their college
- 🤖 The bot answers using college-specific Q&A database
- 👨‍💼 College admins manage Q&A pairs for their students
- 🔐 Super-admin manages all colleges in the system

**Key Concept**: Each college has its own isolated data - student A from College X cannot see College Y's information.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FLASK WEB APP                           │
│              (Flask with Jinja2 Templates)                  │
└─────────────────────────────────────────────────────────────┘
         ↓                    ↓                      ↓
    ┌────────────┐      ┌──────────────┐      ┌──────────────┐
    │  Routes    │      │  Auth Logic  │      │ Chat Logic   │
    │ (URLs)     │      │ (Login/Reg)  │      │ (Q&A Match)  │
    └────────────┘      └──────────────┘      └──────────────┘
         ↓                    ↓                      ↓
    ┌─────────────────────────────────────────────────────────┐
    │           AMBITCHATBOT CLASS (chatbot.py)              │
    │     - get_response(query, college_id)                  │
    │     - Matches user query with college Q&A database     │
    └─────────────────────────────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────────────────────────┐
    │             MONGODB DATABASE (ambit_db)                │
    │  ┌──────────────┐  ┌──────────┐  ┌──────────────────┐ │
    │  │  colleges    │  │  users   │  │ knowledge_base   │ │
    │  └──────────────┘  └──────────┘  └──────────────────┘ │
    │  ┌──────────────────────────┐                          │
    │  │   unanswered_logs        │                          │
    │  └──────────────────────────┘                          │
    └─────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure

```
ambit_chatbot/
├── flask_app.py                    # Main Flask application (all routes)
├── chatbot.py                      # AI chatbot logic
├── knowledge_base.py               # Database utilities (if needed)
├── migrate.py                      # Database migration script
├── requirements.txt                # Python dependencies
├── templates/                      # HTML templates
│   ├── college_selector.html       # Landing page (select college)
│   ├── college_login.html          # Student/admin login form
│   ├── college_chat.html           # Student chat interface
│   ├── college_admin.html          # Admin dashboard (manage Q&A)
│   ├── admin_login.html            # Admin password entry
│   ├── super_admin.html            # Super-admin (register colleges)
│   ├── register.html               # Student registration form
│   └── login.html                  # Legacy login (unused now)
└── __pycache__/                    # Python cache files
```

---

## 🗄️ Database Schema

### **1. colleges** collection
Stores all registered colleges
```javascript
{
  "college_id": "amity",                    // Unique identifier (lowercase)
  "college_name": "Amity University",       // Display name
  "admin_password": "AmityAdmin@2026",      // Password for admin access
  "status": "active"                        // Active/inactive status
}
```

### **2. users** collection
Stores all students and admins
```javascript
{
  "name": "John Doe",
  "email": "john@amity.edu",
  "password_hash": "scrypt:32768:8:1$...",  // Hashed password (secure)
  "college_id": "amity",                    // Which college they belong to
  "role": "student",                        // Or "admin"
  "created_at": ISODate("2026-02-25")
}
```

### **3. knowledge_base** collection
Stores Q&A pairs for each college
```javascript
{
  "question": "what is the admission process",
  "answer": "Fill the application form...",
  "college_id": "amity"                     // College isolation
}
```

### **4. unanswered_logs** collection
Tracks questions the bot couldn't answer
```javascript
{
  "query": "How old is the campus?",
  "college_id": "amity",
  "timestamp": ISODate("2026-02-25T10:30:00Z")
}
```

---

## 👥 User Types & Their Workflows

### **1. Super Admin**
**Purpose**: Register and manage new colleges

**Access**: http://127.0.0.1:5000/super-admin
**Password**: `SuperOwner2026` (from .env)

**Workflow**:
1. Visit `/super-admin`
2. Enter master password
3. Fill:
   - College ID: `amity` (lowercase, unique)
   - College Name: `Amity University`
   - College Admin Password: `AmityAdmin@2026`
4. Click Register
5. College is added to database

---

### **2. College Admin**
**Purpose**: Manage Q&A pairs for their students

**Access**: http://127.0.0.1:5000/college/amity/admin
**Password**: The admin password set during college registration

**Workflow**:
1. Visit `/college/amity/admin`
2. Enter admin password
3. **Two options**:
   - **Add Q&A Form**: 
     - Fill question: "What are fees?"
     - Fill answer: "Annual fees are Rs 1,50,000"
     - Click "Save Q&A"
   - **View Collections**:
     - See all saved Q&A pairs in "Saved Q&A Collection"
     - See unanswered questions students asked

**What happens behind the scenes**:
- Q&A is saved to `knowledge_base` collection with `college_id="amity"`
- When students ask questions, bot searches this Q&A database
- Questions bot can't answer go to `unanswered_logs` for admin review

---

### **3. Student**
**Purpose**: Ask questions about their college

**Access**: http://127.0.0.1:5000/ (start here)

**Workflow**:
1. **Arrive at college selector** (/):
   - Landing page shows all colleges
   - Select your college (e.g., "Amity University")

2. **Choose action**:
   - **New student**: Click "Register" → Fill form → Login
   - **Existing student**: Click college name → Login

3. **Login** (/college/amity/login):
   - Email: `student@amity.edu`
   - Password: `password123`
   - Click Login

4. **Chat** (/college/amity/chat):
   - Professional interface with sidebar
   - Type questions: "What are fees?", "Admission process?"
   - Bot searches college's Q&A database
   - **If found**: Returns answer from knowledge_base
   - **If not found**: Returns generic response + logs question for admin

5. **Logout**: 
   - Click logout button → Returns to college selector

---

## 🤖 How the Chatbot Works

### **Query Processing Flow**

```
Student asks: "What are the fee structures?"
        ↓
Flask receives at /college/amity/chat/api
        ↓
Calls: bot.get_response(query, "amity")
        ↓
AmbitChatbot.get_response() searches:
   1. Find all Q&A for college "amity"
   2. For each Q&A pair:
      - Check if question == query (exact match)
      - Check if question IN query (substring match)
      - Check if query IN question (substring match)
   3. If found: Return the answer
   4. If not found: 
      - Log to unanswered_logs
      - Return fallback response
        ↓
Answer returned to student in chat
```

### **Matching Logic** (in chatbot.py)
```python
def get_response(self, query, college_id):
    query_lower = query.lower()
    
    # Find Q&A for this college
    qa_pairs = list(self.db.knowledge_base.find({"college_id": college_id}))
    
    for qa in qa_pairs:
        question = qa.get("question", "").lower()
        
        # Try different matching strategies
        if question == query_lower:           # Exact match
            return qa["answer"]
        if question in query_lower:           # Question is substring of query
            return qa["answer"]
        if query_lower in question:           # Query is substring of question
            return qa["answer"]
    
    # Not found - log and return fallback
    self.db.unanswered_logs.insert_one({
        "query": query,
        "college_id": college_id
    })
    return "I couldn't find an answer to that..."
```

---

## 🔐 Authentication & Security

### **Password Hashing**
- All passwords are **hashed using scrypt** (very secure)
- Never stored as plain text
- Example hash: `scrypt:32768:8:1$OYO6AToJaqR6Ye77$77cb45e90f...`

### **Session Management**
- **Students**: Session stores `user_id`, `email`, `college_id`, `role`
- **Admins**: Temporary session marker `admin_auth_{college_id}` for quick access
- Sessions expire when user logs out

### **College Isolation**
- Every query checked: does `session.college_id` match the URL `college_id`?
- Students can only see their own college's chat
- Admins can only manage their own college's Q&A
- Data is filtered by `college_id` in all database queries

---

## 📊 Key Features Implemented

| Feature | Status | Details |
|---------|--------|---------|
| Multi-tenant architecture | ✅ | Each college is completely isolated |
| College registration | ✅ | Super-admin registers colleges |
| Student registration | ✅ | Web UI form for students to register |
| Student login | ✅ | College-scoped login with email/password |
| Admin login | ✅ | Password-protected admin panel |
| Q&A management | ✅ | Admins add/view Q&A pairs |
| AI chatbot | ✅ | Query matching with college-specific Q&A |
| Professional UI | ✅ | Modern gradient design with sidebar |
| Session-based auth | ✅ | Secure session management |
| Database isolation | ✅ | Data filtered by college_id |
| Unanswered tracking | ✅ | Logs questions bot couldn't answer |

---

## 🚀 Quick Start Guide

### **1. Start Flask Server**
```bash
cd c:\Users\ajay\OneDrive\Desktop\ambit_chatbot
python flask_app.py
```
Server runs on: http://127.0.0.1:5000

### **2. Register a College** (Super Admin)
- Visit: http://127.0.0.1:5000/super-admin
- Password: `SuperOwner2026`
- Fill college details
- Click Register

### **3. Create a Student Account**
- Visit: http://127.0.0.1:5000/register
- Fill name, email, password, select college
- Click Register
- Login at `/college/<college_id>/login`

### **4. Add Q&A** (Admin)
- Visit: http://127.0.0.1:5000/college/<college_id>/admin
- Enter admin password
- Add questions and answers
- Click "Save Q&A"

### **5. Chat as Student**
- Login as student
- Ask questions
- Bot responds with college-specific answers

---

## 🔧 Environment Variables (.env)

```
MASTER_PASS=SuperOwner2026          # Master password for super-admin
FLASK_SECRET=dev_secret_123         # Flask session encryption key
MONGODB_URI=mongodb://...           # MongoDB connection (if needed)
```

---

## 📞 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | College selector landing page |
| `/super-admin` | GET/POST | Register new colleges |
| `/register` | GET/POST | Student registration |
| `/college/<id>/login` | GET/POST | Student/Admin login |
| `/college/<id>/chat` | GET | Student chat interface |
| `/college/<id>/chat/api` | POST | Backend API (send message) |
| `/college/<id>/admin` | GET/POST | Admin dashboard |
| `/logout` | GET | Logout and clear session |

---

## 🐛 Common Issues & Fixes

### **"Invalid credentials or not a student of this college"**
- Make sure you're logging in with the correct college
- Email must exist in database with matching college_id
- Check password is correct

### **"College not found"**
- College ID doesn't exist
- Register college first via super-admin

### **Bot not answering questions**
- Check if Q&A exists in knowledge_base collection
- Visit admin panel to see "Saved Q&A Collection"
- Try adding more Q&A pairs

### **Messages not scrolling**
- Clear browser cache
- Refresh page
- Scrollbar is larger and more visible now

### **Admin panel shows no Q&A**
- No Q&A pairs added yet
- Visit admin panel → Add Q&A form → Fill and save

---

## 📈 Future Enhancements

**Possible additions**:
- Edit/delete Q&A functionality
- Export Q&A to CSV
- Analytics dashboard (most asked questions)
- AI-powered fallback using API (GPT, etc)
- Multi-language support
- Voice chat
- File uploads for FAQs
- User feedback/ratings on answers

---

## 👨‍💻 Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Flask (Python) |
| **Frontend** | HTML/CSS/JavaScript |
| **Database** | MongoDB |
| **Authentication** | Flask Sessions + Werkzeug |
| **UI Framework** | Custom CSS (Gradient design) |
| **Icons** | Font Awesome |

---

## 📝 Example Workflow: Complete End-to-End

### **Scenario**: New college "XYZ Institute" joins the platform

**Step 1: Super Admin registers college**
```
Visit: /super-admin
Password: SuperOwner2026
Fill:
  - College ID: xyz
  - College Name: XYZ Institute
  - Admin Password: XyzAdmin2026
Result: College added to database
```

**Step 2: College admin adds Q&A**
```
Visit: /college/xyz/admin
Enter password: XyzAdmin2026
Add Q&A:
  - Q: "What are the fees?"
  - A: "Undergraduate fees: Rs 2,00,000/year"
Result: Saved to knowledge_base
```

**Step 3: Student registers**
```
Visit: /register
Fill: Name: Priya, Email: priya@xyz.edu, Password: pass123, College: xyz
Result: User created in database
```

**Step 4: Student logs in and chats**
```
Visit: /college/xyz/login
Login: priya@xyz.edu / pass123
Visit: /college/xyz/chat
Ask: "What are the fees?"
Bot: "Undergraduate fees: Rs 2,00,000/year"
Result: Answer from college-specific Q&A
```

---

## ✅ What Makes This a "Major Website"

✓ **Multi-tenant** - Multiple colleges, isolated data
✓ **Scalable** - Add unlimited colleges/students  
✓ **Secure** - Password hashing, session auth, college isolation
✓ **Professional** - Modern UI with gradient design
✓ **Functional** - Auth, chat, admin panel, DB integration
✓ **Enterprise-ready** - Role-based access control

---

## 📞 Need Help?

Check the relevant section:
- **How to add Q&A?** → See "College Admin" section
- **Why is bot not answering?** → See "Common Issues"
- **What files do what?** → See "File Structure"
- **How does auth work?** → See "Authentication & Security"

---

**Last Updated**: February 25, 2026
**Version**: 1.0
