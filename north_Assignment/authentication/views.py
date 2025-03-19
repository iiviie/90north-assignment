from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth.models import User
from social_django.utils import load_strategy
from social_django.utils import load_backend
from google.oauth2.credentials import Credentials
from google.oauth2 import id_token
from google.auth.transport import requests
from .serializers import UserSerializer
from .models import UserProfile
import json

class GoogleAuthURLView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Get Google OAuth2 authentication URL.
        
        Returns the URL where users should be redirected to start the Google OAuth2 flow.
        """
        strategy = load_strategy(request)
        backend = load_backend(strategy=strategy,
                             name='google-oauth2',
                             redirect_uri="http://localhost:8000/auth/google/callback/")
        
        return Response({
            'auth_url': backend.auth_url()
        })

class GoogleAuthCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Handle Google OAuth2 callback.
        
        Verify the Google token and create/update the user profile.
        
        Request Body:
          - token: Google OAuth2 token
        """
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
    """
    ViewSet for viewing and editing user profiles.
    
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id) 