from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample
from .models import Report
from .serializers import ReportCreateSerializer


class ReportCreateView(generics.CreateAPIView):
    """신고 생성 뷰"""

    queryset = Report.objects.all()
    serializer_class = ReportCreateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="신고 생성",
        description="JWT로 인증된 사용자가 콘텐츠(게시글, 댓글 등)에 대한 신고를 생성합니다.",
        request=ReportCreateSerializer,
        responses={
            201: ReportCreateSerializer,
            401: {"description": "인증되지 않은 사용자"},
            400: {"description": "잘못된 요청 데이터"},
        },
        examples=[
            OpenApiExample(
                "신고 생성 예시",
                summary="게시글 신고 예시",
                description="스팸으로 의심되는 게시글 신고",
                value={
                    "content_type": "insta.post",
                    "object_id": 1,
                    "reason": "spam",
                    "description": "이 게시글은 광고성 스팸으로 의심됩니다.",
                },
                request_only=True,
            ),
        ],
        tags=["reports"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
