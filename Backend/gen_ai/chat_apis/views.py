from django.shortcuts import render

# Create your views here.

# Using views file as tastypie's resource module
from tastypie.resources import Resource
from django.urls import re_path as url
from django.conf import settings

from chat_apis.mongo_utils import *
from chat_apis.mod import *

class FAQ(Resource):
    class Meta:
        resource_name = 'faq'

    def prepend_urls(self):
        return [
            url(r'^(?P<resource_name>%s)$' % (self._meta.resource_name),
                self.wrap_view('faq_root_operations'), name='api_faq_root_operations'),
        ]
        
    def faq_root_operations(self, request, *args, **kwargs):
        self.method_check(request, allowed=['get','post'])
        try:
            if request.method == 'GET':
                collection, client = get_collection(settings.MONGO_DB, settings.FAQ_COLLECTION)
                result = collection.find()[0]
                client.close()
            elif request.method == 'POST':
                result = post_faq(request)
            return self.create_response(request, {'success': True, 'is_exists': False, 'status': 'success', 'data': result})
        except Exception as e:
            return self.error_response(request, {'success': False, 'status': 'failed', 'message': str(e)})
        
class USER(Resource):
    class Meta:
        resource_name = 'users'

    def prepend_urls(self):
        return [
            url(r'^(?P<resource_name>%s)$' % (self._meta.resource_name),
                self.wrap_view('user_prompt_root_operations'), name='api_user_prompt_root_operations'),
            url(r'^(?P<resource_name>%s)/validate$' % (self._meta.resource_name),
                self.wrap_view('user_validate_unit_operations'), name='api_user_validate_unit_operations'),
            url(r'^(?P<resource_name>%s)/feedback$' % (self._meta.resource_name),
                self.wrap_view('user_feedback_operations'), name='api_feedback_operations'),
            url(r'^(?P<resource_name>%s)/(?P<serial_id>[\w]+)$' % (self._meta.resource_name),
                self.wrap_view('user_prompt_unit_operations'), name='api_user_prompt_unit_operations'),
        ]
        
    def user_prompt_root_operations(self, request, *args, **kwargs):
        self.method_check(request, allowed=['get','post'])
        try:
            if request.method == 'GET':
                result = get_users_details(request)
            elif request.method == 'POST':
                params = json.loads(request.body)
                result = create_user_details(request,params)
            return self.create_response(request, {'success': True, 'is_exists': False, 'status': 'success', 'data': result})
        except Exception as e:
            return self.error_response(request, {'success': False, 'status': 'failed', 'message': str(e)})

    def user_validate_unit_operations(self, request, *args, **kwargs):
        self.method_check(request, allowed=['post'])
        try:
            if request.method == 'POST':
                params = json.loads(request.body)
                result = validate_login(request,params)            
                return self.create_response(request, {'success': True, 'is_exists': False, 'status': 'success', 'data': result})
        except Exception as e:
            return self.error_response(request, {'success': False, 'status': 'failed', 'message': str(e)})

    def user_feedback_operations(self, request, *args, **kwargs):
        self.method_check(request, allowed=['post'])
        try:
            if request.method == 'POST':
                params = json.loads(request.body)
                result = post_user_feedback(request,params)            
                return self.create_response(request, {'success': True, 'is_exists': False, 'status': 'success', 'data': result})
        except Exception as e:
            return self.error_response(request, {'success': False, 'status': 'failed', 'message': str(e)})

    def user_prompt_unit_operations(self, request, *args, **kwargs):
        self.method_check(request, allowed=['get','put','delete'])
        try:
            try:
                serial_id = self.remove_api_resource_names(kwargs)['serial_id']
            except:
                raise Exception('Invalid serial ID')
            
            if request.method == 'GET':
                result = get_user_details(request,serial_id)
            elif request.method == 'PUT':
                params = json.loads(request.body)
                result = update_user_details(request,params,serial_id)
            elif request.method == 'DELETE':
                result = delete_user_details(request,serial_id)
                
            return self.create_response(request, {'success': True, 'is_exists': False, 'status': 'success', 'data': result})
        except Exception as e:
            return self.error_response(request, {'success': False, 'status': 'failed', 'message': str(e)})

class ChatPrompt(Resource):
    class Meta:
        resource_name = 'chat_prompt'

    def prepend_urls(self):
        return [
            url(r'^(?P<resource_name>%s)/(?P<msg_id>[\w]+)$' % (self._meta.resource_name),
                self.wrap_view('chat_prompt_root_operations'), name='api_chat_prompt_root_operations'),
        ]
        
    def chat_prompt_root_operations(self, request, *args, **kwargs):
        self.method_check(request, allowed=['get'])
        try:
            try:
                msg_id = self.remove_api_resource_names(kwargs)['msg_id']
            except:
                raise Exception('Invalid serial ID')
            
            if request.method == 'GET':
                result = get_response_from_session(request,msg_id)
                return self.create_response(request, {'success': True, 'is_exists': False, 'status': 'success', 'data': result})
        except Exception as e:
            return self.error_response(request, {'success': False, 'status': 'failed', 'message': str(e)})
        

class UploadPrompt(Resource):
    class Meta:
        resource_name = 'upload_prompt'

    def prepend_urls(self):
        return [
            url(r'^(?P<resource_name>%s)/upload$' % (self._meta.resource_name),
                self.wrap_view('upload_operations'), name='api_upload_operations'),
        ]
        
    def upload_operations(self, request, *args, **kwargs):
        self.method_check(request, allowed=['post'])
        try:
            if request.method == 'POST':
                result = upload_documents(request)
                return self.create_response(request, {'success': True, 'is_exists': False, 'status': 'success', 'data': result})
        except Exception as e:
            return self.error_response(request, {'success': False, 'status': 'failed', 'message': str(e)})       

class UploadFeedback(Resource):
    class Meta:
        resource_name = 'feedback'

    def prepend_urls(self):
        return [
            url(r'^(?P<resource_name>%s)$' % (self._meta.resource_name),
                self.wrap_view('user_feedback_operations'), name='api_user_feedback_operations'),
            url(r'^(?P<resource_name>%s)/image$' % (self._meta.resource_name),
                self.wrap_view('image_feedback_operations'), name='api_image_feedback_operations'),
        ]
        
    def user_feedback_operations(self, request, *args, **kwargs):
        self.method_check(request, allowed=['put'])
        try:
            if request.method == 'PUT':
                params = json.loads(request.body)
                result = update_feedback(request,params)
                return self.create_response(request, {'success': True, 'is_exists': False, 'status': 'success', 'data': result})
        except Exception as e:
            return self.error_response(request, {'success': False, 'status': 'failed', 'message': str(e)})
        
    def image_feedback_operations(self, request, *args, **kwargs):
        self.method_check(request, allowed=['put'])
        try:
            if request.method == 'PUT':
                params = json.loads(request.body)
                result = image_feedback(request,params)
                return self.create_response(request, {'success': True, 'is_exists': False, 'status': 'success', 'data': result})
        except Exception as e:
            return self.error_response(request, {'success': False, 'status': 'failed', 'message': str(e)})
        

class Config(Resource):
    class Meta:
        resource_name = 'config'

    def prepend_urls(self):
        return [
            url(r'^(?P<resource_name>%s)$' % (self._meta.resource_name),
                self.wrap_view('config_root_operations'), name='api_config_root_operations'),
            url(r'^(?P<resource_name>%s)/doc_list/(?P<bu_name>[\w]+)$' % (self._meta.resource_name),
                self.wrap_view('doc_list_operations'), name='api_doc_list_operations'),
            url(r'^(?P<resource_name>%s)/history/(?P<session_id>[\w]+)/$' % (self._meta.resource_name),
                self.wrap_view('chat_history_operations'), name='api_chat_history_operations'),
        ]
        
    def config_root_operations(self, request, *args, **kwargs):
        self.method_check(request, allowed=['post'])
        try:
            if request.method == 'POST':
                params = json.loads(request.body)
                result = config_details(request, params)
                return self.create_response(request, {'success': True, 'is_exists': False, 'status': 'success', 'data': result})
        except Exception as e:
            return self.error_response(request, {'success': False, 'status': 'failed', 'message': str(e)})
        
    def doc_list_operations(self, request, *args, **kwargs):
        self.method_check(request, allowed=['get'])
        try:
            if request.method == 'GET':
                bu_name = self.remove_api_resource_names(kwargs)['bu_name']
                result = list_bu_documents(request, bu_name)
                return self.create_response(request, {'success': True, 'is_exists': False, 'status': 'success', 'data': result})
        except Exception as e:
            return self.error_response(request, {'success': False, 'status': 'failed', 'message': str(e)})
        
    def chat_history_operations(self,request,*args,**kwargs):
        self.method_check(request, allowed=['get'])
        try:
            session_id = self.remove_api_resource_names(kwargs)['session_id']
            if request.method == 'GET':
                session = get_session_messages(request, session_id)
                return self.create_response(request, {'success': True, 'is_exists': False, 'status': 'success', 'data': session['final_list'], 'files':session['files'], 'chat_name': session['chat_name'], 'user_bu': session['user_bu']})
        except Exception as e:
            return self.error_response(request, {'success': False, 'status': 'failed', 'message': str(e)})