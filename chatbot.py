import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


class AmbitChatbot:
    def __init__(self):
        # 1. Connect to MongoDB using the URI from your .env file
        uri = os.getenv("MONGO_URI")
        self.client = MongoClient(uri)
        self.db = self.client.ambit_db

        # 2. Fetch the Master Data (Matches your screenshot: college_config)
        try:
            config = self.db.college_config.find_one({"type": "master_data"})
            self.knowledge_base = config['data'] if config else {}
        except Exception as e:
            print(f"Error loading master data: {e}")
            self.knowledge_base = {}

    def get_response(self, query):
        query = query.lower().strip()

        # --- IMPROVED DYNAMIC SEARCH ---
        try:
            # We fetch ALL custom Q&A pairs from the database
            all_custom_qa = list(self.db.knowledge_base.find())

            # Debug line
            print(f"DEBUG: Found {len(all_custom_qa)} custom Q&A pairs")

            for item in all_custom_qa:
                # Validate that both 'question' and 'answer' keys exist
                if 'question' not in item or 'answer' not in item:
                    # Debug line
                    print(f"DEBUG: Skipping invalid document: {item}")
                    continue

                # Check if the 'question' keyword exists inside the student's message
                # Example: if item['question'] is "bus" and query is "what is the bus timing"
                if item['question'].lower() in query:
                    # Debug line
                    print(
                        f"DEBUG: Found match for '{item['question']}' in '{query}'")
                    return item['answer']
        except Exception as e:
            print(f"❌ Database search error: {e}")

        # --- ORIGINAL LOGIC (Fallback) ---
        if not self.knowledge_base:
            return "I'm having trouble connecting to my database."

        if 'admission' in query:
            return self._format_admissions()
        elif 'fee' in query:
            return self._format_fees()
        elif 'exam' in query:
            return self._format_exams()
        elif 'contact' in query:
            return self._format_contacts()
        else:
            self.db.unanswered_logs.insert_one({"query": query})
            return self._general_help()

    def _format_admissions(self):
        try:
            data = self.knowledge_base['admissions']['undergraduate']
            return f"Admissions: {', '.join(data['courses'])}. Fees: B.Tech {data['fees']['btech']}."
        except KeyError:
            return "Admission details are currently being updated."

    def _format_fees(self):
        try:
            fees = self.knowledge_base['admissions']['undergraduate']['fees']
            return f"Fees: B.Tech {fees['btech']}, BCA {fees['bca']} (per year)."
        except KeyError:
            return "Fee information is currently unavailable."

    def _format_exams(self):
        try:
            exams = self.knowledge_base['examinations']
            return f"VTU Schedule: {exams['vtu_schedule']['odd_sem']}."
        except KeyError:
            return "Exam schedules are not yet posted."

    def _format_contacts(self):
        try:
            info = self.knowledge_base['college_info']
            return f"Phone: {info['phone']}, Email: {info['email']}, Address: {info['address']}."
        except KeyError:
            return "Contact information not found."

    def _general_help(self):
        return "I can help with admissions, fees, exams, and hostel info. Please ask specifically!"
