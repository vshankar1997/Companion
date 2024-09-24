"""
URL configuration for gen_ai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.urls import re_path as url
from tastypie.api import Api
from chat_apis.views import *
from chat_apis.mod import chat_prompt_streaming

admin.autodiscover()
v1_api = Api(api_name='v1')
v1_api.register(FAQ())
v1_api.register(ChatPrompt())
v1_api.register(UploadPrompt())
v1_api.register(USER())
v1_api.register(UploadFeedback())
v1_api.register(Config())

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/stream_data/',chat_prompt_streaming, name='stream_data'),
    url(r'^api/', include(v1_api.urls)),
]