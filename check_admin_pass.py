from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI'))
db = client.ambit_db

college = db.colleges.find_one({'college_id': 'ambit'})
if college:
    print(f"College: {college.get('college_name')}")
    print(f"Admin Password: {college.get('admin_password')}")
else:
    print('College not found')
