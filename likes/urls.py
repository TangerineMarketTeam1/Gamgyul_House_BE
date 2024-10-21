from django.urls import path
from . import views

urlpatterns = [
    path("posts/<uuid:post_id>/like/", views.LikeView.as_view(), name="post_like"),
]
