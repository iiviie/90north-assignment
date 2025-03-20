from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.conf import settings
from social_django.utils import load_strategy
from social_django.utils import load_backend
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
        # Create the flow using the client secrets
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                    "client_secret": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost:8000/auth/google/callback/"]
                }
            },
            scopes=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE
        )
        
        # Set the redirect URI
        flow.redirect_uri = "http://localhost:8000/auth/google/callback/"
        
        # Generate the authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Store the state in the session
        request.session['google_auth_state'] = state
        
        return Response({
            'auth_url': authorization_url
        })

class GoogleAuthCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        logger.debug(f"Callback received. Query params: {request.query_params}")
        logger.debug(f"Full URL: {request.build_absolute_uri()}")
        
        try:
            code = request.query_params.get('code')
            logger.debug(f"Authorization code: {code}")
            if not code:
                return Response({'error': 'No code provided'}, 
                              status=status.HTTP_400_BAD_REQUEST)

            # Create the flow using the client secrets
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                        "client_secret": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost:8000/auth/google/callback/"]
                    }
                },
                scopes=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE
            )
            
            # Set the redirect URI
            flow.redirect_uri = "http://localhost:8000/auth/google/callback/"
            
            # Exchange the authorization code for credentials
            try:
                flow.fetch_token(code=code)
            except Exception as e:
                # If there's a scope mismatch, try with a more flexible approach
                if "Scope has changed" in str(e):
                    logger.debug("Scope mismatch detected, trying with flexible validation")
                    # Create a new flow without strict scope validation
                    flow = Flow.from_client_config(
                        {
                            "web": {
                                "client_id": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                                "client_secret": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": ["http://localhost:8000/auth/google/callback/"]
                            }
                        },
                        scopes=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE
                    )
                    flow.redirect_uri = "http://localhost:8000/auth/google/callback/"
                    
                    # Disable scope validation
                    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
                    flow.fetch_token(code=code)
                else:
                    # If it's not a scope issue, re-raise the exception
                    raise
            
            # Get the credentials
            credentials = flow.credentials
            logger.debug(f"Access token: {credentials.token}")
            
            # Get user info from Google
            id_info = id_token.verify_oauth2_token(
                credentials.id_token, 
                requests.Request(), 
                settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
            )
            
            # Get or create user
            email = id_info['email']
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': id_info.get('given_name', ''),
                    'last_name': id_info.get('family_name', '')
                }
            )
            
            # Create or get the user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.google_token = credentials.token
            profile.refresh_token = credentials.refresh_token
            
            # Set token expiry
            if credentials.expiry:
                profile.token_expiry = credentials.expiry
            
            profile.save()
            
            # Create or get token for API authentication
            token, _ = Token.objects.get_or_create(user=user)
            
            # Return user data and tokens
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