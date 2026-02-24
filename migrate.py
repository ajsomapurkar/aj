import os
from pymongo import MongoClient
from dotenv import load_dotenv
# This reaches into your existing file to grab the data
from knowledge_base import COLLEGE_DATA

load_dotenv()

# Connect to your new MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client.ambit_db


def push_data_to_cloud():
    # We save the dictionary under the 'type': 'master_data' so the bot can find it later
    db.college_config.update_one(
        {"type": "master_data"},
        {"$set": {"data": COLLEGE_DATA}},
        upsert=True
    )
    print("✅ Success! Your COLLEGE_DATA is now in the MongoDB Cloud.")


if __name__ == "__main__":
    push_data_to_cloud()
