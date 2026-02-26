import os
import google.generativeai as genai
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class AmbitChatbot:
    def __init__(self):
        # Setup MongoDB
        uri = os.getenv("MONGO_URI")
        self.client = MongoClient(uri)
        self.db = self.client.ambit_db

        # Setup Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def get_response(self, query, college_id):
        query = query.lower().strip()
        print(f"\n=== BOT QUERY ===\nCollege: {college_id}\nQuery: '{query}'")

        # 1. Search Manual Q&A first (Fastest & Most Accurate for specific FAQs)
        try:
            manual_match = self.db.knowledge_base.find_one({
                "college_id": college_id,
                "type": "manual",
                "question": {"$regex": query, "$options": "i"}
            })
            if manual_match:
                return manual_match['answer']
        except Exception as e:
            print(f"Manual DB error: {e}")

        # 2. Search PDF Content using Gemini (The "Brain" part)
        try:
            # Fetch all PDF extracts for this college
            pdf_docs = list(self.db.knowledge_base.find({
                "college_id": college_id,
                "type": "pdf_content"
            }))

            if pdf_docs:
                # Combine PDF texts into one context (limiting to 10k chars to stay in free tier limits)
                context = "\n".join([doc['answer']
                                    for doc in pdf_docs])[:10000]

                prompt = f"""
                You are an official assistant for {college_id}. 
                Use the following college documents to answer the student's question.
                If the answer isn't in the text, say you don't know and suggest contacting the admin.
                
                Documents: {context}
                Student Question: {query}
                """

                response = self.model.generate_content(prompt)
                return response.text
        except Exception as e:
            print(f"Gemini/PDF error: {e}")

        # 3. Fallback to Master Data (Your original logic)
        try:
            config = self.db.college_config.find_one(
                {"type": "master_data", "college_id": college_id})
            kb = config['data'] if config else {}

            if 'admission' in query:
                return self._format_admissions(kb)
            if 'fee' in query:
                return self._format_fees(kb)
            if 'contact' in query:
                return self._format_contacts(kb)
        except:
            pass

        # 4. Final Fallback: Log for Admin
        self.db.unanswered_logs.insert_one({
            "query": query,
            "college_id": college_id,
            "timestamp": datetime.utcnow()
        })
        return "I'm not quite sure about that. I've sent your query to the college admin for review!"

    def _format_admissions(self, kb):
        try:
            data = kb['admissions']['undergraduate']
            return f"Admissions open for: {', '.join(data['courses'])}. B.Tech Fee: {data['fees']['btech']}."
        except:
            return "Admission details are currently being updated."

    def _format_fees(self, kb):
        try:
            fees = kb['admissions']['undergraduate']['fees']
            return f"Annual Fees: B.Tech: {fees['btech']}, BCA: {fees['bca']}."
        except:
            return "Fee details are not available yet."

    def _format_contacts(self, kb):
        try:
            info = kb['college_info']
            return f"Contact us at {info['phone']} or email {info['email']}."
        except:
            return "Contact information is currently unavailable."
