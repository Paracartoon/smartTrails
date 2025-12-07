from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_device, name='register_device'),
    path('unregister/', views.unregister_device, name='unregister_device'),
    path('test/', views.test_notification, name='test_notification'),
]
