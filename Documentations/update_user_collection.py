import pandas as pd
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime


mongo_uri = "mongodb://localhost:27017/"
client = MongoClient(mongo_uri)
db = client["genai"]
collection = db["user_details"]


def insert_or_update_document(row):
    email = row["Email ID"]
    existing_doc = collection.find_one({"email": email})


    if existing_doc:
        update_data = {
            "$set": {
                "username": row["Name"],
                "bu_name": row["BU Name"],
                "user_type": row["Type"],
                "created_at": datetime.now()
            }
        }
        collection.update_one({"_id": ObjectId(existing_doc["_id"])}, update_data)
        print(f"Updated document for email: {email}")
    else:
        new_document = {
            "username": row["Name"],
            "email": email,
            "bu_name": row["BU Name"],
            "user_type": row["Type"],
            "created_at": datetime.now()
        }
        collection.insert_one(new_document)
        print(f"Inserted new document for email: {email}")


csv_file_path = "app_users.csv"
df = pd.read_csv(csv_file_path)


for index, row in df.iterrows():
    insert_or_update_document(row)

client.close()