from django.urls import path
from . import views

app_name = 'core_settings'

urlpatterns = [
    path('api/contact/', views.submit_contact_form, name='submit_contact_form'),
]
