"""StudentsManager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('index/', views.get_index, name='index'),
    path('stu_score/', views.get_stu_score, name='stu_score'),
    path('stu_course/', views.get_stu_course, name='stu_course'),
    path('stu_select_course/', views.stu_select_course, name='stu_select_course'),
    path('new_course/', views.new_course, name='new_course'),
    path('delete_course/', views.delete_course, name='delete_course'),
    path('update_course_detail/', views.update_course_detail, name='update_course_detail'),
    path('tea_update_score/', views.tea_update_score, name='tea_update_score'),
    path('stu_scheduler/', views.get_stu_scheduler, name='stu_scheduler'),
    path('tea_scheduler/', views.get_tea_scheduler, name='tea_scheduler'),
    path('tea_course/', views.get_tea_course, name='tea_course'),
    path('tea_course_detail/', views.get_tea_course_detail,  name='tea_course_detail'),
    path('jw_students/', views.get_jw_students, name='jw_students'),
    path('stu_quit_course/', views.stu_quit_course, name='stu_quit_course'),
    path('new_user/', views.new_user, name='new_user'),
    path('set_user_description/', views.set_user_description, name='set_user_description'),
    path('login_student/', views.get_login_as_student, name='login_student'),
    path('login_teacher/', views.get_login_as_teacher, name='login_teacher'),
    path('logout/', views.logout, name = 'logout'),
]
