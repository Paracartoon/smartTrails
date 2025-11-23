from django.db import models

# Create your models here.


class Station(models.Model):
    """
    Represents a physical Arduino monitoring station in the mountains.
    Stores static metadata about the station location and configuration.
    """
    station_id = models.CharField(
        max_length=50, 
        primary_key=True,
        help_text="Unique identifier for the station (e.g., 'mombarone-san-carlo')"
    )
    name = models.CharField(
        max_length=200,
        help_text="Human-readable name (e.g., 'Mombarone San Carlo')"
    )
    
    # Location data
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6,
        help_text="GPS latitude coordinate"
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6,
        help_text="GPS longitude coordinate"
    )
    altitude = models.IntegerField(
        help_text="Altitude in meters above sea level"
    )
    trail_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name of the trail this station is on"
    )
    
    # Station metadata
    installation_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when station was installed"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this station is currently operational"
    )
    
    # Sensor configuration (which sensors are installed)
    has_atmospheric = models.BooleanField(
        default=True,
        help_text="Has temperature/humidity/pressure sensor"
    )
    has_precipitation = models.BooleanField(
        default=True,
        help_text="Has rain detection sensor"
    )
    has_light = models.BooleanField(
        default=True,
        help_text="Has UV/lux sensors"
    )
    has_air_quality = models.BooleanField(
        default=True,
        help_text="Has CO2 sensor"
    )
    has_soil = models.BooleanField(
        default=True,
        help_text="Has soil moisture sensor"
    )
    has_trail_activity = models.BooleanField(
        default=True,
        help_text="Has PIR motion sensor for trail traffic"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stations'
        ordering = ['station_id']
        verbose_name = 'Station'
        verbose_name_plural = 'Stations'
    
    def __str__(self):
        return f"{self.name} ({self.station_id})"
