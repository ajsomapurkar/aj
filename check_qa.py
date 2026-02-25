from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI'))
db = client.ambit_db

# Check what's in knowledge_base for ambit
qa_pairs = list(db.knowledge_base.find({"college_id": "ambit"}))
print(f"Total Q&A pairs for ambit: {len(qa_pairs)}")
for qa in qa_pairs:
    print(f"  Q: {qa.get('question')}")
    print(f"  A: {qa.get('answer')}")
    print()
