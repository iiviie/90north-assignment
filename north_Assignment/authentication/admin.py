from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
