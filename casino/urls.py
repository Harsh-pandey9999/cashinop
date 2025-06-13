from django.urls import path
from . import views

urlpatterns = [
    path('admin/logs/', views.admin_logs, name='admin_logs'),
    path('admin/logs/clear/', views.clear_logs, name='clear_logs'),
] 