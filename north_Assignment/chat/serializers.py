from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ChatRoom, Message

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'user', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']

class ChatRoomSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'participants', 'messages', 'created_at']
        read_only_fields = ['id', 'created_at']

class ChatRoomCreateSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True
    )
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'participant_ids', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids')
        chat_room = ChatRoom.objects.create(**validated_data)
        
        # Add participants to the chat room
        for user_id in participant_ids:
            try:
                user = User.objects.get(id=user_id)
                chat_room.participants.add(user)
            except User.DoesNotExist:
                pass
        
        return chat_room 