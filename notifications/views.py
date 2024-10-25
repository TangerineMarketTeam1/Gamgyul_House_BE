from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from uuid import UUID
from notifications.models import Notification
from notifications.serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    알림 목록 조회
    단일 알림 삭제
    모든 알림 삭제
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @extend_schema(
        summary="사용자의 알림 목록 조회",
        description="로그인한 사용자가 받은 모든 알림 목록을 조회합니다.",
        responses={200: NotificationSerializer(many=True)},
        tags=["notifications"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="id", type=UUID, location="path", description="알림 ID"
            )
        ],
        summary="특정 알림 삭제",
        description="특정 ID를 가진 알림을 삭제합니다.",
        responses={
            204: OpenApiResponse(
                description="알림이 성공적으로 삭제되었습니다.",
                examples=[{"message": "알림이 삭제되었습니다."}],
            ),
            404: OpenApiResponse(
                description="알림을 찾을 수 없습니다.",
                examples=[{"detail": "알림을 찾을 수 없습니다."}],
            ),
        },
    )
    def destroy(self, request, *args, **kwargs):
        """
        특정 알림을 삭제
        """
        notification = get_object_or_404(
            Notification,
            id=self.kwargs["id"],
            recipient=request.user,
        )
        notification.delete()
        return Response(
            {"message": "알림이 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=["delete"])
    @extend_schema(
        summary="모든 알림 삭제",
        description="로그인한 사용자의 모든 알림을 삭제합니다.",
        responses={
            204: OpenApiResponse(description="모든 알림이 성공적으로 삭제되었습니다."),
        },
        tags=["notifications"],
    )
    def delete_all(self, request, *args, **kwargs):
        """
        현재 사용자의 모든 알림을 삭제하는 액션
        """
        deleted_count, _ = Notification.objects.filter(recipient=request.user).delete()
        return Response(
            {"message": f"{deleted_count}개의 알림이 삭제되었습니다."},
            status=status.HTTP_204_NO_CONTENT,
        )
