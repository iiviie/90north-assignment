from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class DriveFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_id = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
