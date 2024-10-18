from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.db import models
from .models import Report
import uuid


class ReportCreateSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField()
    object_id = serializers.CharField()

    class Meta:
        model = Report
        fields = ["content_type", "object_id", "reason", "description"]

    def validate(self, attrs):
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
        reporter = self.context["request"].user

        validated_data["reporter"] = reporter

        return Report.objects.create(**validated_data)
