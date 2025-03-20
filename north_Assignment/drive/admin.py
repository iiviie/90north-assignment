from django.contrib import admin
from .models import DriveFile

@admin.register(DriveFile)
class DriveFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'file_id', 'mime_type', 'size', 'created_at')
    list_filter = ('mime_type', 'created_at')
    search_fields = ('name', 'file_id', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
