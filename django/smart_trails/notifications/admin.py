from django.contrib import admin
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import path
from django.utils.html import format_html
from .models import DeviceToken
from .apns_service import apns_service
from .alert_system import Alert
import random


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['platform', 'bundle_id', 'station', 'is_active', 'created_at', 'send_alert_button']
    list_filter = ['platform', 'is_active', 'created_at']
    search_fields = ['token', 'bundle_id']
    readonly_fields = ['token', 'created_at', 'updated_at']
    
    def send_alert_button(self, obj):
        """Add a button to send test alert to this device"""
        if obj.is_active:
            return format_html(
                '<a class="button" href="{}">Send Test Alert</a>',
                f'/admin/notifications/devicetoken/{obj.pk}/send-alert/'
            )
        return '-'
    send_alert_button.short_description = 'Actions'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:device_id>/send-alert/',
                self.admin_site.admin_view(self.send_test_alert),
                name='send-test-alert',
            ),
        ]
        return custom_urls + urls
    
    def send_test_alert(self, request, device_id):
        # RANDOM!
        try:
            device = DeviceToken.objects.get(pk=device_id, is_active=True)
        except DeviceToken.DoesNotExist:
            self.message_user(request, 'Device not found or inactive', level='error')
            return HttpResponseRedirect('../..')
        
        alert = self._generate_random_alert()
        success = apns_service.send_sync(
            device_token=device.token,
            bundle_id=device.bundle_id,
            title=alert.title,
            body=alert.body,
            data={
                'severity': alert.severity,
                'category': alert.category,
                'test': True
            },
            image_url='https://smart-trails.com/static/st_background.jpg',
            category='TRAIL_ALERT'
        )
        

        if success:
            self.message_user(
                request, 
                f'Successfully sent test alert: {alert.title}',
                level='success'
            )
        else:
            self.message_user(request, 'Failed to send notification', level='error')
        
        return HttpResponseRedirect('../..')
    
    def _generate_random_alert(self) -> Alert:
        alerts = [
            # Temp
            Alert(
                severity='danger',
                title='🥶 EXTREME COLD WARNING',
                body='Mombarone: -18°C. Frostbite possible in minutes. Exposed skin at risk.',
                emoji='🥶',
                category='temperature'
            ),
            Alert(
                severity='warning',
                title='❄️ Freezing Conditions',
                body='San Carlo: -3°C. Ice likely on trail. Use traction devices if available.',
                emoji='❄️',
                category='temperature'
            ),
            Alert(
                severity='danger',
                title='🔥 Extreme Heat Warning',
                body='Valle Oropa: 37°C. Heat exhaustion risk. Carry extra water, take frequent breaks.',
                emoji='🔥',
                category='temperature'
            ),
            
            # Weather
            Alert(
                severity='danger',
                title='🥶 Hypothermia Risk',
                body='Mombarone: Cold (2°C) + wet conditions. Hypothermia can occur quickly. Stay dry or turn back.',
                emoji='🥶',
                category='weather'
            ),
            Alert(
                severity='danger',
                title='⛈️ Severe Weather Warning',
                body='San Carlo: Pressure at 915 hPa. Severe weather likely. Descend or seek shelter.',
                emoji='⛈️',
                category='weather'
            ),
            Alert(
                severity='warning',
                title='🌧️ Storm Watch',
                body='Valle Oropa: Low pressure (945 hPa). Weather may deteriorate. Monitor conditions.',
                emoji='🌧️',
                category='weather'
            ),
            Alert(
                severity='warning',
                title='🌧️ Active Rainfall',
                body='Mombarone: Rain detected. Trail may be slippery. Watch footing on rocks and roots.',
                emoji='🌧️',
                category='weather'
            ),
            
            # UV alerts
            Alert(
                severity='danger',
                title='☀️ EXTREME UV',
                body='San Carlo: UV 12. Sunburn in 10-15 minutes. Wear protection, limit exposure.',
                emoji='☀️',
                category='weather'
            ),
            Alert(
                severity='warning',
                title='☀️ Very High UV',
                body='Valle Oropa: UV 9. Apply sunscreen (SPF 30+). Wear hat and sunglasses.',
                emoji='☀️',
                category='weather'
            ),
            
            # Visibility 
            Alert(
                severity='warning',
                title='🌫️ Poor Visibility',
                body='Mombarone: Low light + fog/rain. Visibility reduced. Use headlamp and stay on marked trail.',
                emoji='🌫️',
                category='weather'
            ),
            Alert(
                severity='info',
                title='🌙 Low Light',
                body='San Carlo: Limited daylight. Headlamp recommended.',
                emoji='🌙',
                category='weather'
            ),
            
            # Air quality 
            Alert(
                severity='danger',
                title='💨 DANGEROUS AIR QUALITY',
                body='Refuge: CO2 5200 ppm. Exit immediately if breathing difficulty or dizziness.',
                emoji='💨',
                category='air_quality'
            ),
            Alert(
                severity='warning',
                title='💨 Poor Air Quality',
                body='Refuge: CO2 2100 ppm. Headache or drowsiness possible. Improve ventilation.',
                emoji='💨',
                category='air_quality'
            ),
            
            # Trail 
            Alert(
                severity='info',
                title='👥 High Trail Traffic',
                body='Valle Oropa: 35 hikers detected in last hour. Expect crowds and delays.',
                emoji='👥',
                category='trail'
            ),
            Alert(
                severity='warning',
                title='⚠️ Slippery Trail',
                body='Mombarone: Recent rain + cold temps. Ice or mud likely. Use caution.',
                emoji='⚠️',
                category='trail'
            ),
        ]
        
        return random.choice(alerts)

    actions = ['send_alert_to_selected']
    
    def send_alert_to_selected(self, request, queryset):
        active_devices = queryset.filter(is_active=True)
        
        if not active_devices.exists():
            self.message_user(request, 'No active devices selected', level='warning')
            return
        
        alert = self._generate_random_alert()
        
        sent_count = 0
        failed_count = 0
        
        for device in active_devices:
            success = apns_service.send_sync(
                device_token=device.token,
                bundle_id=device.bundle_id,
                title=alert.title,
                body=alert.body,
                data={
                    'severity': alert.severity,
                    'category': alert.category,
                    'test': True
                },
                image_url='https://smart-trails.com/static/st_background.jpg',
                category='TRAIL_ALERT'
            )
            
            if success:
                sent_count += 1
            else:
                failed_count += 1
        
        self.message_user(
            request,
            f'Sent to {sent_count} devices. Failed: {failed_count}. Alert: {alert.title}',
            level='success' if failed_count == 0 else 'warning'
        )
    
    send_alert_to_selected.short_description = 'Send random test alert to selected devices'
