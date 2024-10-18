from django.urls import path
from . import views

urlpatterns = [
    # 프로필 검색
    path("search-profile/", views.ProfileSearchView.as_view(), name="profile_search"),
]
