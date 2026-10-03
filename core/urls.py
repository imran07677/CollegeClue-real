from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about_view, name='about'),

    # Universities
    path('universities/', views.university_list, name='university_list'),
    path('universities/<slug:slug>/', views.university_detail, name='university_detail'),

    # Colleges
    path('colleges/', views.college_list, name='college_list'),
    path('colleges/<slug:slug>/', views.college_detail, name='college_detail'),
    path('colleges/<slug:slug>/accommodations/', views.college_accommodations_view, name='college_accommodations'),

    # Comparison
    path('compare/', views.compare_colleges, name='compare'),
    path('compare/toggle/<int:college_id>/', views.compare_toggle, name='compare_toggle'),
    path('compare/add/<int:college_id>/', views.compare_add, name='compare_add'),
    path('compare/remove/<int:college_id>/', views.compare_remove, name='compare_remove'),
    path('compare/clear/', views.compare_clear, name='compare_clear'),

    # Accommodation
    path('accommodations/', views.accommodation_list, name='accommodation_list'),
    path('accommodations/<int:pk>/', views.accommodation_detail, name='accommodation_detail'),

    # Wishlist
    path('wishlist/', views.wishlist_list, name='wishlist'),
    path('wishlist/toggle/<int:university_id>/', views.wishlist_toggle, name='wishlist_toggle'),

    # Campus & Housing Location Finder
    path('finder/', views.finder_view, name='finder'),
    path('api/location-colleges/', views.location_colleges_api, name='api_location_colleges'),
    path('api/college-recommendations/<int:college_id>/', views.college_recommendations_api, name='api_college_recommendations'),

    # Student Course Dynamic API
    path('courses/by-college/<int:college_id>/', views.courses_by_college_api, name='courses_by_college_api'),

    # Student Admission Registration & Application Status
    path('register-admission/', views.registration_form_view, name='registration_form'),
    path('register-admission/success/<uuid:registration_id>/', views.registration_success_view, name='registration_success'),
    path('applications/', views.my_applications_view, name='my_applications'),

    # Authentication & OTP Verification
    path('account/login/', views.user_login_view, name='login'),
    path('account/logout/', views.user_logout_view, name='logout'),
    path('account/register/', views.user_register_view, name='register'),
    path('account/send-otp/', views.send_registration_otp, name='send_registration_otp'),
    path('account/verify-otp/', views.verify_registration_otp, name='verify_registration_otp'),

    # University & College Partner Portal
    path('partner/university/', views.university_dashboard_view, name='university_dashboard'),
    path('partner/university/applications/', views.university_applications_view, name='university_applications'),
    path('partner/university/applications/<uuid:registration_id>/approve/', views.university_application_approve_view, name='university_application_approve'),
    path('partner/university/applications/<uuid:registration_id>/reject/', views.university_application_reject_view, name='university_application_reject'),
    path('partner/university/applications/<uuid:registration_id>/update-status/', views.university_application_status_update_view, name='university_application_status_update'),
    path('partner/university/submit-college/', views.college_submit_view, name='college_submit'),
    path('partner/university/college/<int:college_id>/edit/', views.college_edit_view, name='college_edit'),
    path('partner/university/college/<int:college_id>/courses/', views.college_courses_view, name='college_courses'),
    path('partner/university/college/<int:college_id>/toggle-admission/', views.college_admission_toggle_view, name='college_admission_toggle'),
    path('partner/university/college/<int:college_id>/admission-dates/', views.college_admission_dates_update_view, name='college_admission_dates_update'),
    path('partner/university/<int:university_id>/location/', views.university_location_update_view, name='university_location_update'),
    path('partner/university/college/<int:college_id>/team/', views.college_team_management_view, name='college_team'),
    path('partner/university/college/<int:college_id>/add-course/', views.course_add_view, name='course_add'),
    path('partner/university/college/<int:college_id>/delete-course/<int:course_id>/', views.course_delete_view, name='course_delete'),
    path('partner/university/college/<int:college_id>/course/<int:course_id>/edit/', views.course_edit_view, name='course_edit'),

    # Accommodation Provider & PG Owner Partner Portal
    path('partner/accommodation/', views.accommodation_dashboard_view, name='accommodation_dashboard'),
    path('partner/accommodation/submit/', views.accommodation_submit_view, name='accommodation_submit'),
    path('partner/accommodation/<int:acc_id>/edit/', views.accommodation_edit_view, name='accommodation_edit'),
    path('partner/accommodation/<int:acc_id>/toggle-vacancy/', views.accommodation_toggle_vacancy_view, name='accommodation_toggle_vacancy'),

    # Live Search Suggestions API
    path('api/search-suggest/', views.api_search_suggest, name='api_search_suggest'),

    # Real Admin Moderation & Approval Center
    path('admin-portal/login/', views.admin_login_view, name='admin_login'),
    path('admin-portal/moderation/', views.admin_moderation_view, name='admin_moderation'),
    path('admin-portal/moderation/approve-college/<int:college_id>/', views.admin_approve_college_view, name='admin_approve_college'),
    path('admin-portal/moderation/reject-college/<int:college_id>/', views.admin_reject_college_view, name='admin_reject_college'),
    path('admin-portal/moderation/reset-college/<int:college_id>/', views.admin_reset_college_view, name='admin_reset_college'),
    path('admin-portal/moderation/approve-accommodation/<int:acc_id>/', views.admin_approve_acc_view, name='admin_approve_acc'),
    path('admin-portal/moderation/reject-accommodation/<int:acc_id>/', views.admin_reject_acc_view, name='admin_reject_acc'),
]
