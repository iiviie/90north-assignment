from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GoogleDriveViewSet, GooglePickerView

router = DefaultRouter()
router.register(r'files', GoogleDriveViewSet, basename='drive-files')

urlpatterns = [
    path('', include(router.urls)),
    path('picker/', GooglePickerView.as_view(), name='google-picker'),
] 