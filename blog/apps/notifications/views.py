"""
HTTP Polling trade-off:

PROS  — simplicity: no persistent connection, no WebSocket infra needed,
        works behind every proxy/CDN, trivial to implement and cache.
CONS  — latency = poll interval (5-30 s), unnecessary requests when nothing
        changed, server load grows linearly with active users × poll rate.

Polling is acceptable when:
  - Latency of N seconds is fine (notification badges, dashboards).
  - The user base is small or poll interval is long (≥ 30 s).
  - You want zero extra infrastructure.

Switch to WebSockets or SSE when:
  - You need sub-second delivery (chat, live collaboration).
  - You have many concurrent users and want to eliminate empty polls.
  - SSE: server-to-client only (notification feed). 
  - WebSocket: bidirectional (chat, presence).
"""

# Django modules
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import HTTP_200_OK

# Project modules
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_count(request: DRFRequest) -> DRFResponse:
    """GET /api/notifications/count/ — returns unread notification count."""
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()
    return DRFResponse({"unread_count": count}, status=HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request: DRFRequest) -> DRFResponse:
    """GET /api/notifications/ — paginated list of user notifications."""
    notifications = Notification.objects.filter(
        recipient=request.user,
    ).select_related('comment', 'comment__post', 'comment__author')

    page_size = int(request.query_params.get('page_size', 20))
    page      = int(request.query_params.get('page', 1))
    start     = (page - 1) * page_size
    end       = start + page_size

    serializer = NotificationSerializer(notifications[start:end], many=True)
    return DRFResponse({
        "page": page,
        "page_size": page_size,
        "results": serializer.data,
    }, status=HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_read(request: DRFRequest) -> DRFResponse:
    """POST /api/notifications/read/ — marks all unread notifications as read."""
    updated = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).update(is_read=True)
    return DRFResponse({"marked_read": updated}, status=HTTP_200_OK)