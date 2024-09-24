from pymilvus import connections,utility,Collection
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get current working directory
cur_path = os.getcwd()
cur_path = cur_path.replace("ai_core/CreateImageKnowledgeBase", "")

connections.connect("default", host=os.environ["MILVUS_HOST"], port=os.environ["MILVUS_PORT"])

# List all collections
collections = utility.list_collections()
print(f"All Collections: {collections} \n")

# Access a specific collection
# collection = Collection("OBU_Ted_foundational_publication_500_24jan2024")
collection = Collection("TEPEZZA_IMAGES")

# Print collection details
print(f"Collection Schema: {collection.schema} \n")
print(f"Collection Description: {collection.description} \n")
print(f"Collection Name: {collection.name} \n")
print(f"Is Collection Empty: {collection.is_empty} \n")
print(f"Number of Entities in Collection: {collection.num_entities} \n")
print(f"Primary Field of Collection: {collection.primary_field} \n")
print(f"Partitions in Collection: {collection.partitions} \n")
print(f"Indexes in Collection: {collection.indexes} \n")
#print(f"Properties of Collection: {collection.properties} \n")