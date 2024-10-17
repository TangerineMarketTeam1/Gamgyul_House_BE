from django.urls import path
from . import views

urlpatterns = [
    path(
        "recommend/",
        views.FriendRecommendationView.as_view(),
        name="friend_recommendation",
    ),
]
