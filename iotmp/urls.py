"""MyJenkins URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
#from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^$', views.index, name='iotmp_index'),
    url(r'^version/new/', views.version_new, name='version_new'),
    url(r'^version/del/(?P<id>\d+)/', views.version_del, name='version_del'),
    url(r'^version/delfile/(?P<id>\d+)/(?P<fid>\d+)', views.version_delfile, name='version_delfile'),
    url(r'^version/files/(?P<id>\d+)/', views.version_files, name='version_files'),
    url(r'^version/', views.version, name='version_list'),

    url(r'^host/new/', views.host_new, name='host_new'),
    url(r'^host/del/(?P<id>\d+)/', views.host_del, name='host_del'),
    url(r'^host/', views.host, name='host_list'),

    url(r'^hostgroup/new/', views.hostgroup_new, name='hostgroup_new'),
    url(r'^hostgroup/del/(?P<mysql_ip>\d+.\d+.\d+.\d+)/', views.hostgroup_del, name='hostgroup_del'),
    url(r'^hostgroup/', views.hostgroup, name='hostgroup_list'),


    url(r'^server/install/select_env/(?P<mysql_ip>\d+.\d+.\d+.\d+)/', views.select_env, name='select_env'),
    url(r'^server/install/', views.install, name='install'),


    url(r'^server/host/del/(?P<ip>\d+.\d+.\d+.\d+)/(?P<server_name>\w+)/', views.server_host_del, name='server_host_del'),
    url(r'^server/info/del/(?P<ip>\d+.\d+.\d+.\d+)/', views.server_info_del, name='server_info_del'),
    url(r'^server/info/(?P<host_ip>\d+.\d+.\d+.\d+)/', views.server_host, name='server_host'),
    url(r'^server/info/', views.server_info, name='server_info'),
    url(r'^server/check/(?P<ip>\d+.\d+.\d+.\d+)/(?P<server_name>\w+)/', views.server_check, name='server_check'),

    url(r'^tasks/log/(?P<id>\d+)/', views.tasks_log, name='tasks_log'),
    url(r'^tasks/run/', views.tasks_run, name='tasks_run'),
    url(r'^tasks/success/', views.tasks_success, name='tasks_success'),
    url(r'^tasks/failed/', views.tasks_failed, name='tasks_failed'),
    url(r'^tasks/del/(?P<id>\d+)/', views.tasks_del, name='tasks_del'),
    url(r'^tasks/', views.tasks, name='tasks'),

    # url(r'^new/(?P<model_name>[\w_][\w\d_]*)/', views.new_obj, name="new_obj"), #字母或_开头，后面是字母数字_，重复0+次,区分大小写
    # url(r'^del/(?P<model_name>[\w_][\w\d_]*)/(?P<obj_id>\d+)/', views.del_obj, name="del_obj"),
    # url(r'^update/(?P<model_name>[\w_][\w\d_]*)/(?P<obj_id>\d+)/', views.update_obj, name="update_obj"),
    # url(r'^select/(?P<model_name>[\w_][\w\d_]*)/', views.select_model, name="select_model"),

]
