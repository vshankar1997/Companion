from django.conf import settings
import boto3
import os
import logging
logger = logging.getLogger(__name__)

class S3Manager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, bucket_name, aws_access_key_id, aws_secret_access_key):
        if not self._initialized:
            self.bucket_name = bucket_name
            self.s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
            self._initialized = True

    def upload_file(self, file_obj, key):
        try:
            self.s3.upload_fileobj(file_obj, self.bucket_name, key)
            print(f"File {key} uploaded successfully.")
        except Exception as e:
            print(f"Error uploading file: {e}")

    def get_file_url(self, key, doc_type):
        try:
            if doc_type == 'pdf':
                url = self.s3.generate_presigned_url('get_object', Params={'Bucket': self.bucket_name, 'Key': key,'ResponseContentDisposition': 'inline','ResponseContentType':'application/pdf'},ExpiresIn=432000)  # 604800 -> 7days
            elif doc_type == 'image':
                url = self.s3.generate_presigned_url('get_object', Params={'Bucket': self.bucket_name, 'Key': key,'ResponseContentDisposition': 'inline','ResponseContentType':'image/png'},ExpiresIn=432000)  # 604800 -> 7days
            return url
        except Exception as e:
            print(f"Error getting file URL: {e}")
            return None
        
    def list_files(self, folder_path):
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=folder_path)
            files = [item['Key'] for item in response.get('Contents', [])]
            return files
        except Exception as e:
            print(f'Error listing files: {e}')
            return []
        
    def get_folder_file_urls(self, folder_path):
        try:
            files = self.list_files(folder_path)
            file_urls = [{os.path.basename(file): self.get_file_url(file, 'pdf')} for file in files[1:]]
            return file_urls
        except Exception as e:
            print(f'Error getting folder file URLs: {e}')
            return []

def get_s3_manager():
    bucket_name = settings.BUCKET_NAME
    aws_access_key_id = settings.AWS_ACCESS_KEY_ID
    aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
    return S3Manager(bucket_name, aws_access_key_id, aws_secret_access_key)

def get_s3_url(s3_manager, doc_name, unit):
    try:
        if unit == 'UPLOADED_DOCS':
            key_in_bucket = f'{unit}/{doc_name}'
            doc_type = 'pdf'
        elif unit == 'IMAGES':
            key_in_bucket = f'{doc_name}' # Considering this is the complete path of the image
            doc_type = 'image'
        else:
            key_in_bucket = f'KNOWLEDGEBASE/{unit}/{doc_name}'
            doc_type = 'pdf'
        file_url = s3_manager.get_file_url(key_in_bucket, doc_type)
        return file_url
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)

def upload_to_s3(s3_manager, file, doc_name):
    try:
        key_in_bucket = f'UPLOADED_DOCS/{doc_name}'
        file.seek(0)
        s3_manager.upload_file(file, key_in_bucket)
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
def list_folder_files_and_urls(s3_manager, folder_path):
    try:
        file_urls = s3_manager.get_folder_file_urls(folder_path)
        return file_urls
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)