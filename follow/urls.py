from django.urls import path
from . import views

urlpatterns = [
    path("follow/<uuid:pk>/", views.FollowView.as_view(), name="follow"),
    path("unfollow/<uuid:pk>/", views.UnfollowView.as_view(), name="unfollow"),
    path("followers/", views.FollowerListView.as_view(), name="follower-list"),
    path("following/", views.FollowingListView.as_view(), name="following-list"),
]
