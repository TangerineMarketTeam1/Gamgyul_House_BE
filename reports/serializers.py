import uuid
from django.contrib.contenttypes.models import ContentType
from django.db import models

from rest_framework import serializers

from .models import Report


class ReportCreateSerializer(serializers.ModelSerializer):
    """신고 생성을 위한 시리얼라이저.

    이 시리얼라이저는 신고 생성에 필요한 데이터의 유효성을 검사하고,
    신고 객체를 생성합니다.

    Attributes:
        content_type (CharField): 신고 대상 콘텐츠의 타입.
        object_id (CharField): 신고 대상 객체의 ID.
    """

    content_type = serializers.CharField()
    object_id = serializers.CharField()

    class Meta:
        model = Report
        fields = ["content_type", "object_id", "reason", "description"]

    def validate(self, attrs):
        """입력된 데이터의 유효성을 검사합니다.

        이 메서드는 content_type, object_id, reason의 유효성을 검사하고,
        신고 대상 객체의 존재 여부를 확인합니다.

        Args:
            attrs (dict): 유효성을 검사할 속성들의 딕셔너리.

        Returns:
            dict: 유효성이 검증된 속성들의 딕셔너리.

        Raises:
            serializers.ValidationError: 유효성 검사에 실패한 경우 발생합니다.
        """
        content_type_str = attrs.get("content_type")
        object_id = attrs.get("object_id")
        reason = attrs.get("reason")

        if not content_type_str or not object_id or not reason:
            raise serializers.ValidationError("모든 필드를 입력해야 합니다.")

        try:
            app_label, model = content_type_str.split(".")
            content_type_obj = ContentType.objects.get(app_label=app_label, model=model)
            model_class = content_type_obj.model_class()

            if isinstance(model_class._meta.pk, models.UUIDField):
                object_id = uuid.UUID(object_id)

            reported_content = model_class.objects.get(pk=object_id)

        except ValueError:
            raise serializers.ValidationError(
                "유효하지 않은 object_id 형식이거나 content_type 형식이 올바르지 않습니다."
            )
        except ContentType.DoesNotExist:
            raise serializers.ValidationError("유효하지 않은 콘텐츠 유형입니다.")
        except model_class.DoesNotExist:
            raise serializers.ValidationError("신고하려는 객체가 존재하지 않습니다.")

        attrs["content_type"] = content_type_obj
        attrs["object_id"] = str(object_id)

        return attrs

    def create(self, validated_data):
        """검증된 데이터로 새로운 Report 객체를 생성합니다.

        이 메서드는 현재 요청을 보낸 사용자를 신고자로 설정하고,
        새로운 Report 객체를 생성합니다.

        Args:
            validated_data (dict): 유효성이 검증된 데이터의 딕셔너리.

        Returns:
            Report: 새로 생성된 Report 객체.
        """
        reporter = self.context["request"].user

        validated_data["reporter"] = reporter

        return Report.objects.create(**validated_data)
