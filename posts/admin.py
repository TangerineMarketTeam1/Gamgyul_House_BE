from django.contrib import admin
from .models import Post, PostImage


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("user", "content", "location", "created_at", "updated_at")
    search_fields = ("user__username", "content", "location", "tags__name")
    list_filter = ("created_at", "tags")
    inlines = [PostImageInline]


@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ("post", "image")
