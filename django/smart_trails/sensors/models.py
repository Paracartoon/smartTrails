from django.db import models

# Create your models here.

class AtmosphericReading(models.Model):
    """
    Temperature, humidity, and pressure readings.
    Separate table for efficient temperature-only queries.
    """
    station = models.ForeignKey(
        'stations.Station',
        related_name='atmospheric_readings',
        on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(
        db_index=True,
        help_text="When this reading was taken"
    )
    
    # Sensor values
    temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Temperature in Celsius"
    )
    humidity = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Relative humidity percentage (0-100)"
    )
    pressure = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Atmospheric pressure in hPa"
    )
    
    class Meta:
        db_table = 'atmospheric_readings'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['station', '-timestamp']),
        ]
        unique_together = [['station', 'timestamp']]
        verbose_name = 'Atmospheric Reading'
        verbose_name_plural = 'Atmospheric Readings'
    
    def __str__(self):
        return f"{self.station.station_id} - {self.timestamp} - {self.temperature}°C"


class LightReading(models.Model):
    """
    UV index and luminosity readings.
    """
    station = models.ForeignKey(
        'stations.Station',
        related_name='light_readings',
        on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(
        db_index=True,
        help_text="When this reading was taken"
    )
    
    # Sensor values
    uv_index = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="UV index (0-15+)"
    )
    lux = models.IntegerField(
        null=True,
        blank=True,
        help_text="Light intensity in lux"
    )
    
    class Meta:
        db_table = 'light_readings'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['station', '-timestamp']),
        ]
        unique_together = [['station', 'timestamp']]
        verbose_name = 'Light Reading'
        verbose_name_plural = 'Light Readings'
    
    def __str__(self):
        return f"{self.station.station_id} - {self.timestamp} - UV:{self.uv_index}"


class SoilReading(models.Model):
    """
    Soil moisture readings.
    """
    station = models.ForeignKey(
        'stations.Station',
        related_name='soil_readings',
        on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(
        db_index=True,
        help_text="When this reading was taken"
    )
    
    # Sensor values
    moisture_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Soil moisture percentage (0-100)"
    )
    
    class Meta:
        db_table = 'soil_readings'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['station', '-timestamp']),
        ]
        unique_together = [['station', 'timestamp']]
        verbose_name = 'Soil Reading'
        verbose_name_plural = 'Soil Readings'
    
    def __str__(self):
        return f"{self.station.station_id} - {self.timestamp} - {self.moisture_percent}%"


class AirQualityReading(models.Model):
    """
    CO2 and air quality readings.
    """
    station = models.ForeignKey(
        'stations.Station',
        related_name='air_quality_readings',
        on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(
        db_index=True,
        help_text="When this reading was taken"
    )
    
    # Sensor values
    co2_ppm = models.IntegerField(
        null=True,
        blank=True,
        help_text="CO2 concentration in parts per million"
    )
    
    class Meta:
        db_table = 'air_quality_readings'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['station', '-timestamp']),
        ]
        unique_together = [['station', 'timestamp']]
        verbose_name = 'Air Quality Reading'
        verbose_name_plural = 'Air Quality Readings'
    
    def __str__(self):
        return f"{self.station.station_id} - {self.timestamp} - {self.co2_ppm}ppm"


class PrecipitationReading(models.Model):
    """
    Rain detection readings.
    """
    station = models.ForeignKey(
        'stations.Station',
        related_name='precipitation_readings',
        on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(
        db_index=True,
        help_text="When this reading was taken"
    )
    
    # Sensor values
    is_raining = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether it's currently raining"
    )
    rain_detected_last_hour = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether rain was detected in the last hour"
    )
    
    class Meta:
        db_table = 'precipitation_readings'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['station', '-timestamp']),
        ]
        unique_together = [['station', 'timestamp']]
        verbose_name = 'Precipitation Reading'
        verbose_name_plural = 'Precipitation Readings'
    
    def __str__(self):
        return f"{self.station.station_id} - {self.timestamp} - Raining:{self.is_raining}"


class TrailActivityReading(models.Model):
    """
    Trail traffic/motion sensor readings (PIR sensor).
    """
    station = models.ForeignKey(
        'stations.Station',
        related_name='trail_activity_readings',
        on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(
        db_index=True,
        help_text="When this reading was taken"
    )
    
    # Sensor values
    motion_count = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of motion detections"
    )
    period_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Time period over which motion was counted"
    )
    
    class Meta:
        db_table = 'trail_activity_readings'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['station', '-timestamp']),
        ]
        unique_together = [['station', 'timestamp']]
        verbose_name = 'Trail Activity Reading'
        verbose_name_plural = 'Trail Activity Readings'
    
    def __str__(self):
        return f"{self.station.station_id} - {self.timestamp} - {self.motion_count} detections"
