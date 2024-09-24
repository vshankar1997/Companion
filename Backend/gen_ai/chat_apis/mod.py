import json
import uuid
import re
import time
from django.conf import settings
from django.http import StreamingHttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from chat_apis.cloud_utils import *
from datetime import datetime, timedelta
from chat_apis.mongo_utils import *
from chat_apis.faq import get_faq_structure
from ai_core.ai_core import *
from bson.objectid import ObjectId
import logging
logger = logging.getLogger(__name__)

def upload_documents(request):
    """
    Uploads documents and performs necessary processing and storage operations.

    Args:
        request (HttpRequest): The HTTP request object containing uploaded files and other data.

    Returns:
        dict: A dictionary containing the status of the upload operation and relevant information.
            - 'status' (str): 'success' if the upload is successful, 'fail' otherwise.
            - 'session_id' (str): The unique identifier for the created chat session (empty string if failed).

    Raises:
        Exception: If an unexpected error occurs during the execution.

    Note:
        This function assumes the existence of helper functions like get_collection(),
        vectorizePdfs(), upload_to_azure(), and appropriate MongoDB collections as specified
        in the importing module.
    """
    try:
        s3_manager = get_s3_manager()
        start_time = datetime.now()
        email = request.POST.get('email')
        bu_name = request.POST.get('user_bu')
        doc_list = list()
        doc_names = list()
        total_file_size = 0
        for file in request.FILES.values():
            uuid_part = '_@_' + str(uuid.uuid4())
            file_name, file_extension = file.name.rsplit('.', 1)
            modified_file_name = f"{file_name}{uuid_part}.{file_extension}"
            file.name = modified_file_name
            doc_list.append(file)
            doc_names.append(file.name)
            total_file_size += file.size
        
        user_collection, user_client = get_collection(settings.MONGO_DB, settings.USER_DETAILS_COLLECTION)
        user = user_collection.find_one({'email':email})
        
        chat_collection, client = get_collection(settings.MONGO_DB, settings.CHAT_COLLECTION)            
    
        chat = {
            'chat_name':'New Chat',
            'chat_status':'active',
            'user_id':ObjectId(user['_id']),
            'bu_name': bu_name,
            'created_at':datetime.now(),
            'updated_at':datetime.now()
        }
        temp = chat_collection.insert_one(chat)
        session_id = temp.inserted_id
        user_client.close()
        client.close()
        
        s3_start_time = datetime.now()
        for doc in doc_list:
            upload_to_s3(s3_manager, doc, doc.name)
        s3_end_time = datetime.now()
        
        gen_ai_start_time = datetime.now()
        data = vectorizePdfs(doc_names,str(session_id))
        gen_ai_end_time = datetime.now()

        if data['status'] == 'Success':
            
            meta_collection, meta_client = get_collection(settings.MONGO_DB, settings.UPLOAD_META_COLLECTION)
            end_time = datetime.now()
            payload = {
                'files': doc_names,
                'vector_details':data['message'],
                'session_id':session_id,
                'created_at':datetime.now(),
                'total_file_size':total_file_size,
                'upload_total_time': int((end_time-start_time).total_seconds()),
                'textract_extraction_time':data['textract_extraction_time'],
                'vectorization_time':data['vectorization_time'],
                'gen_ai_total_time': int((gen_ai_end_time-gen_ai_start_time).total_seconds()),
                's3_upload_time':int((s3_end_time-s3_start_time).total_seconds())
            }
            meta = meta_collection.insert_one(payload)
            meta_client.close()
            return {'status':'success','session_id':session_id}
        return {'status':'fail','session_id':''}
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)

@csrf_exempt
@require_POST
def chat_prompt_streaming(request):
    try:
        params = json.loads(request.body)
        s3_manager = get_s3_manager()
        prompt = params.get('prompt')
        session_id = params.get('session_id')
        regenerate = params.get('regenerate')
        bu_name = params.get('user_bu')
        is_upload = params.get('is_upload')
        document_names = list()
        
        if is_upload:
            meta_collection,meta_client = get_collection(settings.MONGO_DB, settings.UPLOAD_META_COLLECTION)
            doc_obj = meta_collection.find_one({'session_id':ObjectId(session_id)})
            document_names = doc_obj.get('files')
            meta_client.close()
        
        isTitle = False
        if (session_id is None) or (session_id == ''):
            email = params.get('email')
            user_collection, user_client = get_collection(settings.MONGO_DB, settings.USER_DETAILS_COLLECTION)
            user = user_collection.find_one({'email':email})
            
            chat_collection, client = get_collection(settings.MONGO_DB, settings.CHAT_COLLECTION)            
            current_date = datetime.now().strftime("%d %B, %Y")
            chat_name = f'New Chat - {current_date}'
            chat = {
                'chat_name':chat_name,
                'chat_status':'active',
                'user_id':ObjectId(user['_id']),
                'bu_name': bu_name,
                'created_at':datetime.now(),
                'updated_at':datetime.now()
            }
            res = chat_collection.insert_one(chat)
            isTitle = True
            session_id = res.inserted_id
            user_client.close()
            client.close()
        else:
            session_id = ObjectId(session_id)
        chat_history = list()
        
        list_of_n_msgs,msg_client_in = get_last_nrecords_from_msgcollection(5,session_id)
        reversed_records = list(reversed(list(list_of_n_msgs)))
        for data in reversed_records:
            chat_history.append({'role':'user','content':data['prompt']})
            chat_history.append({'role':'AI','content':data['message']})
        msg_client_in.close()
        
        if regenerate and len(chat_history)>1:
            prompt = chat_history[-2]['content']        
        
        def event_stream(isTitle):
            llm_call_start_time = datetime.now()
            result = own_chat_ai_call(prompt, chat_history, bu_name, session_id, regenerate, is_upload, document_names)
            llm_call_end_time = datetime.now()
            llm_call_time = (llm_call_end_time - llm_call_start_time).total_seconds()
            accumulated_data = ''
            
            if result['is_stream']:
                stream_start_time = datetime.now()
                for chunk in result['message']:
                    content = chunk.choices[0].delta.content
                    
                    if content is not None:
                        
                        formatted_content = content.replace("'","<quote>")
                        formatted_content = formatted_content.replace('"',"<double>")
                        data = {"type":"answer", "data": f"{formatted_content}"}
                        yield f'{data}@@\n\n'
                        accumulated_data += content   
                    else:
                        
                        stream_end_time = datetime.now()
                        chat_collection, client = get_collection(settings.MONGO_DB, settings.CHAT_COLLECTION)
                        chat_obj = chat_collection.find_one({"_id": ObjectId(session_id)},{"chat_name": 1})
                        if isTitle or (chat_obj and chat_obj.get("chat_name") == "New Chat"):
                            title_data = generate_chat_title(prompt, accumulated_data)
                            isTitle = True
                            if title_data.get('title'):
                                update_chat_name(session_id, title_data.get('title'))
                        client.close()
                        
                        if regenerate:
                            result['regenerate'] = regenerate
                        result['message'] = accumulated_data
                        result['session_id'] = session_id
                        result['prompt'] = prompt
                        result['created_at'] = datetime.now()
                        result['updated_at'] = datetime.now()
                        result['llm_call_time'] = llm_call_time
                        result['streaming_response_time'] = (stream_end_time - stream_start_time).total_seconds()

                        if result['source'] != []:
                            for doc in result['source']:
                                if doc['flag'] != 'Internal':
                                    doc['url'] = get_s3_url(s3_manager, doc['DocumentName'],'UPLOADED_DOCS')
                                else:
                                    doc['url'] = get_s3_url(s3_manager, doc['DocumentName'],bu_name)
                                    
                        if result['image_details'] != []:
                            for image in result['image_details']:
                                image['url'] = get_s3_url(s3_manager, image['path'], 'IMAGES')
                                image['document_url'] = get_s3_url(s3_manager, image['document_name'], bu_name)
                                image['source'] = 'internal'
                                    
                        capture_recent_session_updated_at(session_id)
                        chat_msg_collection, msg_client = get_collection(settings.MONGO_DB, settings.CHAT_MSG_COLLECTION)
                        msg_record = chat_msg_collection.insert_one(result.copy())
                        result['msg_id'] = msg_record.inserted_id
                        msg_client.close()
                                    
                        data = {"type":"source", "data": str(result['msg_id'])}
                        
                        yield f"{json.dumps(data)}"
                        break
                    time.sleep(0.02)
                    
            else:
                
                chat_collection, client = get_collection(settings.MONGO_DB, settings.CHAT_COLLECTION)
                chat_obj = chat_collection.find_one({"_id": ObjectId(session_id)},{"chat_name": 1})
                if isTitle or (chat_obj and chat_obj.get("chat_name") == "New Chat"):
                    title_data = generate_chat_title(prompt, accumulated_data)
                    isTitle = True
                    if title_data.get('title'):
                        update_chat_name(session_id, title_data.get('title'))
                client.close()
                
                if result['image_details'] != []:
                    for image in result['image_details']:
                        image['url'] = get_s3_url(s3_manager, image['path'], 'IMAGES')
                        image['document_url'] = get_s3_url(s3_manager, image['document_name'], bu_name)
                        image['source'] = 'internal'
                
                if regenerate:
                    result['regenerate'] = regenerate
                result['session_id'] = session_id
                result['prompt'] = prompt
                result['created_at'] = datetime.now()
                result['updated_at'] = datetime.now()
                result['llm_call_time'] = llm_call_time
                
                capture_recent_session_updated_at(session_id)
                chat_msg_collection, msg_client = get_collection(settings.MONGO_DB, settings.CHAT_MSG_COLLECTION)
                msg_record = chat_msg_collection.insert_one(result.copy())
                result['msg_id'] = msg_record.inserted_id
                msg_client.close()
                
                data1 = {"type":"answer", "msg_id": str(result['msg_id'])}
                
                yield f'{data1}@@\n\n'
                
        response = StreamingHttpResponse(event_stream(isTitle), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        return response
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)

def get_last_nrecords_from_msgcollection(n, session_id):
    chatmsg_collection, msg_client = get_collection(settings.MONGO_DB, settings.CHAT_MSG_COLLECTION)
    last_n_updated_records = chatmsg_collection.find({'session_id':session_id}).sort([('_id', -1)]).limit(n)
    return last_n_updated_records, msg_client

def post_faq(request):
    try:
        collection, client = get_collection(settings.MONGO_DB, settings.FAQ_COLLECTION)
        data = get_faq_structure()
        result = collection.insert_one(data)
        chat_info = collection.find_one({'_id': result.inserted_id})
        client.close()
        return {'chat_id':chat_info}
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)


def get_users_details(request):
    try:
        collection, client = get_collection(settings.MONGO_DB, settings.USER_DETAILS_COLLECTION)
        result = list(collection.find())
        client.close()
        return result
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
def create_user_details(request,params):
    try:
        collection, client = get_collection(settings.MONGO_DB, settings.USER_DETAILS_COLLECTION)
        data = {
            'username': params.get('username'),
            'email': params.get('email'),
            'created_at': datetime.now()
        }
        result = collection.insert_one(data)
        client.close()
        return "User details are saved!!"
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
def get_user_details(request,user_id):
    try:
        user_id = ObjectId(user_id)
        collection, client = get_collection(settings.MONGO_DB, settings.USER_DETAILS_COLLECTION)
        result = collection.find_one({"_id": user_id})
        client.close()
        return result
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
def update_user_details(request,params,user_id):
    try:
        user_id = ObjectId(user_id)
        collection, client = get_collection(settings.MONGO_DB, settings.USER_DETAILS_COLLECTION)
        update_operation = {
            "$set": {
                "username": params.get('username'),
                "email": params.get('email')
            }
        }
        result = collection.update_one({"_id": user_id}, update_operation)
        client.close()
        return "User details are updated!!"
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
def delete_user_details(request,user_id):
    try:
        user_id = ObjectId(user_id)
        collection, client = get_collection(settings.MONGO_DB, settings.USER_DETAILS_COLLECTION)
        result = collection.delete_one({"_id": user_id})
        client.close()
        return "User details are deleted!!"
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
    
def validate_login(request,params):
    try:
        user_mail = params.get('email').lower()
        collection,client = get_collection(settings.MONGO_DB, settings.USER_DETAILS_COLLECTION)
        if collection.find_one({"email": user_mail}) is not None:
            state = 'success'
        else:
            state ='fail'
        client.close()    
        return state
        
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)


def update_feedback(request,params):
    try:
        msg_id = params.get('msg_id')
        update_dict = dict()
        collection,client = get_collection(settings.MONGO_DB, settings.CHAT_MSG_COLLECTION)
        
        if 'rating' in params.keys():
            rating = int(params.get('rating'))
            update_dict['rating'] = rating
            
        if 'feedback' in params.keys():
            feedback = params.get('feedback')
            update_dict['feedback'] = feedback
            
        if 'tag_ratings' in params.keys():
            tag_ratings = params.get('tag_ratings')
            update_dict['tag_ratings'] = tag_ratings 
            
        update_query = {'$set': update_dict} 
        output = collection.update_one({'_id': ObjectId(msg_id)}, update_query, upsert=True)
        
        updated_document = collection.find_one({'_id': ObjectId(msg_id)})
        capture_recent_session_updated_at(updated_document.get('session_id'))
        client.close()
        return "Thank you for your feedback!"
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
def image_feedback(request,params):
    try:
        msg_id = params.get('msg_id')
        img_id = int(params.get('img_id'))
        rating = int(params.get('rating'))
        
        collection,client = get_collection(settings.MONGO_DB, settings.CHAT_MSG_COLLECTION)
        
        result = collection.update_one(
            {
                '_id': ObjectId(msg_id),
                'image_details.img_id': img_id
            },
            {
                '$set':{
                    'image_details.$.rating': rating
                }
            }
        )
        updated_document = collection.find_one({'_id': ObjectId(msg_id)})
        capture_recent_session_updated_at(updated_document.get('session_id'))
        client.close()
        return "Thank you for your feedback!"
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
    
def config_details(request, params):
    try:
        result_dict = {
            "upload_rate": get_upload_rate(),
            "history_list": get_chat_history(params.get("email")),
            "user_bu": get_user_bu(params.get("email")),
            "bu_list": list_sub_bu(params.get("email"))
        }
        
        return result_dict
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
def get_chat_history(email):
    try:
        user_collection,user_client = get_collection(settings.MONGO_DB, settings.USER_DETAILS_COLLECTION)
        chat_collection,chat_client = get_collection(settings.MONGO_DB, settings.CHAT_COLLECTION)
        meta_collection,meta_client = get_collection(settings.MONGO_DB, settings.UPLOAD_META_COLLECTION)
        user = user_collection.find_one({'email':email})
        today_ago = datetime.now().replace(hour=0, minute=0, second=0)
        yesterday_ago = datetime.now().replace(hour=0, minute=0, second=0) - timedelta(days=1)
        seven_days_ago = datetime.now().replace(hour=0, minute=0, second=0) - timedelta(days=7)
        thirty_days_ago = datetime.now().replace(hour=0, minute=0, second=0) - timedelta(days=30)
        today_data = chat_collection.find({
            'user_id': user.get("_id"),
            'updated_at': {'$gte': today_ago}
        }).sort([("updated_at", -1)])
        yesterday_data = chat_collection.find({
            'user_id': user.get("_id"),
            'updated_at': {'$gte': yesterday_ago, '$lt': today_ago}
        }).sort([("updated_at", -1)])
        seven_days_data = chat_collection.find({
            'user_id': user.get("_id"),
            'updated_at': {'$gte': seven_days_ago, '$lt': yesterday_ago}
        }).sort([("updated_at", -1)])
        thirty_days_data = chat_collection.find({
            'user_id': user.get("_id"),
            'updated_at': {'$gte': thirty_days_ago, '$lt': seven_days_ago}
        }).sort([("updated_at", -1)])
        today = []
        yesterday = []
        seven_days = []
        thirty_days = []
        for today_session in today_data:
            document = meta_collection.find_one({"session_id": today_session.get("_id")})
            today.append({
                "session_id": today_session.get("_id"),
                "chat_title": today_session.get("chat_name"),
                "isUpload" : document is not None
            })
        for yesterday_session in yesterday_data:
            document = meta_collection.find_one({"session_id": yesterday_session.get("_id")})
            yesterday.append({
                "session_id": yesterday_session.get("_id"),
                "chat_title": yesterday_session.get("chat_name"),
                "isUpload" : document is not None
            })
        for seven_session in seven_days_data:
            document = meta_collection.find_one({"session_id": seven_session.get("_id")})
            seven_days.append({
                "session_id": seven_session.get("_id"),
                "chat_title": seven_session.get("chat_name"),
                "isUpload" : document is not None
            })
        for thirty_session in thirty_days_data:
            document = meta_collection.find_one({"session_id": thirty_session.get("_id")})
            thirty_days.append({
                "session_id": thirty_session.get("_id"),
                "chat_title": thirty_session.get("chat_name"),
                "isUpload" : document is not None
            })
        history_list = {
            "today": today,
            "yesterday": yesterday,
            "seven_days": seven_days,
            "thirty_days": thirty_days
        }
        
        user_client.close()
        chat_client.close()
        meta_client.close()
        return history_list
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
def get_upload_rate():
    try:
        meta_collection,meta_client = get_collection(settings.MONGO_DB, settings.UPLOAD_META_COLLECTION)
        cutoff_date = datetime.now()
        result = meta_collection.aggregate([
        {
            "$match": {
                "created_at": {"$lte": cutoff_date},
                "upload_total_time": {"$exists": True}
            }
        },
        {
            "$sort": {"created_at": -1}  # Sort by created_at in descending order
        },
        {
            "$limit": 10  # Limit to the last 10 documents
        },
        {
            "$group": {
                "_id": None,
                "total_file_size_sum": {"$sum": "$total_file_size"},
                "upload_document_time_sum": {"$sum": "$upload_total_time"},
            }
        }
    ])
        
        result_data = list(result)
        total_file_size_sum = result_data[0]["total_file_size_sum"]
        upload_document_time_sum = result_data[0]["upload_document_time_sum"]
        meta_client.close()
        return (total_file_size_sum//upload_document_time_sum) if  upload_document_time_sum!=0 else 32500
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
def post_user_feedback(request,params):
    try:
        user_mail = params.get('email').lower()
        feedback = params.get('feedback')
        rating = params.get('rating')
        collection,user_client = get_collection(settings.MONGO_DB, settings.USER_DETAILS_COLLECTION)
        user = collection.find_one({'email':user_mail})
        feedback_form = {
            'user_id':ObjectId(user['_id']),
            'feedback':feedback,
            'rating':rating,
            'created_at':datetime.now(),
        }
        feedback_collection,feedback_client = get_collection(settings.MONGO_DB, settings.FEEDBACK_COLLECTION)
        feedback_record = feedback_collection.insert_one(feedback_form.copy())
        
        user_client.close()
        feedback_client.close()
        return "Thank you for your feedback!"
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
def update_chat_name(session_id, title):
    try:
        chat_collection,chat_client = get_collection(settings.MONGO_DB, settings.CHAT_COLLECTION)
        query = {"_id": ObjectId(session_id)}
        update_values = {
            "$set": {
                "chat_name": title
            }
        }
        chat_collection.update_one(query, update_values)
        chat_client.close()
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
def get_session_messages(request,session_id):
    try:
        chatmsg_collection, msg_client = get_collection(settings.MONGO_DB, settings.CHAT_MSG_COLLECTION)
        meta_collection, meta_client = get_collection(settings.MONGO_DB, settings.UPLOAD_META_COLLECTION)
        chat_collection,chat_client = get_collection(settings.MONGO_DB, settings.CHAT_COLLECTION)
        user_collection,user_client = get_collection(settings.MONGO_DB, settings.USER_DETAILS_COLLECTION)
        files = []
        
        chat_session = chat_collection.find_one({'_id': ObjectId(session_id)})
        chat_name = chat_session.get('chat_name')
        user_document = user_collection.find_one({'_id':chat_session.get('user_id')})
        bu_name = chat_session.get('bu_name') if chat_session.get('bu_name') else user_document.get('bu_name')
        last_updated_records = chatmsg_collection.find({'session_id':ObjectId(session_id)}).sort([('_id', 1)])
        final_list = list(last_updated_records)
        
        for data in final_list:
            for val in data['image_details']:
                val['img_id'] = str(val['img_id'])
        
        session_exists = meta_collection.count_documents({'session_id': ObjectId(session_id)}) > 0
        if session_exists:
            obj = meta_collection.find_one({'session_id': ObjectId(session_id)})
            files.extend(obj.get('files'))
        
        msg_client.close()
        meta_client.close()
        chat_client.close()
        user_client.close()
        return {'final_list': final_list, 'files': files, 'chat_name':chat_name, 'user_bu': bu_name}

    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
    
def capture_recent_session_updated_at(session_id):
    try:
        chat_collection,chat_client = get_collection(settings.MONGO_DB, settings.CHAT_COLLECTION)
        query = {"_id": ObjectId(session_id)}
        update_values = {
            "$set": {
                "updated_at": datetime.now()
            }
        }
        chat_collection.update_one(query, update_values)
        chat_client.close()
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
def get_user_bu(email):
    try:
        user_collection,user_client = get_collection(settings.MONGO_DB, settings.USER_DETAILS_COLLECTION)
        document = user_collection.find_one({'email':email})
        bu_name = document.get('bu_name')
        user_client.close()
        return bu_name
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
def get_response_from_session(request,msg_id):
    try:
        chatmsg_collection, msg_client = get_collection(settings.MONGO_DB, settings.CHAT_MSG_COLLECTION)
        chat_collection,chat_client = get_collection(settings.MONGO_DB, settings.CHAT_COLLECTION)
        document = chatmsg_collection.find_one({'_id':ObjectId(msg_id)})
        session_document = chat_collection.find_one({'_id': ObjectId(document.get('session_id'))})
        
        for val in document['image_details']:
                val['img_id'] = str(val['img_id'])
        
        document['chat_title'] = session_document.get('chat_name')
        msg_client.close()
        chat_client.close()
        return document
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
def list_bu_documents(request,bu_name):
    try:
        s3_manager = get_s3_manager()
        folder_path = f"KNOWLEDGEBASE/{bu_name}/"
        response = list_folder_files_and_urls(s3_manager, folder_path)
        return response
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)
    
def list_sub_bu(email):
    try:
        sub_bu_collection, sub_bu_client = get_collection(settings.MONGO_DB, settings.SUB_COLLECTION)
        bu_name = get_user_bu(email)
        document = sub_bu_collection.find_one({'bu_name':bu_name})
        sub_bu_list = document.get('sub_bu')
        
        sub_bu_client.close()
        return sub_bu_list if sub_bu_list else []
    except Exception as e:
        logger.error(f'{e}')
        raise Exception(e)