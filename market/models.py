import uuid
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFit
from django.db import models
from django.db.models import Avg
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()


class Product(models.Model):
    """
    상품 모델
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    stock = models.IntegerField()
    variety = models.CharField(max_length=255, blank=True, null=True)
    growing_region = models.CharField(max_length=255, blank=True, null=True)
    harvest_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def average_rating(self):
        return self.reviews.aggregate(Avg("rating"))["rating__avg"]


def upload_to(instance, filename):
    """
    이미지를 UUID로 데이터베이스에 저장하는 함수
    """
    ext = filename.split(".")[-1]
    now = datetime.now()
    return f"products/{now.year}/{now.month:02d}/{now.day:02d}/{uuid.uuid4()}.{ext}"


class ProductImage(models.Model):
    """
    상품에 들어갈 이미지 모델
    """

    product = models.ForeignKey(
        "Product", related_name="images", on_delete=models.CASCADE
    )
    image = ProcessedImageField(
        upload_to=upload_to,
        processors=[ResizeToFit(1920, 1080)],
        format="JPEG",
        options={"quality": 100},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"
