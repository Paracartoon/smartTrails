import asyncio
from aioapns import APNs, NotificationRequest
from django.conf import settings
from threading import Lock


class APNsService:
    """Service for sending push notifications via APNs"""
    
    def __init__(self):
        self.client = None
        self._lock = Lock()
    
    async def get_client(self):
        """Get or create APNs client"""
        if self.client is None:
            # Read key file as bytes
            with open(settings.APNS_KEY_PATH, 'rb') as f:
                key_data = f.read()
            
            self.client = APNs(
                key=key_data,
                key_id=settings.APNS_KEY_ID,
                team_id=settings.APNS_TEAM_ID,
                topic='com.kateDmitrieva.SmartTrails',
                use_sandbox=settings.APNS_USE_SANDBOX,
            )
        return self.client
    
    async def send_notification(self, device_token, bundle_id, title, body, 
                                 data=None, image_url=None, category=None):
        """
        Send push notification to a device
        
        Args:
            device_token: Device APNs token
            bundle_id: App bundle identifier
            title: Notification title
            body: Notification body
            data: Additional data payload
            image_url: URL to image to attach (optional)
            category: Notification category for actions (optional)
        """
        client = await self.get_client()
        
        # Build notification payload
        aps = {
            "alert": {
                "title": title,
                "body": body,
            },
            "sound": "default",
            "badge": 1,
        }
        
        if category:
            aps["category"] = category
        
        message = {"aps": aps}
        
        if data:
            message.update(data)
        
        if image_url:
            message["image_url"] = image_url
        
        request = NotificationRequest(
            device_token=device_token,
            message=message,
        )
        
        try:
            response = await client.send_notification(request)
            return response.is_successful
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False
    
    def send_sync(self, device_token, bundle_id, title, body, data=None, 
                   image_url=None, category=None):
        """Synchronous wrapper for send_notification"""
        with self._lock:
            try:
                # Try to get existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                # No event loop in current thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(
                    self.send_notification(device_token, bundle_id, title, body, 
                                           data, image_url, category)
                )
            except Exception as e:
                print(f"Error in send_sync: {e}")
                return False



apns_service = APNsService()
