from pymilvus import MilvusClient
from django.conf import settings

conn = MilvusClient(
    host=settings.MILVUS_HOST,port=settings.MILVUS_PORT, secure=False
)

collectionList = conn.list_collections()
