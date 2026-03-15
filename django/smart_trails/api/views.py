from django.shortcuts import render

# Create your views here.

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from stations.models import Station
from sensors.models import (
    AtmosphericReading,
    LightReading,
    SoilReading,
    AirQualityReading,
    PrecipitationReading,
    TrailActivityReading
)
from notifications.alert_system import alert_analyzer


@api_view(['POST'])
def receive_sensor_data(request):
    """
    POST /api/v1/sensors/data
    
    Arduino posts complete sensor snapshot here.
    
    Expected JSON format:
    {
        "station_id": "mombarone-san-carlo",
        "timestamp": "2024-11-22T14:30:00Z",
        "location": {
            "latitude": 45.5615,
            "longitude": 8.0573,
            "altitude": 1250,
            "trail_name": "Sentiero Graglia"
        },
        "sensors": {
            "atmospheric": {
                "temperature": 12.5,
                "humidity": 65.0,
                "pressure": 875.3
            },
            "light": {
                "uv_index": 3.2,
                "lux": 45000
            },
            "soil": {
                "moisture_percent": 45.5
            },
            "air_quality": {
                "co2_ppm": 420
            },
            "precipitation": {
                "is_raining": false,
                "rain_detected_last_hour": true
            },
            "trail_activity": {
                "motion_count": 12,
                "period_minutes": 60
            }
        }
    }
    """
    data = request.data
    
    try:
        if 'station_id' not in data:
            return Response({
                'status': 'error',
                'message': 'station_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if 'timestamp' not in data:
            return Response({
                'status': 'error',
                'message': 'timestamp is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        station, created = Station.objects.get_or_create(
            station_id=data['station_id'],
            defaults={
                'name': data.get('name', data['station_id']),
                'latitude': data.get('location', {}).get('latitude', 0),
                'longitude': data.get('location', {}).get('longitude', 0),
                'altitude': data.get('location', {}).get('altitude', 0),
                'trail_name': data.get('location', {}).get('trail_name', ''),
            }
        )
        
        # Use server time instead of Arduino's timestamp (Arduino doesn't have RTC)
        timestamp = timezone.now()
        
        sensors = data.get('sensors', {})
        
        # Create all sensor readings in a transaction
        # If any INSERT fails, all are rolled back
        with transaction.atomic():
            if 'atmospheric' in sensors:
                atm = sensors['atmospheric']
                AtmosphericReading.objects.update_or_create(
                    station=station,
                    timestamp=timestamp,
                    defaults={
                        'temperature': atm.get('temperature'),
                        'humidity': atm.get('humidity'),
                        'pressure': atm.get('pressure')
                    }
                )
            
            if 'light' in sensors:
                light = sensors['light']
                LightReading.objects.update_or_create(
                    station=station,
                    timestamp=timestamp,
                    defaults={
                        'uv_index': light.get('uv_index'),
                        'lux': light.get('lux')
                    }
                )
            
            if 'soil' in sensors:
                soil = sensors['soil']
                SoilReading.objects.update_or_create(
                    station=station,
                    timestamp=timestamp,
                    defaults={
                        'moisture_percent': soil.get('moisture_percent')
                    }
                )
            
            if 'air_quality' in sensors:
                air = sensors['air_quality']
                AirQualityReading.objects.update_or_create(
                    station=station,
                    timestamp=timestamp,
                    defaults={
                        'co2_ppm': air.get('co2_ppm')
                    }
                )
            
            if 'precipitation' in sensors:
                precip = sensors['precipitation']
                PrecipitationReading.objects.update_or_create(
                    station=station,
                    timestamp=timestamp,
                    defaults={
                        'is_raining': precip.get('is_raining'),
                        'rain_detected_last_hour': precip.get('rain_detected_last_hour')
                    }
                )
            
            if 'trail_activity' in sensors:
                activity = sensors['trail_activity']
                TrailActivityReading.objects.update_or_create(
                    station=station,
                    timestamp=timestamp,
                    defaults={
                        'motion_count': activity.get('motion_count'),
                        'period_minutes': activity.get('period_minutes')
                    }
                )
        
        return Response({
            'status': 'success',
            'station_id': station.station_id,
            'timestamp': timestamp.isoformat(),
            'message': 'Data received and stored successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def health_check(request):
    return Response({
        'status': 'healthy',
        'message': 'SmartTrails API is running'
    })


@api_view(['GET'])
def get_station_data(request, station_id):
    """
    GET /api/v1/stations/<station_id>/data

    Returns latest sensor readings with danger flags from AlertAnalyzer.
    """
    try:
        station = Station.objects.get(station_id=station_id)
    except Station.DoesNotExist:
        return Response({
            'status': 'error',
            'message': f'Station {station_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    atmospheric = station.atmospheric_readings.first()
    light = station.light_readings.first()
    soil = station.soil_readings.first()
    air_quality = station.air_quality_readings.first()
    precipitation = station.precipitation_readings.first()
    trail_activity = station.trail_activity_readings.first()

    # Extract raw values
    temp = float(atmospheric.temperature) if atmospheric and atmospheric.temperature else None
    humidity = float(atmospheric.humidity) if atmospheric and atmospheric.humidity else None
    pressure = float(atmospheric.pressure) if atmospheric and atmospheric.pressure else None
    uv = float(light.uv_index) if light and light.uv_index else None
    lux = light.lux if light and light.lux else None
    moisture = float(soil.moisture_percent) if soil and soil.moisture_percent else None
    co2 = air_quality.co2_ppm if air_quality and air_quality.co2_ppm else None
    is_raining = precipitation.is_raining if precipitation else False
    rain_recent = precipitation.rain_detected_last_hour if precipitation else False
    motion = trail_activity.motion_count if trail_activity and trail_activity.motion_count else 0
    period = trail_activity.period_minutes if trail_activity and trail_activity.period_minutes else 60

    # Build sensor data dict for AlertAnalyzer
    sensor_data = {
        'atmospheric': {
            'temperature': temp,
            'humidity': humidity,
            'pressure': pressure,
        },
        'light': {
            'uv_index': uv,
            'lux': lux,
        },
        'soil': {
            'moisture_percent': moisture,
        },
        'air_quality': {
            'co2_ppm': co2,
        },
        'precipitation': {
            'is_raining': is_raining,
            'rain_detected_last_hour': rain_recent,
        },
        'trail_activity': {
            'motion_count': motion,
        },
    }

    # Get danger flags from AlertAnalyzer
    flags = alert_analyzer.get_is_dangerous_flags(sensor_data)

    response_data = {
        'station_id': station.station_id,
        'timestamp': timezone.now().isoformat(),
        'location': {
            'latitude': float(station.latitude),
            'longitude': float(station.longitude),
            'altitude': station.altitude,
            'trail_name': station.trail_name or station.name
        },
        'sensors': {
            'atmospheric': {
                'temperature': temp if temp is not None else 0.0,
                'temperature_is_dangerous': flags['temperature_is_dangerous'],
                'humidity': humidity if humidity is not None else 0.0,
                'humidity_is_dangerous': flags['humidity_is_dangerous'],
                'pressure': pressure if pressure is not None else 0.0,
                'pressure_is_dangerous': flags['pressure_is_dangerous'],
            },
            'light': {
                'uv_index': uv if uv is not None else 0.0,
                'uv_index_is_dangerous': flags['uv_index_is_dangerous'],
                'lux': lux if lux is not None else 0,
                'lux_is_dangerous': flags['lux_is_dangerous'],
            },
            'soil': {
                'moisture_percent': moisture if moisture is not None else 0.0,
                'moisture_percent_is_dangerous': flags['moisture_percent_is_dangerous'],
            },
            'air_quality': {
                'co2_ppm': co2 if co2 is not None else 0,
                'co2_ppm_is_dangerous': flags['co2_ppm_is_dangerous'],
            },
            'precipitation': {
                'is_raining': is_raining,
                'is_raining_is_dangerous': flags['is_raining_is_dangerous'],
                'rain_detected_last_hour': rain_recent,
                'rain_detected_last_hour_is_dangerous': flags['rain_detected_last_hour_is_dangerous'],
            },
            'trail_activity': {
                'motion_count': motion,
                'motion_count_is_dangerous': flags['motion_count_is_dangerous'],
                'period_minutes': period,
            },
        },
    }

    return Response(response_data)


def index(request):
    return render(request, 'index.html')


from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def sensor_dashboard(request):
    return render(request, 'admin/dashboard.html')
