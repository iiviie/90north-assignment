from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GoogleAuthURLView, GoogleAuthCallbackView, UserProfileViewSet

router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
    path('google/auth-url/', GoogleAuthURLView.as_view(), name='google-auth-url'),
    path('google/callback/', GoogleAuthCallbackView.as_view(), name='google-auth-callback'),
] 