from django.contrib import admin

# Register your models here.

from .models import (
    AtmosphericReading,
    LightReading,
    SoilReading,
    AirQualityReading,
    PrecipitationReading,
    TrailActivityReading
)


@admin.register(AtmosphericReading)
class AtmosphericReadingAdmin(admin.ModelAdmin):
    list_display = ['station', 'timestamp', 'temperature', 'humidity', 'pressure']
    list_filter = ['station', 'timestamp']
    search_fields = ['station__station_id', 'station__name']
    ordering = ['-timestamp']


@admin.register(LightReading)
class LightReadingAdmin(admin.ModelAdmin):
    list_display = ['station', 'timestamp', 'uv_index', 'lux']
    list_filter = ['station', 'timestamp']
    search_fields = ['station__station_id', 'station__name']
    ordering = ['-timestamp']


@admin.register(SoilReading)
class SoilReadingAdmin(admin.ModelAdmin):
    list_display = ['station', 'timestamp', 'moisture_percent']
    list_filter = ['station', 'timestamp']
    search_fields = ['station__station_id', 'station__name']
    ordering = ['-timestamp']


@admin.register(AirQualityReading)
class AirQualityReadingAdmin(admin.ModelAdmin):
    list_display = ['station', 'timestamp', 'co2_ppm']
    list_filter = ['station', 'timestamp']
    search_fields = ['station__station_id', 'station__name']
    ordering = ['-timestamp']


@admin.register(PrecipitationReading)
class PrecipitationReadingAdmin(admin.ModelAdmin):
    list_display = ['station', 'timestamp', 'is_raining', 'rain_detected_last_hour']
    list_filter = ['station', 'timestamp', 'is_raining']
    search_fields = ['station__station_id', 'station__name']
    ordering = ['-timestamp']


@admin.register(TrailActivityReading)
class TrailActivityReadingAdmin(admin.ModelAdmin):
    list_display = ['station', 'timestamp', 'motion_count', 'period_minutes']
    list_filter = ['station', 'timestamp']
    search_fields = ['station__station_id', 'station__name']
    ordering = ['-timestamp']
