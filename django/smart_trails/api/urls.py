from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('sensors/data/', views.receive_sensor_data, name='receive_sensor_data'),
    path('stations/<str:station_id>/data/', views.get_station_data, name='get_station_data'),
]