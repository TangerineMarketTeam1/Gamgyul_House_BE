from django.conf import settings
from django.urls import reverse
from django.core.files.storage import default_storage
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from .models import Product, ProductImage
from .serializers import ProductListSerializer, ProductSerializer
from config.pagination import PageNumberPagination
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from urllib.parse import urlparse


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.order_by("-created_at")
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name", "user__username", "variety", "growing_region"]
    pagination_class = PageNumberPagination
    lookup_field = "id"

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get("search", None)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(user__username__icontains=search_query)
                | Q(variety__icontains=search_query)
                | Q(growing_region__icontains=search_query)
            )
        return queryset.prefetch_related("images")

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductSerializer

    @extend_schema(
        summary="상품 목록 조회",
        description="모든 상품의 목록을 반환합니다. 검색 기능을 사용하여 특정 상품을 찾을 수 있습니다.",
        parameters=[
            OpenApiParameter(
                name="search",
                type=str,
                description="상품 이름, 작성자, 품종, 재배 지역으로 검색 (선택사항)",
                required=False,
            ),
        ],
        responses={200: ProductListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="상품 등록",
        description="새로운 상품을 등록합니다.",
        request=ProductSerializer,
        responses={201: ProductSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save(user=request.user)
            images = request.FILES.getlist("images")

            if len(images) > 5:
                return Response(
                    {"error": "최대 5장까지만 이미지를 업로드할 수 있습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for image in images:
                ProductImage.objects.create(product=product, image=image)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="상품 상세 정보 조회",
        description="특정 상품의 상세 정보를 반환합니다.",
        responses={200: ProductSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="상품 정보 수정",
        description="특정 상품의 정보를 수정합니다.",
        request=ProductSerializer,
        responses={200: ProductSerializer},
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):
        product = serializer.save()
        images_to_delete = self.request.data.getlist("images_to_delete", [])

        for full_image_url in images_to_delete:
            try:
                parsed_url = urlparse(full_image_url)
                relative_path = parsed_url.path
                if relative_path.startswith(settings.MEDIA_URL):
                    relative_path = relative_path[len(settings.MEDIA_URL) :]

                image = ProductImage.objects.get(image=relative_path, product=product)

                if default_storage.exists(relative_path):
                    default_storage.delete(relative_path)
                else:
                    print(f"File not found in storage: {relative_path}")

                image.delete()
            except ProductImage.DoesNotExist:
                print(f"Image record not found for path: {relative_path}")
            except Exception as e:
                print(f"Error deleting image with URL {full_image_url}: {str(e)}")

        new_images = self.request.FILES.getlist("image")
        for image in new_images:
            ProductImage.objects.create(product=product, image=image)

        return product

    @extend_schema(
        summary="상품 삭제",
        description="특정 상품을 삭제합니다.",
        responses={204: "삭제가 완료되었습니다"},
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
