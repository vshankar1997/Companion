from django.conf import settings
from datetime import datetime, timedelta
from chat_apis.mongo_utils import *
import bson
import logging
logger = logging.getLogger(__name__)


def my_scheduled_job():
    try:
        logger.info('Anonymize job started')
        chat_collection, chat_client = get_collection(settings.MONGO_DB, settings.CHAT_COLLECTION)
        user_collection, user_client = get_collection(settings.MONGO_DB, settings.USER_DETAILS_COLLECTION)
        
        threshold_date = datetime.now() - timedelta(days=30)
        sessions_to_anonymize = chat_collection.find({
            'updated_at':{'$lt':threshold_date},
            'anonymized':{'$exists':False}
        })
        
        anonymized_user_id = bson.ObjectId()
        
        for session in sessions_to_anonymize:
            user = user_collection.find_one({'_id':session['user_id']})
            chat_collection.update_one(
                {'_id': session['_id']},
                {'$set':{
                    'user_id':anonymized_user_id,
                    'anonymized':True,
                    'bu_name': session.get('bu_name', user.get('bu_name'))
                }}
            )
            
        logger.info('Anonymize job completed')
    except Exception as e:
        logger.error(f'Faced following issue while running anonymize job - {e}')
    finally:
        chat_client.close()
        user_client.close()
    return 