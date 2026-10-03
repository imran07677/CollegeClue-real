from rest_framework import serializers
from core.models import (
    University,
    College,
    Course,
    Accommodation,
    StudentRegistration,
)


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'id',
            'name',
            'duration_years',
            'fee',
            'seats',
        ]


class CollegeSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True, read_only=True)
    university_name = serializers.CharField(source='university.name', read_only=True)

    class Meta:
        model = College
        fields = [
            'id',
            'name',
            'slug',
            'university',
            'university_name',
            'city',
            'description',
            'logo',
            'fees',
            'rating',
            'facilities',
            'courses',
        ]


class UniversitySerializer(serializers.ModelSerializer):
    colleges = CollegeSerializer(many=True, read_only=True)

    class Meta:
        model = University
        fields = [
            'id',
            'name',
            'slug',
            'city',
            'state',
            'description',
            'logo',
            'established_year',
            'website',
            'rating',
            'colleges',
        ]


class AccommodationSerializer(serializers.ModelSerializer):
    college_name = serializers.CharField(source='college.name', read_only=True)

    class Meta:
        model = Accommodation
        fields = [
            'id',
            'name',
            'type',
            'college',
            'college_name',
            'address',
            'city',
            'rent',
            'room_type',
            'facilities',
            'image',
            'contact_phone',
            'contact_email',
            'is_available',
        ]


class StudentRegistrationSerializer(serializers.ModelSerializer):
    registration_id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    status = serializers.CharField(read_only=True)
    college_name = serializers.CharField(source='college.name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = StudentRegistration
        fields = [
            'id',
            'registration_id',
            'full_name',
            'email',
            'phone',
            'college',
            'college_name',
            'course',
            'course_name',
            'status',
            'created_at',
        ]

    def validate_phone(self, value):
        digits = ''.join(c for c in value if c.isdigit())
        if len(digits) < 10:
            raise serializers.ValidationError("Phone number must contain at least 10 valid digits.")
        return value

    def validate(self, attrs):
        college = attrs.get('college')
        course = attrs.get('course')

        if college and course:
            if course.college_id != college.id:
                raise serializers.ValidationError({
                    'course': f"The course '{course.name}' does not belong to '{college.name}'."
                })
        return attrs
