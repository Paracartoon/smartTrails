from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Arduino POST endpoint
    path('sensors/data/', views.receive_sensor_data, name='receive_sensor_data'),
]