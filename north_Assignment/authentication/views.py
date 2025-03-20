from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.conf import settings
from google.oauth2.credentials import Credentials
from google.oauth2 import id_token
from google.auth.transport import requests
from google_auth_oauthlib.flow import Flow
from datetime import datetime, timedelta
from .serializers import UserSerializer
from .models import UserProfile
from rest_framework.authtoken.models import Token
import json
import logging
import os

# Disable strict scope checking
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_IGNORE_SCOPE_CHANGE'] = '1'

logger = logging.getLogger(__name__)

class GoogleAuthURLView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Get Google OAuth2 authentication URL.
        
        Returns the URL where users should be redirected to start the Google OAuth2 flow.
        """
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        logger.debug(f"Using redirect URI: {redirect_uri}")
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                    "client_secret": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE
        )
        
        flow.redirect_uri = redirect_uri
        logger.debug(f"Flow configuration: {flow.client_config}")
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        logger.debug(f"Generated authorization URL: {authorization_url}")
        request.session['google_auth_state'] = state
        
        return Response({
            'auth_url': authorization_url
        })

class GoogleAuthCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            code = request.query_params.get('code')
            if not code:
                return Response({'error': 'No code provided'}, 
                              status=status.HTTP_400_BAD_REQUEST)

            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                        "client_secret": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                    }
                },
                scopes=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE
            )
            
            flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
            
            try:
                flow.fetch_token(code=code)
            except Exception as e:
                if "Scope has changed" in str(e):
                    flow = Flow.from_client_config(
                        {
                            "web": {
                                "client_id": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                                "client_secret": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                            }
                        },
                        scopes=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE
                    )
                    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
                    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
                    flow.fetch_token(code=code)
                else:
                    raise
            
            credentials = flow.credentials
            
            id_info = id_token.verify_oauth2_token(
                credentials.id_token, 
                requests.Request(), 
                settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
            )
            
            email = id_info['email']
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': id_info.get('given_name', ''),
                    'last_name': id_info.get('family_name', '')
                }
            )
            
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.google_token = credentials.token
            profile.refresh_token = credentials.refresh_token
            
            if credentials.expiry:
                profile.token_expiry = credentials.expiry
            
            profile.save()
            
            token, _ = Token.objects.get_or_create(user=user)
            
            user_data = UserSerializer(user).data
            user_data['profile'] = {
                'id': profile.id,
                'google_token': profile.google_token,
                'refresh_token': profile.refresh_token,
                'token_expiry': profile.token_expiry,
                'created_at': profile.created_at,
                'updated_at': profile.updated_at
            }
            user_data['api_token'] = token.key
            
            return Response(user_data)

        except Exception as e:
            return Response(
                {'error': f'General error: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id) 