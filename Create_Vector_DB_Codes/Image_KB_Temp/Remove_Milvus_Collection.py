import os
from pymilvus import connections,utility,Collection

# Collection name
collection_db_name = "TED_GUIDEBOOK"

# Connect to Milvus server
connections.connect("default", host="localhost", port="19530")

# Drop collection
utility.drop_collection(collection_db_name)