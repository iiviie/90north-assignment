from rest_framework import serializers
from .models import DriveFile

class DriveFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriveFile
        fields = ('id', 'file_id', 'name', 'mime_type', 'size', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    folder_id = serializers.CharField(required=False, allow_blank=True) 