from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import DeviceToken
from .apns_service import apns_service


@api_view(['POST'])
def register_device(request):
    token = request.data.get('token')
    platform = request.data.get('platform')
    bundle_id = request.data.get('bundle_id')

    station_id = request.data.get('station_id')
    

    if not token or not platform or not bundle_id:
        return Response(
            {'error': 'token, platform, and bundle_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    device, created = DeviceToken.objects.update_or_create(
        token=token,
        defaults={
            'platform': platform,
            'bundle_id': bundle_id,
            'station_id': station_id,
            'is_active': True,
        }
    )
    
    return Response({
        'status': 'success',
        'message': 'Device registered' if created else 'Device updated',
        'device_id': device.id
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)




@api_view(['POST'])
def unregister_device(request):

    token = request.data.get('token')
    
    if not token:
        return Response(
            {'error': 'token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        device = DeviceToken.objects.get(token=token)
        device.is_active = False
        device.save()
        return Response({'status': 'success', 'message': 'Device unregistered'})
    except DeviceToken.DoesNotExist:
        return Response(
            {'error': 'Device not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def test_notification(request):
    token = request.data.get('token')
    
    if not token:
        return Response(
            {'error': 'token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        device = DeviceToken.objects.get(token=token, is_active=True)
        
        success = apns_service.send_sync(
            device_token=device.token,
            bundle_id=device.bundle_id,
            title="Smart Trails Test",
            body="Push notifications are working! 🏔️ yeah! ",
            data={'test': True}
        )
        
        if success:
            return Response({'status': 'success', 'message': 'Notification sent'})
        else:
            return Response(
                {'error': 'Failed to send notification'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    except DeviceToken.DoesNotExist:
        return Response(
            {'error': 'Device not found or inactive'},
            status=status.HTTP_404_NOT_FOUND
        )
