from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import ChatRoom, Message
from .serializers import (
    ChatRoomSerializer, 
    ChatRoomCreateSerializer, 
    MessageSerializer,
    UserSerializer
)
from rest_framework.authtoken.models import Token

# Create your views here.

# View to list all chat rooms
@login_required
def index(request):
    rooms = ChatRoom.objects.filter(participants=request.user)
    token, _ = Token.objects.get_or_create(user=request.user)
    
    return render(request, 'chat/index.html', {
        'rooms': rooms,
        'token': token.key
    })

# View to render the chat room template
@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Check if user is a participant in the room
    if request.user not in room.participants.all():
        return render(request, 'chat/error.html', {
            'error': 'You are not a participant in this chat room'
        })
    
    return render(request, 'chat/room.html', {
        'room_id': room_id,
        'user_id': request.user.id,
        'username': request.user.username
    })

class ChatRoomViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ChatRoomCreateSerializer
        return ChatRoomSerializer
    
    def get_queryset(self):
        return ChatRoom.objects.filter(participants=self.request.user)
    
    def perform_create(self, serializer):
        chat_room = serializer.save()
        chat_room.participants.add(self.request.user)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        try:
            room = self.get_object()
            
            if request.user not in room.participants.all():
                return Response(
                    {'error': 'You are not a participant in this chat room'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            content = request.data.get('content')
            if not content:
                return Response(
                    {'error': 'Message content is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            message = Message.objects.create(
                room=room,
                user=request.user,
                content=content
            )
            
            serializer = MessageSerializer(message)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        try:
            room = self.get_object()
            
            if request.user not in room.participants.all():
                return Response(
                    {'error': 'You are not a participant in this chat room'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            messages = room.messages.all()
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def users(self, request):
        try:
            users = User.objects.exclude(id=request.user.id)
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
