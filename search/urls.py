from django.urls import path
from . import views

urlpatterns = [
    path("search-profile/", views.ProfileSearchView.as_view(), name="profile_search"),
    path("search-post/", views.PostSearchView.as_view(), name="post_search"),
    path("search-product/", views.ProductSearchView.as_view(), name="product_search"),
    path(
        "chatrooms/<uuid:room_id>/messages/",
        views.MessageSearchView.as_view(),
        name="message_search",
    ),
]
