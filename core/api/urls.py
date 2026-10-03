from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UniversityViewSet,
    CollegeViewSet,
    AccommodationViewSet,
    StudentRegistrationCreateAPIView,
)

router = DefaultRouter()
router.register(r'universities', UniversityViewSet, basename='api-university')
router.register(r'colleges', CollegeViewSet, basename='api-college')
router.register(r'accommodations', AccommodationViewSet, basename='api-accommodation')

urlpatterns = [
    path('register/', StudentRegistrationCreateAPIView.as_view(), name='api-register'),
    path('', include(router.urls)),
]
