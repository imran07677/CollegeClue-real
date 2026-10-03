from django.contrib import admin
from .models import (
    UserProfile,
    University,
    College,
    Course,
    Accommodation,
    StudentRegistration,
    Wishlist,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'organization_name', 'phone', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email', 'organization_name', 'phone')


class CourseInline(admin.TabularInline):
    model = Course
    extra = 1
    fields = ('name', 'duration_years', 'fee', 'seats')


class AccommodationInline(admin.StackedInline):
    model = Accommodation
    extra = 0
    fields = ('name', 'type', 'rent', 'room_type', 'is_available', 'contact_phone', 'contact_email')


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state', 'established_year', 'rating', 'website')
    list_filter = ('state', 'city', 'rating')
    search_fields = ('name', 'city', 'state', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('name', 'university', 'city', 'fees', 'rating', 'status', 'submitted_by')
    list_filter = ('status', 'university', 'city', 'rating')
    search_fields = ('name', 'city', 'university__name', 'facilities')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [CourseInline, AccommodationInline]
    actions = ['approve_colleges', 'reject_colleges']

    @admin.action(description="Approve selected colleges (Make Live)")
    def approve_colleges(self, request, queryset):
        updated = queryset.update(status='Approved')
        self.message_user(request, f"{updated} college(s) approved and published to database.")

    @admin.action(description="Reject selected colleges")
    def reject_colleges(self, request, queryset):
        updated = queryset.update(status='Rejected')
        self.message_user(request, f"{updated} college(s) marked as Rejected.")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'college', 'duration_years', 'fee', 'seats')
    list_filter = ('duration_years', 'college__university', 'college')
    search_fields = ('name', 'college__name', 'college__university__name')


@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'city', 'college', 'rent', 'room_type', 'is_available', 'status', 'submitted_by')
    list_filter = ('status', 'type', 'room_type', 'is_available', 'city')
    search_fields = ('name', 'address', 'city', 'college__name', 'facilities')
    actions = ['approve_accommodations', 'reject_accommodations']

    @admin.action(description="Approve selected accommodations (Make Live)")
    def approve_accommodations(self, request, queryset):
        updated = queryset.update(status='Approved')
        self.message_user(request, f"{updated} accommodation(s) approved and published.")

    @admin.action(description="Reject selected accommodations")
    def reject_accommodations(self, request, queryset):
        updated = queryset.update(status='Rejected')
        self.message_user(request, f"{updated} accommodation(s) marked as Rejected.")


@admin.register(StudentRegistration)
class StudentRegistrationAdmin(admin.ModelAdmin):
    list_display = ('registration_id', 'full_name', 'email', 'phone', 'college', 'course', 'status', 'created_at')
    list_filter = ('status', 'college', 'created_at')
    search_fields = ('registration_id', 'full_name', 'email', 'phone', 'college__name', 'course__name')
    readonly_fields = ('registration_id', 'created_at')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'university', 'created_at')
    list_filter = ('created_at', 'university')
    search_fields = ('user__username', 'user__email', 'university__name')
