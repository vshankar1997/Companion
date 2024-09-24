import os
from pymilvus import connections,utility,Collection
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get current working directory
cur_path = os.getcwd()
cur_path = cur_path.replace("ai_core/CreateImageKnowledgeBase", "")

# Collection name
collection_db_name = "TEPEZZA_IMAGES"
# collection_db_name = "OBU_Ted_foundational_publication_500_24jan2024"
#collection_db_name = "OBU_Ted_foundational_publication_500_07Mar2024"

# Connect to Milvus server
connections.connect("default", host=os.environ["MILVUS_HOST"], port=os.environ["MILVUS_PORT"])

# Drop collection
utility.drop_collection(collection_db_name)