from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth.models import User
from social_django.utils import load_strategy
from google.oauth2.credentials import Credentials
from google.oauth2 import id_token
from google.auth.transport import requests
from .serializers import UserSerializer
from .models import UserProfile
import json

class GoogleAuthURLView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        strategy = load_strategy(request)
        return Response({
            'auth_url': strategy.backend.auth_url()
        })

class GoogleAuthCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            token = request.data.get('token')
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
            )

            # Get or create user
            email = idinfo['email']
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': idinfo.get('given_name', ''),
                    'last_name': idinfo.get('family_name', '')
                }
            )

            profile = user.profile
            profile.google_token = token
            profile.save()

            serializer = UserSerializer(user)
            return Response(serializer.data)

        except ValueError:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id) 