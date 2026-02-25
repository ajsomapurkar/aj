import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


class AmbitChatbot:
    def __init__(self):
        uri = os.getenv("MONGO_URI")
        self.client = MongoClient(uri)
        self.db = self.client.ambit_db

    def get_response(self, query, college_id):
        query = query.lower().strip()
        print(f"\n=== BOT QUERY ===\nCollege: {college_id}\nQuery: '{query}'")

        # 1. Search Custom Q&A for THIS college
        try:
            # We look for keywords belonging only to this specific college
            all_custom_qa = list(self.db.knowledge_base.find(
                {"college_id": college_id}))
            print(f"Found {len(all_custom_qa)} Q&A pairs for {college_id}")
            for item in all_custom_qa:
                if item.get('question'):
                    # Try exact match first, then substring
                    item_question = item['question'].lower().strip()
                    print(
                        f"  Checking: '{item_question}' (len={len(item_question)})")
                    if item_question == query or item_question in query or query in item_question:
                        print(f"  ✓ MATCH! Returning: '{item['answer']}'")
                        return item['answer']
            print(f"  No match found in custom Q&A")
        except Exception as e:
            print(f"Database error: {e}")

        # 2. Search Master Data for THIS college
        try:
            config = self.db.college_config.find_one(
                {"type": "master_data", "college_id": college_id})
            kb = config['data'] if config else {}
        except:
            kb = {}

        # 3. Fallback Logic (using the specific college's data)
        if 'admission' in query:
            return self._format_admissions(kb)
        elif 'fee' in query:
            return self._format_fees(kb)
        elif 'contact' in query:
            return self._format_contacts(kb)
        else:
            # Log unanswered questions so the specific college admin can see them
            self.db.unanswered_logs.insert_one({
                "query": query,
                "college_id": college_id
            })
            return "I'm not sure about that. Try asking about admissions, fees, or contact info."

    def _format_admissions(self, kb):
        try:
            data = kb['admissions']['undergraduate']
            return f"Admissions open for: {', '.join(data['courses'])}. B.Tech Fee: {data['fees']['btech']}."
        except:
            return "Admission details are currently being updated for this campus."

    def _format_fees(self, kb):
        try:
            fees = kb['admissions']['undergraduate']['fees']
            return f"Annual Fees: B.Tech: {fees['btech']}, BCA: {fees['bca']}."
        except:
            return "Fee details are not available for this college yet."

    def _format_contacts(self, kb):
        try:
            info = kb['college_info']
            return f"Contact us at {info['phone']} or email {info['email']}."
        except:
            return "Contact information is currently unavailable."
