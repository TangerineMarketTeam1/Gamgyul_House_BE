from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample
from .models import Report
from .serializers import ReportCreateSerializer


class ReportCreateView(generics.CreateAPIView):
    """신고 생성 뷰.

    이 뷰는 인증된 사용자가 콘텐츠(게시글, 댓글 등)에 대한 신고를 생성할 수 있게 합니다.

    Attributes:
        queryset: 모든 Report 객체를 포함하는 쿼리셋.
        serializer_class: 신고 생성에 사용되는 시리얼라이저.
        permission_classes: 뷰에 접근하기 위해 필요한 권한.
    """

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
        """신고를 생성합니다.

        이 메서드는 사용자로부터 받은 데이터를 검증하고, 유효한 경우 새로운 신고를 생성합니다.

        Args:
            request: HTTP 요청 객체.
            *args: 추가 인자.
            **kwargs: 추가 키워드 인자.

        Returns:
            Response: 생성된 신고 정보를 포함한 HTTP 응답.
                성공 시 201 Created, 실패 시 400 Bad Request를 반환합니다.
        """
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
        """신고 생성을 수행합니다.

        이 메서드는 신고를 데이터베이스에 저장하기 전에 현재 인증된 사용자를 신고자로 설정합니다.

        Args:
            serializer: 유효성이 검증된 시리얼라이저 인스턴스.
        """
        serializer.save(reporter=self.request.user)
