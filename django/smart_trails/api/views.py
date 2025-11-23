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
        
        timestamp = parse_datetime(data['timestamp'])
        if not timestamp:
            return Response({
                'status': 'error',
                'message': 'Invalid timestamp format. Use ISO format: 2024-11-22T14:30:00Z'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if timezone.is_naive(timestamp):
            timestamp = timezone.make_aware(timestamp)
        
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

def index(request):
    return render(request, 'index.html')
