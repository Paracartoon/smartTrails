from django.db import models
from stations.models import Station


class DeviceToken(models.Model):
    PLATFORM_CHOICES = [
        ('ios', 'iOS'),
        ('watchos', 'watchOS'),
    ]
    
    token = models.CharField(max_length=200, unique=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    bundle_id = models.CharField(max_length=200)
    station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, blank=True, 
                                help_text="Station this device is subscribed to")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'device_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['station', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.platform} - {self.token[:20]}..."
