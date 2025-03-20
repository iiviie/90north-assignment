from django.contrib import admin
from .models import ChatRoom, Message

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'get_participants_count')
    search_fields = ('name', 'participants__username', 'participants__email')
    filter_horizontal = ('participants',)
    readonly_fields = ('created_at',)
    
    def get_participants_count(self, obj):
        return obj.participants.count()
    get_participants_count.short_description = 'Participants'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'user', 'content_preview', 'created_at')
    search_fields = ('content', 'user__username', 'room__name')
    list_filter = ('room', 'created_at')
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
