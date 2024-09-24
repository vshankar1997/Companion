from pymongo import MongoClient
from django.conf import settings


def get_mongodb_client():
    client = MongoClient(settings.MONGO_CONNECTION_STRING)
    return client

def get_collection(db, collectn):
    client = get_mongodb_client()
    db = client[db]
    collection = db[collectn]
    return collection, client