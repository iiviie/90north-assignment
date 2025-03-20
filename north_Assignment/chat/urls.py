from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatRoomViewSet, chat_room, index

router = DefaultRouter()
router.register(r'rooms', ChatRoomViewSet, basename='chatroom')

urlpatterns = [
    path('', index, name='chat_index'),
    path('api/', include(router.urls)),
    path('room/<int:room_id>/', chat_room, name='chat_room'),
] 