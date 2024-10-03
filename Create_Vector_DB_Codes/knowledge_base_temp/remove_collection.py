import os
from pymilvus import connections,utility,Collection

# Collection name
# collection_db_name = "UPLIZNA"
collection_db_name = "TARLATAMAB"
# collection_db_name = "OBU_Ted_foundational_publication_500_24jan2024"
#collection_db_name = "OBU_Ted_foundational_publication_500_07Mar2024"

# Connect to Milvus server
connections.connect("default", host="localhost", port="19530")

# Drop collection
utility.drop_collection(collection_db_name)

# List all collections
# collections = utility.list_collections()

# Iterate over all collections
# for collection in collections:
#    # Check if the collection name starts with 'temp_'
    # if collection.startswith('temp_'):
        # Drop the collection
        # utility.drop_collection(collection)
