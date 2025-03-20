from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse
from django.conf import settings
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from .serializers import DriveFileSerializer, FileUploadSerializer
from .models import DriveFile
import io
import logging
import tempfile
import os
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)

class GoogleDriveViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_permissions(self):
        logger.debug(f"Request method: {self.request.method}")
        logger.debug(f"Auth header: {self.request.META.get('HTTP_AUTHORIZATION', 'No auth header')}")
        return super().get_permissions()
    
    def _get_drive_service(self, user):
        """Get Google Drive service for the authenticated user."""
        logger.debug(f"Getting drive service for user: {user.email}")
        profile = user.profile
        
        if not profile.google_token:
            logger.error(f"No Google token found for user: {user.email}")
            return None
            
        logger.debug(f"Using token: {profile.google_token[:10]}... for user: {user.email}")
        credentials = Credentials(
            token=profile.google_token,
            refresh_token=profile.refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            client_secret=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
            scopes=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE
        )
        
        return build('drive', 'v3', credentials=credentials)
    
    def list(self, request):
        """List files from Google Drive."""
        try:
            logger.debug(f"List files request from user: {request.user}")
            logger.debug(f"Auth header: {request.META.get('HTTP_AUTHORIZATION', 'No auth header')}")
            drive_service = self._get_drive_service(request.user)
            
            if not drive_service:
                return Response(
                    {'error': 'Google Drive not connected'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get files from Google Drive
            results = drive_service.files().list(
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime)",
                q="trashed=false"
            ).execute()
            
            items = results.get('files', [])
            
            logger.debug(f"Found {len(items)} files in Google Drive")
            for item in items:
                logger.debug(f"File: {item.get('name')} ({item.get('id')})")
            
            # Save files to database
            for item in items:
                DriveFile.objects.update_or_create(
                    user=request.user,
                    file_id=item['id'],
                    defaults={
                        'name': item.get('name', 'Unnamed'),
                        'mime_type': item.get('mimeType', 'unknown'),
                        'size': item.get('size')
                    }
                )
            
            # Get updated files from database
            files = DriveFile.objects.filter(user=request.user)
            serializer = DriveFileSerializer(files, many=True)
            
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return Response(
                {'error': f'Error listing files: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload a file to Google Drive."""
        try:
            serializer = FileUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            drive_service = self._get_drive_service(request.user)
            
            if not drive_service:
                return Response(
                    {'error': 'Google Drive not connected'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file_obj = serializer.validated_data['file']
            folder_id = serializer.validated_data.get('folder_id', None)
            
            # Save file to temporary location
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in file_obj.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # Prepare file metadata
                file_metadata = {
                    'name': file_obj.name
                }
                
                # If folder_id is provided, set parent folder
                if folder_id:
                    file_metadata['parents'] = [folder_id]
                
                # Upload file to Google Drive
                media = MediaFileUpload(
                    temp_file_path,
                    mimetype=file_obj.content_type,
                    resumable=True
                )
                
                file = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, mimeType, size'
                ).execute()
                
                # Save file to database
                drive_file = DriveFile.objects.create(
                    user=request.user,
                    file_id=file['id'],
                    name=file['name'],
                    mime_type=file['mimeType'],
                    size=file.get('size')
                )
                
                serializer = DriveFileSerializer(drive_file)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return Response(
                {'error': f'Error uploading file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a file from Google Drive."""
        try:
            drive_file = DriveFile.objects.get(id=pk, user=request.user)
            
            drive_service = self._get_drive_service(request.user)
            
            if not drive_service:
                return Response(
                    {'error': 'Google Drive not connected'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create a BytesIO object to store the downloaded file
            file_buffer = io.BytesIO()
            
            # Get the file from Google Drive
            request = drive_service.files().get_media(fileId=drive_file.file_id)
            downloader = MediaIoBaseDownload(file_buffer, request)
            
            # Download the file
            done = False
            while not done:
                status_download, done = downloader.next_chunk()
            
            # Reset the file pointer to the beginning
            file_buffer.seek(0)
            
            # Return the file as a response
            return FileResponse(
                file_buffer,
                as_attachment=True,
                filename=drive_file.name
            )
            
        except DriveFile.DoesNotExist:
            return Response(
                {'error': 'File not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return Response(
                {'error': f'Error downloading file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def test_auth(self, request):
        """Test endpoint to verify authentication."""
        return Response({
            'authenticated': True,
            'user': request.user.email,
            'auth_header': request.META.get('HTTP_AUTHORIZATION', 'No auth header')[:20] + '...' if request.META.get('HTTP_AUTHORIZATION') else 'None'
        })

    @action(detail=False, methods=['get'])
    def picker_config(self, request):
        """Get configuration for Google Picker API."""
        try:
            profile = request.user.profile
            
            if not profile.google_token:
                return Response(
                    {'error': 'Google Drive not connected'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'apiKey': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                'clientId': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                'developerKey': settings.GOOGLE_DEVELOPER_KEY,
                'appId': settings.GOOGLE_APP_ID,
                'token': profile.google_token,
                'scope': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE,
                'userId': request.user.email
            })
            
        except Exception as e:
            logger.error(f"Error getting picker config: {str(e)}")
            return Response(
                {'error': f'Error getting picker config: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def import_file(self, request):
        """Import a file from Google Drive."""
        try:
            file_id = request.data.get('file_id')
            if not file_id:
                return Response(
                    {'error': 'No file ID provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            drive_service = self._get_drive_service(request.user)
            
            if not drive_service:
                return Response(
                    {'error': 'Google Drive not connected'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get file metadata from Google Drive
            file = drive_service.files().get(fileId=file_id, fields='id,name,mimeType,size').execute()
            
            # Save file to database
            drive_file, created = DriveFile.objects.update_or_create(
                user=request.user,
                file_id=file['id'],
                defaults={
                    'name': file.get('name', 'Unnamed'),
                    'mime_type': file.get('mimeType', 'unknown'),
                    'size': file.get('size')
                }
            )
            
            serializer = DriveFileSerializer(drive_file)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error importing file: {str(e)}")
            return Response(
                {'error': f'Error importing file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def direct_list(self, request):
        """List files directly from Google Drive without saving to database."""
        try:
            drive_service = self._get_drive_service(request.user)
            
            if not drive_service:
                return Response(
                    {'error': 'Google Drive not connected'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get files from Google Drive
            results = drive_service.files().list(
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime)",
                q="trashed=false"
            ).execute()
            
            items = results.get('files', [])
            logger.debug(f"Found {len(items)} files in Google Drive")
            
            return Response(items)
            
        except Exception as e:
            logger.error(f"Error listing files directly: {str(e)}")
            return Response(
                {'error': f'Error listing files: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GooglePickerView(TemplateView):
    template_name = 'drive/picker.html'
