from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from core.models import University, College, Accommodation, StudentRegistration
from .serializers import (
    UniversitySerializer,
    CollegeSerializer,
    AccommodationSerializer,
    StudentRegistrationSerializer,
)


class UniversityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = University.objects.prefetch_related('colleges__courses').all()
    serializer_class = UniversitySerializer
    lookup_field = 'slug'


class CollegeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = College.objects.select_related('university').prefetch_related('courses').all()
    serializer_class = CollegeSerializer
    lookup_field = 'slug'


class AccommodationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Accommodation.objects.select_related('college').all()
    serializer_class = AccommodationSerializer


class StudentRegistrationCreateAPIView(generics.CreateAPIView):
    queryset = StudentRegistration.objects.all()
    serializer_class = StudentRegistrationSerializer

    def perform_create(self, serializer):
        registration = serializer.save()

        # Send confirmation email
        email_context = {
            'student_name': registration.full_name,
            'college_name': registration.college.name,
            'course_name': registration.course.name,
            'registration_id': str(registration.registration_id),
            'status': registration.status,
        }
        email_body = render_to_string(
            'core/emails/registration_confirmation.txt',
            email_context
        )

        try:
            send_mail(
                subject=f"Admission Registration Confirmation - {registration.registration_id}",
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[registration.email],
                fail_silently=False,
            )
        except Exception:
            # Continue even if email service has issues
            pass
