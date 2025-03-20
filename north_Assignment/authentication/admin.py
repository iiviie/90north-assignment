from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'token_expiry', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    exclude = ('google_token', 'refresh_token')
    list_filter = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
