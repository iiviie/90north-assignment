from django.contrib import admin
from .models import DriveFile

@admin.register(DriveFile)
class DriveFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'mime_type', 'size_formatted', 'created_at')
    list_filter = ('mime_type', 'created_at', 'user')
    search_fields = ('name', 'file_id', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    def size_formatted(self, obj):
        if obj.size is None:
            return 'N/A'
        for unit in ['B', 'KB', 'MB', 'GB']:
            if obj.size < 1024:
                return f"{obj.size:.2f} {unit}"
            obj.size /= 1024
        return f"{obj.size:.2f} TB"
    size_formatted.short_description = 'Size'
