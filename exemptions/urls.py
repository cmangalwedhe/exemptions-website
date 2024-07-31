from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='exemptions'),
    path('teachers/', views.teacher, name='teachers'),
    path('teachers-student/', views.teacher_list, name='teacher_list'),
    path('administrators/', views.administration, name='administration'),
    path('admin-login/', views.admin_login, name='admin_login')
]