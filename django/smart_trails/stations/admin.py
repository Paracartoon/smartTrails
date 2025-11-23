from django.contrib import admin

# Register your models here.

from .models import Station


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ['station_id', 'name', 'altitude', 'trail_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'trail_name']
    search_fields = ['station_id', 'name', 'trail_name']
    readonly_fields = ['created_at', 'updated_at']
