# api/serializers.py

from rest_framework import serializers
from stations.models import Station
from sensors.models import (
    AtmosphericReading,
    LightReading,
    SoilReading,
    AirQualityReading,
    PrecipitationReading,
    TrailActivityReading
)


class StationSerializer(serializers.ModelSerializer):
    """Serializer for Station model"""
    
    class Meta:
        model = Station
        fields = [
            'station_id',
            'name',
            'latitude',
            'longitude',
            'altitude',
            'trail_name',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AtmosphericReadingSerializer(serializers.ModelSerializer):
    """Serializer for atmospheric readings"""
    
    class Meta:
        model = AtmosphericReading
        fields = ['station', 'timestamp', 'temperature', 'humidity', 'pressure']


class LightReadingSerializer(serializers.ModelSerializer):
    """Serializer for light/UV readings"""
    
    class Meta:
        model = LightReading
        fields = ['station', 'timestamp', 'uv_index', 'lux']


class SoilReadingSerializer(serializers.ModelSerializer):
    """Serializer for soil moisture readings"""
    
    class Meta:
        model = SoilReading
        fields = ['station', 'timestamp', 'moisture_percent']


class AirQualityReadingSerializer(serializers.ModelSerializer):
    """Serializer for air quality readings"""
    
    class Meta:
        model = AirQualityReading
        fields = ['station', 'timestamp', 'co2_ppm']


class PrecipitationReadingSerializer(serializers.ModelSerializer):
    """Serializer for precipitation readings"""
    
    class Meta:
        model = PrecipitationReading
        fields = ['station', 'timestamp', 'is_raining', 'rain_detected_last_hour']


class TrailActivityReadingSerializer(serializers.ModelSerializer):
    """Serializer for trail activity readings"""
    
    class Meta:
        model = TrailActivityReading
        fields = ['station', 'timestamp', 'motion_count', 'period_minutes']