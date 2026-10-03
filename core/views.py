import uuid
import json
import secrets
import datetime
import urllib.parse
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Min, Max

from .models import (
    University,
    College,
    Course,
    Accommodation,
    StudentRegistration,
    Wishlist,
    UserProfile,
    CollegeTeamMember,
    EmailVerificationOTP,
)
from .forms import (
    UniversityFilterForm,
    CollegeFilterForm,
    AccommodationFilterForm,
    StudentRegistrationForm,
    CustomUserRegistrationForm,
    CollegeSubmissionForm,
    AccommodationSubmissionForm,
    CollegeEditForm,
    CourseForm,
    AccommodationEditForm,
    UniversityLocationForm,
    UserLoginForm,
    CollegeAdmissionDatesForm,
)
from .college_insights import (
    get_college_about,
    get_college_placements,
    get_college_companies,
)


def home(request):
    featured_universities = University.objects.all().order_by('-rating')[:4]
    featured_colleges = College.objects.filter(status='Approved').select_related('university').all().order_by('-rating')[:6]
    recent_accommodations = Accommodation.objects.filter(status='Approved', is_available=True).order_by('-rent')[:3]
    unique_cities = list(College.objects.filter(status='Approved').values_list('city', flat=True).distinct().order_by('city'))

    stats = {
        'total_universities': University.objects.count(),
        'total_colleges': College.objects.filter(status='Approved').count(),
        'total_courses': Course.objects.filter(college__status='Approved').count(),
        'total_accommodations': Accommodation.objects.filter(status='Approved').count(),
        'total_applications': StudentRegistration.objects.count(),
    }

    # Student-specific context attributes when authenticated
    user_applications = []
    user_applications_count = 0
    wishlist_count = 0
    compare_count = len(request.session.get('compare_colleges', []))
    latest_application = None

    user_wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        user_wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list('university_id', flat=True))
        session_reg_ids = request.session.get('my_registration_ids', [])
        q_filter = Q()
        if request.user.email:
            q_filter |= Q(email__iexact=request.user.email)
        if session_reg_ids:
            q_filter |= Q(registration_id__in=session_reg_ids)
        if q_filter:
            user_apps_qs = StudentRegistration.objects.filter(q_filter).select_related('college__university', 'course').order_by('-created_at')
            user_applications_count = user_apps_qs.count()
            user_applications = list(user_apps_qs[:3])
            if user_applications:
                latest_application = user_applications[0]

    context = {
        'featured_universities': featured_universities,
        'featured_colleges': featured_colleges,
        'recent_accommodations': recent_accommodations,
        'unique_cities': unique_cities,
        'stats': stats,
        'user_applications': user_applications,
        'user_applications_count': user_applications_count,
        'wishlist_count': wishlist_count,
        'user_wishlist_ids': user_wishlist_ids,
        'compare_count': compare_count,
        'latest_application': latest_application,
    }
    return render(request, 'core/home.html', context)


def finder_view(request):
    """
    Dedicated interactive step-by-step workflow:
    1. Enter / Select Location (City)
    2. Show colleges of that location
    3. When college selected -> Recommend nearby PGs & Hostels + Admission Action
    """
    unique_cities = list(College.objects.filter(status='Approved').values_list('city', flat=True).distinct().order_by('city'))
    selected_city = request.GET.get('city', '').strip()
    selected_college_id = request.GET.get('college')

    colleges_in_city = []
    selected_college = None
    recommended_accommodations = []

    if selected_city:
        colleges_in_city = College.objects.filter(status='Approved', city__icontains=selected_city).select_related('university').prefetch_related('courses')
    
    if selected_college_id:
        try:
            selected_college = College.objects.select_related('university').prefetch_related('courses').get(id=int(selected_college_id), status='Approved')
            direct_accs = list(selected_college.accommodations.filter(status='Approved', is_available=True))
            direct_ids = [a.id for a in direct_accs]
            city_accs = list(
                Accommodation.objects.filter(
                    city__iexact=selected_college.city,
                    status='Approved',
                    is_available=True
                ).exclude(id__in=direct_ids)
            )
            recommended_accommodations = direct_accs + city_accs
        except (College.DoesNotExist, ValueError):
            selected_college = None

    context = {
        'unique_cities': unique_cities,
        'selected_city': selected_city,
        'colleges_in_city': colleges_in_city,
        'selected_college': selected_college,
        'recommended_accommodations': recommended_accommodations,
    }
    return render(request, 'core/finder.html', context)


def location_colleges_api(request):
    """
    API endpoint returning colleges for a given city location.
    """
    city = request.GET.get('city', '').strip()
    if not city:
        return JsonResponse({'colleges': []})
    
    colleges = College.objects.filter(status='Approved', city__icontains=city).select_related('university').prefetch_related('courses')
    data = [
        {
            'id': c.id,
            'name': c.name,
            'slug': c.slug,
            'university': c.university.name,
            'city': c.city,
            'fees': str(c.fees),
            'rating': str(c.rating),
            'facilities': c.facilities,
            'courses_count': c.courses.count(),
        }
        for c in colleges
    ]
    return JsonResponse({'city': city, 'colleges': data})


def college_recommendations_api(request, college_id):
    """
    API endpoint returning college details, courses, and recommended nearby PGs and Hostels.
    """
    college = get_object_or_404(College.objects.select_related('university').prefetch_related('courses'), id=college_id)
    courses = [
        {
            'id': c.id,
            'name': c.name,
            'duration_years': c.duration_years,
            'fee': str(c.fee),
            'seats': c.seats,
        }
        for c in college.courses.all()
    ]
    
    direct_accs = list(college.accommodations.filter(is_available=True))
    direct_ids = [a.id for a in direct_accs]
    city_accs = list(
        Accommodation.objects.filter(
            city__iexact=college.city,
            is_available=True
        ).exclude(id__in=direct_ids)
    )
    all_accs = direct_accs + city_accs

    accommodations_data = [
        {
            'id': a.id,
            'name': a.name,
            'type': a.type,
            'address': a.address,
            'city': a.city,
            'rent': str(a.rent),
            'room_type': a.room_type,
            'facilities': a.facilities,
            'contact_phone': a.contact_phone,
            'contact_email': a.contact_email,
            'is_direct': a.college_id == college.id,
        }
        for a in all_accs
    ]

    return JsonResponse({
        'college': {
            'id': college.id,
            'name': college.name,
            'slug': college.slug,
            'university': college.university.name,
            'city': college.city,
            'fees': str(college.fees),
            'rating': str(college.rating),
            'facilities': college.facilities,
            'description': college.description,
        },
        'courses': courses,
        'accommodations': accommodations_data,
    })


def college_detail(request, slug):
    college = get_object_or_404(
        College.objects.select_related('university').prefetch_related('courses', 'accommodations'),
        slug=slug
    )
    courses = college.courses.all()
    direct_accommodations = list(college.accommodations.filter(is_available=True))
    direct_ids = [a.id for a in direct_accommodations]
    nearby_city_accommodations = list(
        Accommodation.objects.filter(
            city__iexact=college.city,
            is_available=True
        ).exclude(id__in=direct_ids)
    )
    all_recommended_accommodations = direct_accommodations + nearby_city_accommodations

    compare_list = request.session.get('compare_colleges', [])
    is_in_compare = college.id in compare_list

    is_college_admin = college.is_admin_or_team(request.user) if request.user.is_authenticated else False

    about_info = get_college_about(college)
    placement_info = get_college_placements(college)
    companies_info = get_college_companies(college)

    context = {
        'college': college,
        'courses': courses,
        'about_info': about_info,
        'placement_info': placement_info,
        'companies_info': companies_info,
        'direct_accommodations': direct_accommodations,
        'nearby_city_accommodations': nearby_city_accommodations,
        'accommodations': all_recommended_accommodations,
        'is_in_compare': is_in_compare,
        'is_college_admin': is_college_admin,
    }
    return render(request, 'core/college_detail.html', context)


def college_accommodations_view(request, slug):
    """
    Dedicated page showing all verified PGs & Hostels recommended for a specific college.
    """
    college = get_object_or_404(
        College.objects.select_related('university').prefetch_related('courses', 'accommodations'),
        slug=slug
    )
    direct_accommodations = list(college.accommodations.filter(is_available=True))
    direct_ids = [a.id for a in direct_accommodations]
    nearby_city_accommodations = list(
        Accommodation.objects.filter(
            city__iexact=college.city,
            is_available=True
        ).exclude(id__in=direct_ids)
    )
    all_accommodations = direct_accommodations + nearby_city_accommodations

    context = {
        'college': college,
        'direct_accommodations': direct_accommodations,
        'nearby_city_accommodations': nearby_city_accommodations,
        'accommodations': all_accommodations,
    }
    return render(request, 'core/college_accommodations.html', context)


def university_list(request):
    form = UniversityFilterForm(request.GET or None)
    queryset = University.objects.prefetch_related('colleges__courses').all()

    search = request.GET.get('search', '').strip() or request.GET.get('q', '').strip()
    location = request.GET.get('location', '').strip() or request.GET.get('city', '').strip()
    course_type = request.GET.get('course_type', '').strip()
    budget = request.GET.get('budget', '').strip()
    state = request.GET.get('state', '').strip()
    min_rating = request.GET.get('min_rating', '').strip()
    established_year = request.GET.get('established_year', '').strip()

    active_filters_count = 0
    if search:
        active_filters_count += 1
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(city__icontains=search) |
            Q(state__icontains=search) |
            Q(colleges__name__icontains=search) |
            Q(colleges__courses__name__icontains=search)
        ).distinct()

    if location:
        active_filters_count += 1
        queryset = queryset.filter(
            Q(city__icontains=location) |
            Q(state__icontains=location) |
            Q(colleges__city__icontains=location)
        ).distinct()

    if course_type:
        active_filters_count += 1
        if course_type == 'engineering':
            kw_q = Q()
            for kw in ['engineering', 'tech', 'b.tech', 'm.tech', 'btech', 'mtech', 'computer science', 'mechanical', 'electrical', 'civil']:
                kw_q |= Q(colleges__courses__name__icontains=kw) | Q(colleges__name__icontains=kw)
            queryset = queryset.filter(kw_q).distinct()
        elif course_type == 'management':
            kw_q = Q()
            for kw in ['management', 'mba', 'bba', 'pgdm', 'business', 'strategy']:
                kw_q |= Q(colleges__courses__name__icontains=kw) | Q(colleges__name__icontains=kw)
            queryset = queryset.filter(kw_q).distinct()
        elif course_type == 'computer_it':
            kw_q = Q()
            for kw in ['computer', 'bca', 'mca', 'data science', 'ai', 'artificial intelligence', 'information technology', 'software']:
                kw_q |= Q(colleges__courses__name__icontains=kw) | Q(colleges__name__icontains=kw)
            queryset = queryset.filter(kw_q).distinct()
        elif course_type == 'sciences':
            kw_q = Q()
            for kw in ['science', 'b.sc', 'm.sc', 'bsc', 'msc', 'physics', 'chemistry', 'mathematics', 'biotech', 'biology']:
                kw_q |= Q(colleges__courses__name__icontains=kw) | Q(colleges__name__icontains=kw)
            queryset = queryset.filter(kw_q).distinct()
        elif course_type == 'commerce':
            kw_q = Q()
            for kw in ['commerce', 'b.com', 'm.com', 'bcom', 'mcom', 'finance', 'banking', 'accounting', 'economics']:
                kw_q |= Q(colleges__courses__name__icontains=kw) | Q(colleges__name__icontains=kw)
            queryset = queryset.filter(kw_q).distinct()
        elif course_type == 'arts':
            kw_q = Q()
            for kw in ['arts', 'b.a', 'm.a', 'ba', 'ma', 'humanities', 'journalism', 'design', 'law']:
                kw_q |= Q(colleges__courses__name__icontains=kw) | Q(colleges__name__icontains=kw)
            queryset = queryset.filter(kw_q).distinct()

    if budget:
        active_filters_count += 1
        if budget == 'under_100k':
            queryset = queryset.filter(Q(colleges__fees__lte=100000) | Q(colleges__courses__fee__lte=100000)).distinct()
        elif budget == '100k_200k':
            queryset = queryset.filter(
                (Q(colleges__fees__gte=100000) & Q(colleges__fees__lte=200000)) |
                (Q(colleges__courses__fee__gte=100000) & Q(colleges__courses__fee__lte=200000))
            ).distinct()
        elif budget == '200k_350k':
            queryset = queryset.filter(
                (Q(colleges__fees__gte=200000) & Q(colleges__fees__lte=350000)) |
                (Q(colleges__courses__fee__gte=200000) & Q(colleges__courses__fee__lte=350000))
            ).distinct()
        elif budget == 'above_350k':
            queryset = queryset.filter(Q(colleges__fees__gte=350000) | Q(colleges__courses__fee__gte=350000)).distinct()

    if state:
        active_filters_count += 1
        queryset = queryset.filter(state__icontains=state)
    if min_rating:
        try:
            val = float(min_rating)
            active_filters_count += 1
            queryset = queryset.filter(rating__gte=val)
        except ValueError:
            pass
    if established_year:
        try:
            yr = int(established_year)
            active_filters_count += 1
            queryset = queryset.filter(established_year__gte=yr)
        except ValueError:
            pass

    user_wishlist_ids = []
    if request.user.is_authenticated:
        user_wishlist_ids = list(
            Wishlist.objects.filter(user=request.user).values_list('university_id', flat=True)
        )

    # Distinct locations for the dropdown
    uni_cities = list(University.objects.values_list('city', flat=True).distinct())
    col_cities = list(College.objects.filter(status='Approved').values_list('city', flat=True).distinct())
    available_locations = sorted(list(set(c for c in uni_cities + col_cities if c)))

    available_cities = list(University.objects.values_list('city', flat=True).distinct().order_by('city'))
    available_states = list(University.objects.values_list('state', flat=True).distinct().order_by('state'))

    context = {
        'form': form,
        'universities': queryset.order_by('-rating'),
        'user_wishlist_ids': user_wishlist_ids,
        'search_query': search,
        'location': location,
        'course_type': course_type,
        'budget': budget,
        'active_filters_count': active_filters_count,
        'available_locations': available_locations,
        'available_cities': available_cities,
        'available_states': available_states,
        'hide_navbar_search': True,
    }
    return render(request, 'core/university_list.html', context)


def university_detail(request, slug):
    university = get_object_or_404(University, slug=slug)
    colleges = university.colleges.prefetch_related('courses').all()

    # STRICTLY show only accommodations located near this university's colleges:
    recommended_accommodations = Accommodation.objects.filter(
        college__university=university,
        is_available=True,
        status='Approved'
    ).select_related('college').distinct()

    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = Wishlist.objects.filter(
            user=request.user,
            university=university
        ).exists()

    context = {
        'university': university,
        'colleges': colleges,
        'accommodations': recommended_accommodations,
        'is_wishlisted': is_wishlisted,
        'compare_list': request.session.get('compare_colleges', []),
    }
    return render(request, 'core/university_detail.html', context)


def college_list(request):
    form = CollegeFilterForm(request.GET or None)
    queryset = College.objects.filter(status='Approved').select_related('university').prefetch_related('courses').all()

    search = request.GET.get('search', '').strip()
    city = request.GET.get('city', '').strip()
    course = request.GET.get('course', '').strip() or request.GET.get('course_name', '').strip()
    max_fee = request.GET.get('max_fee', '').strip()
    min_fee = request.GET.get('min_fee', '').strip()
    rating = request.GET.get('rating', '').strip()

    if form.is_valid():
        if not search and form.cleaned_data.get('search'):
            search = form.cleaned_data.get('search')
        if not city and form.cleaned_data.get('city'):
            city = form.cleaned_data.get('city')
        if not course and form.cleaned_data.get('course_name'):
            course = form.cleaned_data.get('course_name')
        if not max_fee and form.cleaned_data.get('max_fee'):
            max_fee = str(form.cleaned_data.get('max_fee'))

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(facilities__icontains=search) |
            Q(description__icontains=search) |
            Q(university__name__icontains=search) |
            Q(courses__name__icontains=search)
        ).distinct()
    if city:
        queryset = queryset.filter(city__iexact=city) if queryset.filter(city__iexact=city).exists() else queryset.filter(city__icontains=city)
    if course:
        queryset = queryset.filter(courses__name__icontains=course).distinct()
    if max_fee:
        try:
            queryset = queryset.filter(fees__lte=Decimal(max_fee))
        except (ValueError, TypeError):
            pass
    if min_fee:
        try:
            queryset = queryset.filter(fees__gte=Decimal(min_fee))
        except (ValueError, TypeError):
            pass
    if rating:
        try:
            queryset = queryset.filter(rating__gte=Decimal(rating))
        except (ValueError, TypeError):
            pass

    compare_list = request.session.get('compare_colleges', [])

    context = {
        'form': form,
        'colleges': queryset,
        'compare_list': compare_list,
        'active_city': city,
        'active_course': course,
        'active_max_fee': max_fee,
        'active_search': search,
        'hide_navbar_search': True,
    }
    return render(request, 'core/college_list.html', context)



def compare_colleges(request):
    compare_ids = request.session.get('compare_colleges', [])
    colleges = College.objects.filter(id__in=compare_ids).select_related('university').prefetch_related('courses')

    context = {
        'colleges': colleges,
        'compare_count': len(compare_ids),
    }
    return render(request, 'core/compare.html', context)


def compare_toggle(request, college_id):
    """
    Seamless toggle endpoint for adding/removing colleges from comparison.
    Strictly caps comparison at 4 colleges.
    Returns JSON when requested via AJAX/fetch (preventing full-page reload and screen shake).
    """
    college = get_object_or_404(College, id=college_id)
    compare_list = request.session.get('compare_colleges', [])
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or \
              'application/json' in request.headers.get('accept', '') or \
              request.GET.get('format') == 'json'

    if college.id in compare_list:
        compare_list.remove(college.id)
        request.session['compare_colleges'] = compare_list
        if is_ajax:
            return JsonResponse({
                'status': 'removed',
                'action': 'removed',
                'success': True,
                'is_in_compare': False,
                'college_id': college.id,
                'college_name': college.name,
                'count': len(compare_list),
                'max_limit': 4,
                'message': f"{college.name} removed from comparison."
            })
        messages.info(request, f"{college.name} removed from comparison.")
    else:
        if len(compare_list) >= 4:
            if is_ajax:
                return JsonResponse({
                    'status': 'limit_reached',
                    'action': 'none',
                    'success': False,
                    'is_in_compare': False,
                    'college_id': college.id,
                    'college_name': college.name,
                    'count': len(compare_list),
                    'max_limit': 4,
                    'message': "Maximum 4 colleges can be compared at a time."
                })
            messages.warning(request, "You can compare up to 4 colleges at a time.")
        else:
            compare_list.append(college.id)
            request.session['compare_colleges'] = compare_list
            if is_ajax:
                return JsonResponse({
                    'status': 'added',
                    'action': 'added',
                    'success': True,
                    'is_in_compare': True,
                    'college_id': college.id,
                    'college_name': college.name,
                    'count': len(compare_list),
                    'max_limit': 4,
                    'message': f"{college.name} added to comparison."
                })
            messages.success(request, f"{college.name} added to comparison.")

    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('compare')
    return redirect(next_url)


def compare_add(request, college_id):
    college = get_object_or_404(College, id=college_id)
    compare_list = request.session.get('compare_colleges', [])
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or \
              'application/json' in request.headers.get('accept', '') or \
              request.GET.get('format') == 'json'

    if college.id not in compare_list:
        if len(compare_list) >= 4:
            if is_ajax:
                return JsonResponse({
                    'status': 'limit_reached',
                    'action': 'none',
                    'success': False,
                    'is_in_compare': False,
                    'college_id': college.id,
                    'college_name': college.name,
                    'count': len(compare_list),
                    'max_limit': 4,
                    'message': "Maximum 4 colleges can be compared at a time."
                })
            messages.warning(request, "You can compare up to 4 colleges at a time.")
        else:
            compare_list.append(college.id)
            request.session['compare_colleges'] = compare_list
            if is_ajax:
                return JsonResponse({
                    'status': 'added',
                    'action': 'added',
                    'success': True,
                    'is_in_compare': True,
                    'college_id': college.id,
                    'college_name': college.name,
                    'count': len(compare_list),
                    'max_limit': 4,
                    'message': f"{college.name} added to comparison."
                })
            messages.success(request, f"{college.name} added to comparison.")
    else:
        if is_ajax:
            return JsonResponse({
                'status': 'already_added',
                'action': 'none',
                'success': True,
                'is_in_compare': True,
                'college_id': college.id,
                'college_name': college.name,
                'count': len(compare_list),
                'max_limit': 4,
                'message': f"{college.name} is already in comparison."
            })
        messages.info(request, f"{college.name} is already in comparison.")

    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('compare')
    return redirect(next_url)


def compare_remove(request, college_id):
    compare_list = request.session.get('compare_colleges', [])
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or \
              'application/json' in request.headers.get('accept', '') or \
              request.GET.get('format') == 'json'

    if college_id in compare_list:
        compare_list.remove(college_id)
        request.session['compare_colleges'] = compare_list
        if is_ajax:
            return JsonResponse({
                'status': 'removed',
                'action': 'removed',
                'success': True,
                'is_in_compare': False,
                'college_id': college_id,
                'count': len(compare_list),
                'max_limit': 4,
                'message': "College removed from comparison."
            })
        messages.info(request, "College removed from comparison.")
    else:
        if is_ajax:
            return JsonResponse({
                'status': 'not_in_compare',
                'action': 'none',
                'success': True,
                'is_in_compare': False,
                'college_id': college_id,
                'count': len(compare_list),
                'max_limit': 4,
                'message': "College was not in comparison."
            })

    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('compare')
    return redirect(next_url)


def compare_clear(request):
    request.session['compare_colleges'] = []
    messages.info(request, "College comparison cleared.")
    return redirect('compare')


def accommodation_list(request):
    form = AccommodationFilterForm(request.GET or None)
    queryset = Accommodation.objects.filter(status='Approved').select_related('college__university').all()

    search_query = request.GET.get('q', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(facilities__icontains=search_query) |
            Q(college__name__icontains=search_query) |
            Q(college__university__name__icontains=search_query)
        )

    if form.is_valid():
        college = form.cleaned_data.get('college')
        city = form.cleaned_data.get('city')
        acc_type = form.cleaned_data.get('type')
        room_type = form.cleaned_data.get('room_type')
        min_rent = form.cleaned_data.get('min_rent')
        max_rent = form.cleaned_data.get('max_rent')

        if college:
            queryset = queryset.filter(college=college)
        if city:
            queryset = queryset.filter(city__icontains=city)
        if acc_type:
            queryset = queryset.filter(type=acc_type)
        if room_type:
            queryset = queryset.filter(room_type=room_type)
        if min_rent is not None:
            queryset = queryset.filter(rent__gte=min_rent)
        if max_rent is not None:
            queryset = queryset.filter(rent__lte=max_rent)

    colleges = College.objects.filter(status='Approved').select_related('university').order_by('name')

    # Count how many filters are currently active
    active_filters_count = 0
    if request.GET.get('college'): active_filters_count += 1
    if request.GET.get('room_type'): active_filters_count += 1
    if request.GET.get('min_rent') or request.GET.get('max_rent'): active_filters_count += 1
    if request.GET.get('type'): active_filters_count += 1
    if request.GET.get('city'): active_filters_count += 1

    context = {
        'form': form,
        'accommodations': queryset,
        'search_query': search_query,
        'colleges': colleges,
        'active_filters_count': active_filters_count,
        'hide_navbar_search': True,
    }
    return render(request, 'core/accommodation_list.html', context)


def accommodation_detail(request, pk):
    accommodation = get_object_or_404(
        Accommodation.objects.select_related('college', 'college__university'),
        pk=pk
    )
    context = {
        'accommodation': accommodation,
    }
    return render(request, 'core/accommodation_detail.html', context)


@login_required
def wishlist_list(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('university')
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'core/wishlist.html', context)


def wishlist_toggle(request, university_id):
    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.headers.get('accept') == 'application/json' or
        request.GET.get('format') == 'json'
    )

    if not request.user.is_authenticated:
        if is_ajax:
            login_url = f"{reverse('login')}?next={request.GET.get('next', reverse('home'))}"
            return JsonResponse({
                'status': 'unauthenticated',
                'login_url': login_url,
                'message': 'Please login to save institutions to your wishlist.'
            }, status=401)
        messages.warning(request, "Please log in to manage your wishlist.")
        return redirect(f"{reverse('login')}?next={request.path}")

    university = get_object_or_404(University, id=university_id)
    item = Wishlist.objects.filter(user=request.user, university=university).first()

    if item:
        item.delete()
        is_wishlisted = False
        msg = f"Removed {university.name} from your wishlist."
    else:
        Wishlist.objects.create(user=request.user, university=university)
        is_wishlisted = True
        msg = f"Added {university.name} to your wishlist!"

    wishlist_count = Wishlist.objects.filter(user=request.user).count()

    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'is_wishlisted': is_wishlisted,
            'wishlist_count': wishlist_count,
            'message': msg,
            'university_id': university.id,
            'university_name': university.name
        })

    if is_wishlisted:
        messages.success(request, msg)
    else:
        messages.info(request, msg)

    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('wishlist')
    return redirect(next_url)


def courses_by_college_api(request, college_id):
    """
    JSON endpoint for dynamic client-side filtering of courses and eligibility cutoffs based on selected college.
    """
    try:
        college = College.objects.get(id=college_id)
        college_name = college.name
        min_10th = float(college.min_10th_percentage) if college.min_10th_percentage is not None else 50.0
        min_12th = float(college.min_12th_percentage) if college.min_12th_percentage is not None else 50.0
    except College.DoesNotExist:
        college_name = ""
        min_10th = 50.0
        min_12th = 50.0

    courses = Course.objects.filter(college_id=college_id).order_by('name')
    data = [
        {
            'id': course.id,
            'name': course.name,
            'duration_years': course.duration_years,
            'fee': str(course.fee),
            'seats': course.available_seats,
            'total_seats': course.seats,
        }
        for course in courses
    ]
    return JsonResponse({
        'college_name': college_name,
        'min_10th_percentage': min_10th,
        'min_12th_percentage': min_12th,
        'courses': data,
    })


def registration_form_view(request):
    # Enforce student login requirement: redirect to login first if not logged in as student
    if not request.user.is_authenticated:
        messages.info(request, "Please log in as a student to apply for college admission.")
        login_url = reverse('login')
        next_param = urllib.parse.quote(request.get_full_path())
        return redirect(f"{login_url}?role=student&next={next_param}")

    user_profile = getattr(request.user, 'profile', None)
    if user_profile and user_profile.role == 'university':
        messages.warning(
            request,
            "You are logged in as an official University Administrator. Student admission applications are reserved for student accounts. Redirected to your University Portal."
        )
        return redirect('university_dashboard')
    elif user_profile and user_profile.role == 'accommodation':
        messages.warning(
            request,
            "You are logged in as an Accommodation Provider. Student admission applications are reserved for student accounts. Redirected to your Housing Portal."
        )
        return redirect('accommodation_dashboard')
    elif user_profile and user_profile.role != 'student' and not (request.user.is_staff or request.user.is_superuser):
        messages.warning(request, "Please sign in with a student account to apply for college admission.")
        login_url = reverse('login')
        next_param = urllib.parse.quote(request.get_full_path())
        return redirect(f"{login_url}?role=student&next={next_param}")

    selected_college_id = request.GET.get('college')
    selected_course_id = request.GET.get('course')
    target_college = None
    initial_data = {}
    if selected_college_id:
        try:
            target_college = College.objects.get(id=selected_college_id)
            if not target_college.is_registered:
                messages.warning(
                    request,
                    f"This particular college ({target_college.name}) is not registered here, so application to apply is not available."
                )
                return redirect('college_detail', slug=target_college.slug)
            if not target_college.is_admission_open:
                messages.warning(
                    request,
                    f"Admissions are currently closed for {target_college.name}."
                )
                return redirect('college_detail', slug=target_college.slug)
            initial_data['college'] = selected_college_id
        except College.DoesNotExist:
            pass
    if selected_course_id:
        initial_data['course'] = selected_course_id

    # Pre-populate student information from user account
    initial_data['first_name'] = request.user.first_name
    initial_data['last_name'] = request.user.last_name
    full_name = f"{request.user.first_name} {request.user.last_name}".strip()
    if not full_name:
        full_name = request.user.username
    initial_data['full_name'] = full_name
    if request.user.email:
        initial_data['email'] = request.user.email
    if hasattr(request.user, 'profile') and request.user.profile.phone:
        initial_data['phone'] = request.user.profile.phone

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save()

            # Record in user session for Applied button / Application Tracker
            my_reg_ids = request.session.get('my_registration_ids', [])
            reg_id_str = str(registration.registration_id)
            if reg_id_str not in my_reg_ids:
                my_reg_ids.append(reg_id_str)
                request.session['my_registration_ids'] = my_reg_ids
                request.session.modified = True

            # Render email template
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
            except Exception as e:
                # Log email failure but don't break user flow
                messages.warning(request, "Registration successful, but there was an issue sending confirmation email.")

            return redirect('registration_success', registration_id=str(registration.registration_id))
    else:
        form = StudentRegistrationForm(initial=initial_data)

    context = {
        'form': form,
        'target_college': target_college,
    }
    return render(request, 'core/registration_form.html', context)


def registration_success_view(request, registration_id):
    registration = get_object_or_404(
        StudentRegistration.objects.select_related('college', 'course'),
        registration_id=registration_id
    )
    context = {
        'registration': registration,
    }
    return render(request, 'core/registration_success.html', context)


def my_applications_view(request):
    """
    Dedicated view for users to track their submitted college applications and status.
    Displays applied colleges, allotment status (Pending/Confirmed/Cancelled),
    permanent tracking ID, and direct links to slip and nearby PGs.
    """
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'university':
        messages.info(request, "Redirected to your University Admissions Applications Registry.")
        return redirect('university_applications')

    search_query = request.GET.get('q', '').strip()
    session_reg_ids = request.session.get('my_registration_ids', [])

    queryset = StudentRegistration.objects.select_related('college__university', 'course').all()

    if search_query:
        # Search by tracking UUID, email, phone, applicant name, or college name
        try:
            val_uuid = uuid.UUID(search_query)
            queryset = queryset.filter(registration_id=val_uuid)
        except ValueError:
            queryset = queryset.filter(
                Q(email__iexact=search_query) |
                Q(phone__icontains=search_query) |
                Q(full_name__icontains=search_query) |
                Q(college__name__icontains=search_query)
            )
    else:
        # Match for current user email or session-stored registrations
        q_filter = Q()
        if request.user.is_authenticated and request.user.email:
            q_filter |= Q(email__iexact=request.user.email)
        if session_reg_ids:
            q_filter |= Q(registration_id__in=session_reg_ids)

        if q_filter:
            queryset = queryset.filter(q_filter)
        else:
            # If no logged in email and no session registration, default to empty list
            queryset = StudentRegistration.objects.none()

    context = {
        'applications': queryset,
        'search_query': search_query,
    }
    return render(request, 'core/my_applications.html', context)


def user_login_view(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile and profile.role == 'university':
            return redirect('university_dashboard')
        elif profile and profile.role == 'accommodation':
            return redirect('accommodation_dashboard')
        elif request.user.is_staff or request.user.is_superuser:
            return redirect('admin_moderation')
        return redirect('home')

    # Forward direct visits to role=admin to the dedicated admin login URL
    if request.method == 'GET' and request.GET.get('role') == 'admin':
        admin_login_url = reverse('admin_login')
        next_param = request.GET.get('next')
        if next_param:
            admin_login_url += f"?next={urllib.parse.quote(next_param)}"
        return redirect(admin_login_url)

    selected_role = request.POST.get('portal_role') or request.GET.get('role', 'student')
    if selected_role not in ['student', 'university', 'accommodation', 'admin']:
        selected_role = 'student'

    if request.method == 'POST':
        post_data = request.POST.copy()
        raw_username = post_data.get('username', '').strip()
        # Support logging in with email address directly, prioritizing account matching selected portal role
        user_by_email = (
            User.objects.filter(email__iexact=raw_username, profile__role=selected_role).first() or
            User.objects.filter(email__iexact=raw_username).first()
        )
        if user_by_email:
            post_data['username'] = user_by_email.username

        form = UserLoginForm(request, data=post_data, portal_role=selected_role)
        if form.is_valid():
            user = form.get_user()

            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'student'}
            )

            # Strict role-to-portal check:
            # 1. Administrator Portal (Direct POST compatibility)
            if selected_role == 'admin':
                if not (user.is_staff or user.is_superuser):
                    messages.error(
                        request,
                        "Access Denied: You do not have administrator credentials to sign in through the Admin Portal."
                    )
                    return render(request, 'account/login.html', {'form': form, 'selected_role': selected_role, 'hide_navbar_search': True})
                login(request, user)
                messages.success(request, f"Welcome back, Administrator {user.first_name or user.username}!")
                next_url = request.GET.get('next') or request.POST.get('next')
                return redirect(next_url or 'admin_moderation')

            # 2. Student Portal: Block admin/staff and partner accounts
            elif selected_role == 'student':
                if user.is_staff or user.is_superuser:
                    messages.error(
                        request,
                        "Access Denied: This login portal is for Students only. Administrator accounts cannot sign in through the public Student portal."
                    )
                    return render(request, 'account/login.html', {'form': form, 'selected_role': selected_role, 'hide_navbar_search': True})
                elif profile.role != 'student':
                    role_label = profile.get_role_display() or profile.role.title()
                    messages.error(
                        request,
                        f"Access Denied: This login portal is for Students only. {role_label} accounts cannot sign in through the Student portal. Please switch to the '{role_label}' tab above."
                    )
                    return render(request, 'account/login.html', {'form': form, 'selected_role': selected_role, 'hide_navbar_search': True})

            # 3. University Partner Portal
            elif selected_role == 'university':
                if user.is_staff or user.is_superuser:
                    messages.error(
                        request,
                        "Access Denied: This login portal is for University Partners only. Administrator accounts cannot sign in through the public University portal."
                    )
                    return render(request, 'account/login.html', {'form': form, 'selected_role': selected_role, 'hide_navbar_search': True})
                elif profile.role != 'university':
                    messages.error(
                        request,
                        "Access Denied: This login portal is for University Partners only. Students and other users cannot sign in through the University portal. Please switch to the 'Student' tab above."
                    )
                    return render(request, 'account/login.html', {'form': form, 'selected_role': selected_role, 'hide_navbar_search': True})

            # 4. Accommodation Partner Portal
            elif selected_role == 'accommodation':
                if user.is_staff or user.is_superuser:
                    messages.error(
                        request,
                        "Access Denied: This login portal is for Accommodation Providers only. Administrator accounts cannot sign in through the public Housing portal."
                    )
                    return render(request, 'account/login.html', {'form': form, 'selected_role': selected_role, 'hide_navbar_search': True})
                elif profile.role != 'accommodation':
                    messages.error(
                        request,
                        "Access Denied: This login portal is for Accommodation Providers only. Please switch to the appropriate portal tab above."
                    )
                    return render(request, 'account/login.html', {'form': form, 'selected_role': selected_role, 'hide_navbar_search': True})

            # Credentials and role matched -> complete login
            login(request, user)

            # Role-specific strict redirection and tailored notification
            if profile.role == 'university':
                display_name = profile.organization_name or user.get_full_name() or user.username
                messages.success(request, f"Logged in to University Partner Portal ({display_name}).")
                return redirect('university_dashboard')
            elif profile.role == 'accommodation':
                display_name = profile.organization_name or user.get_full_name() or user.username
                messages.success(request, f"Logged in to Housing Partner Portal ({display_name}).")
                return redirect('accommodation_dashboard')
            else:
                display_name = user.first_name or user.username
                messages.success(request, f"Welcome back, {display_name}!")

            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url and not any(p in next_url for p in ['/partner/', '/admin-portal/']):
                return redirect(next_url)
            return redirect('home')
    else:
        form = UserLoginForm(portal_role=selected_role)

    context = {
        'form': form,
        'selected_role': selected_role,
        'hide_navbar_search': True,
    }
    return render(request, 'account/login.html', context)


def admin_login_view(request):
    """
    Dedicated, separate login portal for platform administrators and moderation staff only.
    Not exposed on the public student/partner login portal tabs.
    """
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_moderation')
        return redirect('home')

    if request.method == 'POST':
        post_data = request.POST.copy()
        raw_username = post_data.get('username', '').strip()
        user_by_email = User.objects.filter(email__iexact=raw_username).first()
        if user_by_email:
            post_data['username'] = user_by_email.username

        form = UserLoginForm(request, data=post_data, portal_role='admin')
        if form.is_valid():
            user = form.get_user()
            if not (user.is_staff or user.is_superuser):
                messages.error(
                    request,
                    "Access Denied: You do not have administrator credentials to access the Platform Admin Portal."
                )
                return render(request, 'account/admin_login.html', {'form': form, 'hide_navbar_search': True})

            login(request, user)
            messages.success(request, f"Welcome back, Administrator {user.first_name or user.username}!")
            next_url = request.GET.get('next') or request.POST.get('next')
            return redirect(next_url or 'admin_moderation')
    else:
        form = UserLoginForm(portal_role='admin')

    context = {
        'form': form,
        'hide_navbar_search': True,
    }
    return render(request, 'account/admin_login.html', context)


def user_logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')


def send_registration_otp(request):
    """
    Generates and dispatches a temporary 6-digit verification OTP to the student's email.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}
    else:
        data = request.POST

    email = data.get('email', '').strip().lower()
    username = data.get('username', '').strip()

    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError

    if not email or '@' not in email:
        return JsonResponse({'success': False, 'message': 'Please enter a valid email address.'}, status=400)

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'success': False, 'message': 'Please enter a correct and valid email address.'}, status=400)

    # Check if email is already taken
    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse({
            'success': False,
            'message': 'An account with this email address already exists. Please sign in or use another email.'
        }, status=400)

    # Check if username is already taken
    if username and User.objects.filter(username__iexact=username).exists():
        return JsonResponse({
            'success': False,
            'message': f"The username '{username}' is already taken. Please choose another username."
        }, status=400)

    # Generate 6-digit random numeric OTP
    otp_code = f"{secrets.randbelow(900000) + 100000:06d}"
    expires_at = timezone.now() + datetime.timedelta(minutes=10)

    # Deactivate or delete old unverified OTPs for this email
    EmailVerificationOTP.objects.filter(email__iexact=email, is_verified=False).delete()
    EmailVerificationOTP.objects.create(
        email=email,
        otp_code=otp_code,
        expires_at=expires_at,
        is_verified=False
    )

    # Store in session as helper
    request.session['student_reg_otp'] = {
        'email': email,
        'code': otp_code,
        'expires_at': expires_at.isoformat(),
        'verified': False
    }

    # Dispatch email
    display_name = username or "Student"
    subject = f"Your CollegeClue Student Verification Code: {otp_code}"
    message = (
        f"Hello {display_name},\n\n"
        f"Thank you for registering on CollegeClue!\n\n"
        f"Your 6-digit email verification code is:\n\n"
        f"   >>> {otp_code} <<<\n\n"
        f"This temporary verification code will expire in 10 minutes.\n\n"
        f"Please enter this OTP to verify your email address and activate your account creation.\n\n"
        f"If you did not request this verification, please ignore this email.\n\n"
        f"Warm regards,\n"
        f"CollegeClue Admissions Team\n"
        f"https://collegeclue.local"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
    except Exception as e:
        err_msg = str(e)
        if 'Username and Password not accepted' in err_msg or 'SMTPAuthenticationError' in type(e).__name__:
            return JsonResponse({
                'success': False,
                'message': 'Gmail SMTP authentication failed. Please ensure your 16-character Google App Password in .env is correct.'
            }, status=500)
        return JsonResponse({'success': False, 'message': 'Could not deliver OTP to this email address. Please enter a correct email.'}, status=400)

    response_data = {
        'success': True,
        'message': f"A 6-digit OTP code has been sent to '{email}'. Please check your inbox and spam folder.",
    }
    return JsonResponse(response_data)


def verify_registration_otp(request):
    """
    Verifies the submitted 6-digit OTP code for a student's email address.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}
    else:
        data = request.POST

    email = data.get('email', '').strip().lower()
    otp_code = data.get('otp', '').strip()

    if not email or not otp_code:
        return JsonResponse({'success': False, 'message': 'Both email address and OTP code are required.'}, status=400)

    record = EmailVerificationOTP.objects.filter(
        email__iexact=email,
        otp_code=otp_code,
        is_verified=False
    ).order_by('-id').first()

    if not record:
        return JsonResponse({
            'success': False,
            'message': 'Invalid verification code. Please check the code in your email or request a new one.'
        }, status=400)

    if record.expires_at < timezone.now():
        return JsonResponse({
            'success': False,
            'message': 'This verification code has expired. Please click "Resend OTP" to generate a fresh code.'
        }, status=400)

    record.is_verified = True
    record.save()

    request.session['verified_student_email'] = email

    return JsonResponse({
        'success': True,
        'message': 'Email verified successfully! You can now proceed to create your Student account.'
    })


def user_register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    selected_role = request.GET.get('role', 'student')

    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)

        # For student role: strictly enforce OTP verification
        if selected_role == 'student':
            email_submitted = request.POST.get('email', '').strip().lower()
            is_otp_verified = (
                request.session.get('verified_student_email') == email_submitted or
                EmailVerificationOTP.objects.filter(
                    email__iexact=email_submitted,
                    is_verified=True,
                    expires_at__gte=timezone.now() - datetime.timedelta(hours=2)
                ).exists()
            )

            if not is_otp_verified:
                form.add_error('email', "Email verification required. Please click 'Send OTP' and verify the 6-digit code before creating your account.")
                messages.error(request, "Please verify your email address with the OTP code before creating your account.")
                context = {
                    'form': form,
                    'selected_role': selected_role,
                    'approved_colleges': College.objects.filter(status='Approved').select_related('university').order_by('name'),
                    'hide_navbar_search': True,
                }
                return render(request, 'account/register.html', context)

        if form.is_valid():
            user = form.save()
            profile = UserProfile.objects.get(user=user)

            # For student accounts: redirect directly to student login portal
            if profile.role == 'student':
                request.session.pop('verified_student_email', None)
                request.session.pop('student_reg_otp', None)
                messages.success(
                    request,
                    "Student account created and email verified successfully! Please sign in with your credentials."
                )
                return redirect(reverse('login') + '?role=student')

            # For partner accounts (university / accommodation)
            login(request, user)
            messages.success(request, f"Account created successfully as {profile.get_role_display()}!")
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)

            if profile.role == 'university':
                return redirect('university_dashboard')
            elif profile.role == 'accommodation':
                return redirect('accommodation_dashboard')
            return redirect('home')
    else:
        form = CustomUserRegistrationForm(initial={'role': selected_role})

    context = {
        'form': form,
        'selected_role': selected_role,
        'approved_colleges': College.objects.filter(status='Approved').select_related('university').order_by('name'),
        'hide_navbar_search': True,
    }
    return render(request, 'account/register.html', context)


# ==============================================================================
# ROLE ACCESS GUARDS & DECORATORS
# ==============================================================================

def university_partner_required(view_func):
    """
    Ensures user is logged in as a University / College Partner, authorized team member, or Admin.
    Redirects non-partners to homepage with an error message.
    """
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        profile = getattr(request.user, 'profile', None)
        if profile and profile.role == 'university':
            return view_func(request, *args, **kwargs)
        if request.user.email and CollegeTeamMember.objects.filter(email__iexact=request.user.email).exists():
            return view_func(request, *args, **kwargs)
        messages.error(request, "Access restricted to verified University Partners.")
        return redirect('home')
    return _wrapped_view


def get_user_administered_colleges(user):
    """
    Returns QuerySet of colleges the user administers (as primary creator/admin or authorized team member).
    Platform admins and superusers have access to all colleges.
    """
    if user.is_staff or user.is_superuser:
        return College.objects.select_related('university').prefetch_related('courses', 'team_members').all().order_by('-id')
    return College.objects.filter(
        Q(submitted_by=user) |
        Q(admin_email__iexact=user.email) |
        Q(team_members__user=user) |
        Q(team_members__email__iexact=user.email)
    ).distinct().select_related('university').prefetch_related('courses', 'team_members').order_by('-id')


def accommodation_partner_required(view_func):
    """
    Ensures user is logged in as an Accommodation Provider / PG Owner or Admin.
    Redirects non-partners to homepage with an error message.
    """
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        profile = getattr(request.user, 'profile', None)
        if profile and profile.role == 'accommodation':
            return view_func(request, *args, **kwargs)
        messages.error(request, "Access restricted to verified Accommodation Providers.")
        return redirect('home')
    return _wrapped_view


# ==============================================================================
# UNIVERSITY / COLLEGE PARTNER PORTAL
# ==============================================================================

@university_partner_required
def university_dashboard_view(request):
    """
    Dashboard for University and College Partners.
    Lists their administered college, verification status, pending student applications, and team access.
    Each university partner admin manages 1 university campus institution.
    """
    administered_colleges = get_user_administered_colleges(request.user)
    if not (request.user.is_staff or request.user.is_superuser):
        first_college_id = administered_colleges.values_list('id', flat=True).first()
        if first_college_id:
            administered_colleges = College.objects.filter(id=first_college_id).select_related('university').prefetch_related('courses', 'team_members')
        else:
            administered_colleges = College.objects.none()

    college_ids = list(administered_colleges.values_list('id', flat=True))

    pending_apps_count = StudentRegistration.objects.filter(
        college_id__in=college_ids,
        status='Pending'
    ).count()

    total_apps_count = StudentRegistration.objects.filter(
        college_id__in=college_ids
    ).count()

    stats = {
        'total': administered_colleges.count(),
        'pending': administered_colleges.filter(status='Pending').count(),
        'approved': administered_colleges.filter(status='Approved').count(),
        'rejected': administered_colleges.filter(status='Rejected').count(),
        'pending_applications': pending_apps_count,
        'total_applications': total_apps_count,
    }
    administered_universities = University.objects.filter(colleges__in=administered_colleges).distinct()
    if not (request.user.is_staff or request.user.is_superuser):
        first_uni_id = administered_universities.values_list('id', flat=True).first()
        if first_uni_id:
            administered_universities = University.objects.filter(id=first_uni_id)
        else:
            administered_universities = University.objects.none()

    context = {
        'submitted_colleges': administered_colleges,
        'administered_universities': administered_universities,
        'stats': stats,
    }
    return render(request, 'partner/university_dashboard.html', context)


@university_partner_required
def college_submit_view(request):
    """
    Submission form for University Partners to submit new colleges & courses for admin review.
    Each university partner admin is restricted to creating/managing only 1 university / college.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        existing_colleges = get_user_administered_colleges(request.user)
        if existing_colleges.exists():
            messages.warning(
                request,
                "Policy Notice: Each University Administrator is permitted to create and manage only 1 university / college campus. You already administer an active campus."
            )
            return redirect('university_dashboard')

    if request.method == 'POST':
        form = CollegeSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            college = form.save(commit=False)
            
            # Handle new university if specified
            new_uni_name = form.cleaned_data.get('new_university_name', '').strip()
            if new_uni_name and not college.university_id:
                uni, _ = University.objects.get_or_create(
                    name=new_uni_name,
                    defaults={
                        'city': form.cleaned_data.get('new_university_city') or college.city,
                        'state': form.cleaned_data.get('new_university_state') or 'India',
                        'description': f"Higher education university institution located in {college.city}.",
                        'established_year': 2000,
                        'rating': Decimal('4.0'),
                    }
                )
                college.university = uni

            college.submitted_by = request.user
            college.status = 'Pending'
            college.save()

            # Create Primary Course
            Course.objects.create(
                college=college,
                name=form.cleaned_data['course_1_name'],
                duration_years=form.cleaned_data['course_1_duration'],
                fee=form.cleaned_data['course_1_fee'],
                seats=form.cleaned_data['course_1_seats'],
                course_url=form.cleaned_data.get('course_1_url') or None
            )

            # Create Secondary Course if provided
            if form.cleaned_data.get('course_2_name'):
                Course.objects.create(
                    college=college,
                    name=form.cleaned_data['course_2_name'],
                    duration_years=form.cleaned_data['course_2_duration'] or 2,
                    fee=form.cleaned_data['course_2_fee'] or 100000,
                    seats=form.cleaned_data['course_2_seats'] or 60,
                    course_url=form.cleaned_data.get('course_2_url') or None
                )

            # Sync gmap_location to university if university location not set
            if college.gmap_location and college.university and not college.university.gmap_location:
                college.university.gmap_location = college.gmap_location
                college.university.save(update_fields=['gmap_location'])

            messages.success(
                request,
                f"College '{college.name}' submitted successfully! It has been forwarded to the Admin Moderation Queue for review."
            )
            return redirect('university_dashboard')
    else:
        form = CollegeSubmissionForm()

    context = {
        'form': form,
    }
    return render(request, 'partner/college_submit.html', context)


@university_partner_required
def college_edit_view(request, college_id):
    """
    Self-service editing dashboard for approved colleges.
    Allows university partners to update fees, facilities, descriptions, location, and campus details directly.
    """
    college = get_object_or_404(College.objects.prefetch_related('courses', 'university'), id=college_id)
    
    # Ownership, team, or staff check
    if not college.is_admin_or_team(request.user):
        messages.error(request, "You are not authorized to modify this college.")
        return redirect('university_dashboard')

    if request.method == 'POST':
        form = CollegeEditForm(request.POST, request.FILES, instance=college)
        if form.is_valid():
            col = form.save()
            if col.gmap_location and col.university and (not col.university.gmap_location or request.POST.get('sync_to_university')):
                col.university.gmap_location = col.gmap_location
                col.university.save(update_fields=['gmap_location'])
            messages.success(request, f"Campus details for '{college.name}' updated successfully!")
            return redirect('college_edit', college_id=college.id)
    else:
        form = CollegeEditForm(instance=college)

    context = {
        'college': college,
        'form': form,
        'courses': college.courses.all(),
        'active_tab': 'details',
    }
    return render(request, 'partner/college_edit.html', context)


@university_partner_required
def college_courses_view(request, college_id):
    """
    Dedicated view for university partners to manage academic courses under an approved college.
    Separated from campus details, supporting dynamic '+ course' bulk additions.
    """
    college = get_object_or_404(College.objects.prefetch_related('courses', 'university'), id=college_id)
    if not college.is_admin_or_team(request.user):
        messages.error(request, "You are not authorized to modify courses for this college.")
        return redirect('university_dashboard')

    if request.method == 'POST':
        # Accept dynamic multi-row submissions or standard single form
        names = request.POST.getlist('course_name[]') or request.POST.getlist('name[]') or request.POST.getlist('name')
        durations = request.POST.getlist('course_duration[]') or request.POST.getlist('duration_years[]') or request.POST.getlist('duration_years')
        fees = request.POST.getlist('course_fee[]') or request.POST.getlist('fee[]') or request.POST.getlist('fee')
        seats_list = request.POST.getlist('course_seats[]') or request.POST.getlist('seats[]') or request.POST.getlist('seats')
        urls = request.POST.getlist('course_url[]') or request.POST.getlist('course_url')

        added_count = 0
        for i, raw_name in enumerate(names):
            name = (raw_name or '').strip()
            if not name:
                continue

            try:
                duration_val = int(durations[i]) if i < len(durations) and durations[i] else 3
            except (ValueError, TypeError):
                duration_val = 3

            try:
                raw_fee_str = str(fees[i]).replace(',', '').strip() if i < len(fees) and fees[i] else '0.00'
                fee_val = Decimal(raw_fee_str)
            except Exception:
                fee_val = Decimal('0.00')

            try:
                seats_val = int(seats_list[i]) if i < len(seats_list) and seats_list[i] else 60
            except (ValueError, TypeError):
                seats_val = 60

            url_val = urls[i].strip() if i < len(urls) and urls[i] and urls[i].strip() else None

            Course.objects.update_or_create(
                college=college,
                name=name,
                defaults={
                    'duration_years': duration_val,
                    'fee': fee_val,
                    'seats': seats_val,
                    'course_url': url_val,
                }
            )
            added_count += 1

        if added_count > 0:
            messages.success(request, f"Successfully saved {added_count} academic course(s) for {college.name}!")
        else:
            messages.warning(request, "No course names were provided. Please enter at least one course.")

        return redirect('college_courses', college_id=college.id)

    courses = college.courses.all()
    course_form = CourseForm()
    context = {
        'college': college,
        'courses': courses,
        'course_form': course_form,
        'active_tab': 'courses',
    }
    return render(request, 'partner/college_courses.html', context)


@university_partner_required
def university_location_update_view(request, university_id):
    """
    Allows university portal admins to manually set or update the Google Maps location of an affiliated university.
    """
    administered_colleges = get_user_administered_colleges(request.user)
    university = get_object_or_404(University, id=university_id)
    if not (request.user.is_staff or request.user.is_superuser or administered_colleges.filter(university=university).exists()):
        messages.error(request, "Permission denied to update this university's location.")
        return redirect('university_dashboard')

    if request.method == 'POST':
        form = UniversityLocationForm(request.POST, instance=university)
        if form.is_valid():
            form.save()
            messages.success(request, f"Google Maps location for '{university.name}' updated successfully!")
        else:
            messages.error(request, "Invalid location details provided.")
    return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('university_dashboard'))


@university_partner_required
def college_admission_toggle_view(request, college_id):
    """
    1-click admission toggle for university partners to switch admissions ON or OFF.
    """
    college = get_object_or_404(College, id=college_id)
    if not college.is_admin_or_team(request.user):
        messages.error(request, "Permission denied to update admission status for this campus.")
        return redirect('university_dashboard')

    if request.method == 'POST':
        # Check current status: if Open and not expired, turn OFF. Otherwise turn ON.
        if college.admissions_status == 'Open' and (not college.admission_close_date or college.admission_close_date >= datetime.date.today()):
            college.admissions_status = 'Closed'
            messages.warning(request, f"Admissions for '{college.name}' are now turned OFF (Closed). Student applications are paused.")
        else:
            college.admissions_status = 'Open'
            # If closed date was in past or not set, set a generous open deadline
            if not college.admission_close_date or college.admission_close_date < datetime.date.today():
                college.admission_close_date = datetime.date.today() + datetime.timedelta(days=90)
            messages.success(request, f"Admissions for '{college.name}' are now turned ON (Open)! Students can submit applications.")
        college.save(update_fields=['admissions_status', 'admission_close_date'])

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('university_dashboard')
    return redirect(next_url)


@university_partner_required
def college_admission_dates_update_view(request, college_id):
    """
    Allows university portal admins to quickly update the admissions schedule (status, open date, close date/opened till)
    for their campus directly from the dashboard modal or edit page.
    """
    college = get_object_or_404(College, id=college_id)
    if not college.is_admin_or_team(request.user):
        messages.error(request, "Permission denied to update admission dates for this campus.")
        return redirect('university_dashboard')

    if request.method == 'POST':
        form = CollegeAdmissionDatesForm(request.POST, instance=college)
        if form.is_valid():
            form.save()
            status_label = college.admission_dates_display
            messages.success(request, f"Admissions schedule for '{college.name}' updated successfully! ({status_label})")
        else:
            messages.error(request, "Could not update admission dates. Please check the values provided.")

    return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('university_dashboard'))


@university_partner_required
def course_add_view(request, college_id):
    """
    Adds a new academic course directly under an approved college.
    """
    college = get_object_or_404(College, id=college_id)
    if not college.is_admin_or_team(request.user):
        messages.error(request, "Permission denied.")
        return redirect('university_dashboard')

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.college = college
            course.save()
            messages.success(request, f"Course '{course.name}' added successfully to {college.name}!")
        else:
            messages.error(request, "Could not add course. Please check all required fields.")

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('college_courses', kwargs={'college_id': college.id})
    return redirect(next_url)


@university_partner_required
def course_delete_view(request, college_id, course_id):
    """
    Removes a course from a college.
    """
    college = get_object_or_404(College, id=college_id)
    if not college.is_admin_or_team(request.user):
        messages.error(request, "Permission denied.")
        return redirect('university_dashboard')

    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id, college=college)
        course_name = course.name
        course.delete()
        messages.info(request, f"Course '{course_name}' has been deleted from campus offerings.")

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('college_courses', kwargs={'college_id': college.id})
    return redirect(next_url)


@university_partner_required
def course_edit_view(request, college_id, course_id):
    """
    Edits an existing course offering for an authorized university partner campus.
    """
    college = get_object_or_404(College, id=college_id)
    if not college.is_admin_or_team(request.user):
        messages.error(request, "Permission denied.")
        return redirect('university_dashboard')

    course = get_object_or_404(Course, id=course_id, college=college)

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            updated_course = form.save()
            messages.success(request, f"Course '{updated_course.name}' updated successfully!")
        else:
            errors = ", ".join([f"{f}: {e[0]}" for f, e in form.errors.items()])
            messages.error(request, f"Could not update course: {errors}")

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('college_courses', kwargs={'college_id': college.id})
    return redirect(next_url)


# ==============================================================================
# UNIVERSITY ADMISSION APPLICATIONS & TEAM MANAGEMENT
# ==============================================================================

@university_partner_required
def university_applications_view(request):
    """
    Dedicated view for university admin holders and their authorized team to review
    student admission applications for their colleges.
    """
    colleges = get_user_administered_colleges(request.user)
    college_ids = colleges.values_list('id', flat=True)

    applications = StudentRegistration.objects.filter(
        college_id__in=college_ids
    ).select_related('college__university', 'course', 'reviewed_by').order_by('-created_at')

    # Status filter
    status_filter = request.GET.get('status', '').strip()
    if status_filter in ['Pending', 'Confirmed', 'Cancelled']:
        applications = applications.filter(status=status_filter)

    # College filter
    selected_college_id = request.GET.get('college', '').strip()
    if selected_college_id:
        try:
            applications = applications.filter(college_id=int(selected_college_id))
        except ValueError:
            pass

    # Available courses for administered campuses
    courses_qs = Course.objects.filter(college_id__in=college_ids)
    if selected_college_id and selected_college_id.isdigit():
        courses_qs = courses_qs.filter(college_id=int(selected_college_id))
    available_courses = list(courses_qs.select_related('college').order_by('name'))

    # Course filter
    selected_course_id = request.GET.get('course', '').strip()
    selected_course = None
    if selected_course_id:
        try:
            course_id_int = int(selected_course_id)
            applications = applications.filter(course_id=course_id_int)
            selected_course = next((c for c in available_courses if c.id == course_id_int), None)
        except ValueError:
            pass

    # Search filter (name, email, phone, UUID)
    search_q = request.GET.get('q', '').strip()
    if search_q:
        try:
            val_uuid = uuid.UUID(search_q)
            applications = applications.filter(registration_id=val_uuid)
        except ValueError:
            applications = applications.filter(
                Q(full_name__icontains=search_q) |
                Q(email__icontains=search_q) |
                Q(phone__icontains=search_q) |
                Q(course__name__icontains=search_q)
            )

    all_apps = StudentRegistration.objects.filter(college_id__in=college_ids)
    if selected_college_id and selected_college_id.isdigit():
        all_apps = all_apps.filter(college_id=int(selected_college_id))
    if selected_course_id and selected_course_id.isdigit():
        all_apps = all_apps.filter(course_id=int(selected_course_id))

    stats = {
        'total': all_apps.count(),
        'pending': all_apps.filter(status='Pending').count(),
        'confirmed': all_apps.filter(status='Confirmed').count(),
        'cancelled': all_apps.filter(status='Cancelled').count(),
    }

    context = {
        'applications': applications,
        'colleges': colleges,
        'available_courses': available_courses,
        'selected_course': selected_course,
        'stats': stats,
        'status_filter': status_filter,
        'selected_college_id': int(selected_college_id) if selected_college_id and selected_college_id.isdigit() else None,
        'selected_course_id': int(selected_course_id) if selected_course_id and selected_course_id.isdigit() else None,
        'search_q': search_q,
    }
    return render(request, 'partner/university_applications.html', context)


@university_partner_required
def university_application_approve_view(request, registration_id):
    """
    Allows university admin holder / staff to approve an applicant.
    Sets status to Confirmed and sends official email confirmation to student.
    """
    if request.method != 'POST':
        return redirect('university_applications')

    registration = get_object_or_404(
        StudentRegistration.objects.select_related('college', 'course'),
        registration_id=registration_id
    )

    if not registration.college.is_admin_or_team(request.user):
        messages.error(request, "You are not authorized to approve applications for this institution.")
        return redirect('university_applications')

    notes = request.POST.get('admin_notes', '').strip()
    registration.status = 'Confirmed'
    registration.reviewed_by = request.user
    registration.reviewed_at = timezone.now()
    if notes:
        registration.admin_notes = notes
    registration.save()

    # Send confirmation email to student
    try:
        email_context = {
            'student_name': registration.full_name,
            'college_name': registration.college.name,
            'course_name': registration.course.name,
            'registration_id': str(registration.registration_id),
            'admin_notes': registration.admin_notes,
            'status': 'Confirmed',
        }
        body = render_to_string('core/emails/application_approved.txt', email_context)
        send_mail(
            subject=f"Admission Approved! Application {registration.registration_id} - {registration.college.name}",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registration.email],
            fail_silently=True,
        )
    except Exception as e:
        pass

    messages.success(
        request,
        f"Application for '{registration.full_name}' has been APPROVED and marked as Confirmed! Updated available seats for {registration.course.name}: {registration.course.available_seats} remaining."
    )
    next_url = request.POST.get('next') or reverse('university_applications')
    return redirect(next_url)


@university_partner_required
def university_application_reject_view(request, registration_id):
    """
    Allows university admin holder / staff to reject/cancel an applicant.
    Sets status to Cancelled and records cancellation notes.
    """
    if request.method != 'POST':
        return redirect('university_applications')

    registration = get_object_or_404(
        StudentRegistration.objects.select_related('college', 'course'),
        registration_id=registration_id
    )

    if not registration.college.is_admin_or_team(request.user):
        messages.error(request, "You are not authorized to review applications for this institution.")
        return redirect('university_applications')

    notes = request.POST.get('admin_notes', '').strip()
    registration.status = 'Cancelled'
    registration.reviewed_by = request.user
    registration.reviewed_at = timezone.now()
    if notes:
        registration.admin_notes = notes
    registration.save()

    # Send update email to student
    try:
        email_context = {
            'student_name': registration.full_name,
            'college_name': registration.college.name,
            'course_name': registration.course.name,
            'registration_id': str(registration.registration_id),
            'admin_notes': registration.admin_notes,
            'status': 'Cancelled',
        }
        body = render_to_string('core/emails/application_rejected.txt', email_context)
        send_mail(
            subject=f"Admission Update - Application {registration.registration_id} - {registration.college.name}",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registration.email],
            fail_silently=True,
        )
    except Exception as e:
        pass

    messages.info(
        request,
        f"Application for '{registration.full_name}' has been marked as Cancelled."
    )
    next_url = request.POST.get('next') or reverse('university_applications')
    return redirect(next_url)


@university_partner_required
def university_application_status_update_view(request, registration_id):
    """
    Allows university admin holders and authorized admissions team to update an applicant's
    status at any time: Confirmed (Approved), Cancelled (Rejected), or Pending (Under Re-evaluation),
    with custom admissions notes and automatic student email notification.
    """
    if request.method != 'POST':
        return redirect('university_applications')

    registration = get_object_or_404(
        StudentRegistration.objects.select_related('college', 'course'),
        registration_id=registration_id
    )

    if not registration.college.is_admin_or_team(request.user):
        messages.error(request, "You are not authorized to update applications for this institution.")
        return redirect('university_applications')

    new_status = request.POST.get('status', '').strip()
    if new_status not in ['Confirmed', 'Cancelled', 'Pending']:
        messages.error(request, "Invalid status choice selected.")
        return redirect('university_applications')

    notes = request.POST.get('admin_notes', '').strip()
    registration.status = new_status
    registration.reviewed_by = request.user
    registration.reviewed_at = timezone.now()
    if notes:
        registration.admin_notes = notes
    registration.save()

    # Send status email to student
    try:
        email_context = {
            'student_name': registration.full_name,
            'college_name': registration.college.name,
            'course_name': registration.course.name,
            'registration_id': str(registration.registration_id),
            'admin_notes': registration.admin_notes,
            'status': new_status,
        }
        if new_status == 'Confirmed':
            subject = f"Admission Approved! Application {registration.registration_id} - {registration.college.name}"
            template_name = 'core/emails/application_approved.txt'
        elif new_status == 'Cancelled':
            subject = f"Admission Update - Application {registration.registration_id} - {registration.college.name}"
            template_name = 'core/emails/application_rejected.txt'
        else:
            subject = f"Application Under Re-evaluation - Application {registration.registration_id} - {registration.college.name}"
            template_name = 'core/emails/application_under_review.txt'

        body = render_to_string(template_name, email_context)
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registration.email],
            fail_silently=True,
        )
    except Exception:
        pass

    if new_status == 'Confirmed':
        messages.success(request, f"Application for '{registration.full_name}' has been APPROVED and marked as Confirmed!")
    elif new_status == 'Cancelled':
        messages.warning(request, f"Application for '{registration.full_name}' has been REJECTED and marked as Cancelled.")
    else:
        messages.info(request, f"Application for '{registration.full_name}' has been reset to PENDING for re-evaluation.")

    next_url = request.POST.get('next') or reverse('university_applications')
    return redirect(next_url)


@university_partner_required
def college_team_management_view(request, college_id):
    """
    Allows the primary admin holder of a college to configure their team access:
    - Update official college admin email (e.g. xyz@svr.edu.in)
    - Set allowed team accounts limit (e.g. 1 solo admin, 2, 4, 6, 8, 10)
    - Add authorized staff emails (up to the limit)
    - Remove authorized staff emails
    """
    college = get_object_or_404(College.objects.select_related('university'), id=college_id)

    # Only primary creator/admin or staff can manage the team
    if not (request.user.is_staff or request.user.is_superuser) and college.submitted_by != request.user:
        messages.error(request, "Only the Primary Administrator of this college can manage staff team access.")
        return redirect('university_dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_settings':
            admin_email = request.POST.get('admin_email', '').strip()
            max_members = request.POST.get('max_team_members', '1').strip()
            try:
                max_members_val = max(1, min(20, int(max_members)))
                college.max_team_members = max_members_val
                if admin_email:
                    college.admin_email = admin_email
                college.save()
                messages.success(request, f"College admin settings updated! Maximum team members allowed: {college.max_team_members}.")
            except ValueError:
                messages.error(request, "Invalid number for team member capacity.")

        elif action == 'add_member':
            current_count = college.team_members.count()
            if current_count >= college.max_team_members:
                messages.error(request, f"Team member capacity limit ({college.max_team_members}) reached. Please increase allowed capacity in settings first.")
                return redirect('college_team', college_id=college.id)

            staff_username = request.POST.get('staff_username', '').strip()
            staff_email = request.POST.get('staff_email', '').strip().lower()
            staff_password = request.POST.get('staff_password', '').strip()

            from django.contrib.auth.models import User

            # 1. Email handling
            if staff_email and '@' not in staff_email:
                staff_email = f"{staff_email}@{college.email_domain}"

            if not staff_email or '@' not in staff_email:
                messages.error(request, "Please enter a valid staff email address.")
                return redirect('college_team', college_id=college.id)

            if college.team_members.filter(email__iexact=staff_email).exists():
                messages.warning(request, f"An account with email '{staff_email}' is already an authorized team member for this college.")
                return redirect('college_team', college_id=college.id)

            # 2. Require or generate unique username
            if not staff_username:
                base_username = staff_email.split('@')[0].replace('.', '_').replace('-', '_')
                staff_username = base_username
                counter = 1
                while User.objects.filter(username__iexact=staff_username).exists():
                    staff_username = f"{base_username}_{counter}"
                    counter += 1
            elif User.objects.filter(username__iexact=staff_username).exists():
                messages.error(
                    request,
                    f"The username '{staff_username}' is already taken. Each username must be unique. Please choose another username."
                )
                return redirect('college_team', college_id=college.id)

            # 3. Determine password
            password_to_set = staff_password if staff_password else "PartnerPassword123!"

            # 4. Create or link User account
            existing_user = User.objects.filter(email__iexact=staff_email).first()
            if existing_user:
                new_user = existing_user
                profile, _ = UserProfile.objects.get_or_create(user=new_user)
                profile.role = 'university'
                profile.organization_name = college.name
                profile.save()
            else:
                new_user = User.objects.create_user(
                    username=staff_username,
                    email=staff_email,
                    password=password_to_set
                )
                new_user.first_name = staff_username.replace('_', ' ').replace('.', ' ').title()
                new_user.save()

                profile, _ = UserProfile.objects.get_or_create(user=new_user)
                profile.role = 'university'
                profile.organization_name = college.name
                profile.save()

            # 5. Link to college team
            CollegeTeamMember.objects.create(
                college=college,
                email=staff_email,
                user=new_user,
                added_by=request.user
            )

            messages.success(
                request,
                f"Administrator account successfully created and saved! Username: '{staff_username}' (Password: '{password_to_set}'). "
                f"The other user can now log in using this username to access the exact same college database and dashboard."
            )

        elif action == 'remove_member':
            member_id = request.POST.get('member_id')
            member = get_object_or_404(CollegeTeamMember, id=member_id, college=college)
            removed_email = member.email
            removed_user = member.user
            removed_username = removed_user.username if removed_user else ""
            member.delete()
            if removed_user and removed_user != college.submitted_by and not (removed_user.is_staff or removed_user.is_superuser):
                removed_user.delete()
            messages.info(request, f"Access revoked and account '{removed_username or removed_email}' removed.")

        return redirect('college_team', college_id=college.id)

    team_members = college.team_members.select_related('user').all()
    context = {
        'college': college,
        'team_members': team_members,
        'current_count': team_members.count(),
        'seats_remaining': max(0, college.max_team_members - team_members.count()),
    }
    return render(request, 'partner/college_team.html', context)


# ==============================================================================
# ACCOMMODATION PROVIDER / PG OWNER PARTNER PORTAL
# ==============================================================================

@accommodation_partner_required
def accommodation_dashboard_view(request):
    """
    Dashboard for Accommodation Providers / PG Owners.
    Lists their submitted student hostels and PGs, verification status, and direct link to submit new listings.
    """
    submitted_accommodations = Accommodation.objects.filter(submitted_by=request.user).select_related('college').order_by('-id')
    stats = {
        'total': submitted_accommodations.count(),
        'pending': submitted_accommodations.filter(status='Pending').count(),
        'approved': submitted_accommodations.filter(status='Approved').count(),
        'rejected': submitted_accommodations.filter(status='Rejected').count(),
    }
    context = {
        'submitted_accommodations': submitted_accommodations,
        'stats': stats,
    }
    return render(request, 'partner/accommodation_dashboard.html', context)


@accommodation_partner_required
def accommodation_submit_view(request):
    """
    Submission form for Accommodation Providers to list a new student PG or hostel for admin review.
    """
    if request.method == 'POST':
        form = AccommodationSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            acc = form.save(commit=False)
            acc.submitted_by = request.user
            acc.status = 'Pending'
            acc.save()

            messages.success(
                request,
                f"Accommodation '{acc.name}' submitted successfully! It has been forwarded to the Admin Moderation Queue for verification."
            )
            return redirect('accommodation_dashboard')
    else:
        form = AccommodationSubmissionForm()

    context = {
        'form': form,
    }
    return render(request, 'partner/accommodation_submit.html', context)


@accommodation_partner_required
def accommodation_edit_view(request, acc_id):
    """
    Self-service editing dashboard for approved PGs/Hostels.
    Allows accommodation providers to update photos, monthly rent, facilities, and manage vacancy availability.
    """
    acc = get_object_or_404(Accommodation.objects.select_related('college'), id=acc_id)
    if not (request.user.is_staff or request.user.is_superuser) and acc.submitted_by != request.user:
        messages.error(request, "You are not authorized to modify this property.")
        return redirect('accommodation_dashboard')

    if request.method == 'POST':
        form = AccommodationEditForm(request.POST, request.FILES, instance=acc)
        if form.is_valid():
            form.save()
            messages.success(request, f"Property '{acc.name}' updated successfully in the live database!")
            return redirect('accommodation_edit', acc_id=acc.id)
    else:
        form = AccommodationEditForm(instance=acc)

    context = {
        'accommodation': acc,
        'form': form,
    }
    return render(request, 'partner/accommodation_edit.html', context)


@accommodation_partner_required
def accommodation_toggle_vacancy_view(request, acc_id):
    """
    1-click vacancy toggle for accommodation owners to switch between Available (Vacant) and Full (No Vacancy).
    """
    acc = get_object_or_404(Accommodation, id=acc_id)
    if not (request.user.is_staff or request.user.is_superuser) and acc.submitted_by != request.user:
        messages.error(request, "Permission denied.")
        return redirect('accommodation_dashboard')

    if request.method == 'POST':
        acc.is_available = not acc.is_available
        acc.save()
        status_text = "Vacant & Available for Students" if acc.is_available else "Full / No Vacancy"
        messages.success(request, f"Vacancy status for '{acc.name}' updated to: {status_text}.")

    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('accommodation_dashboard')
    return redirect(next_url)


# ==============================================================================
# REAL ADMIN APPROVAL / MODERATION CENTER
# ==============================================================================

@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_moderation_view(request):
    """
    Real Admin Approval & Moderation Dashboard.
    Enables the super admin to review incoming college and accommodation submissions,
    and Accept / Approve or Reject with a single click.
    """
    pending_colleges = College.objects.filter(status='Pending').select_related('university', 'submitted_by').prefetch_related('courses').order_by('-id')
    pending_accommodations = Accommodation.objects.filter(status='Pending').select_related('college', 'submitted_by').order_by('-id')
    
    reviewed_colleges = College.objects.filter(status__in=['Approved', 'Rejected']).exclude(submitted_by=None).select_related('university', 'submitted_by').order_by('-id')[:6]
    reviewed_accommodations = Accommodation.objects.filter(status__in=['Approved', 'Rejected']).exclude(submitted_by=None).select_related('college', 'submitted_by').order_by('-id')[:6]

    context = {
        'pending_colleges': pending_colleges,
        'pending_accommodations': pending_accommodations,
        'reviewed_colleges': reviewed_colleges,
        'reviewed_accommodations': reviewed_accommodations,
        'total_pending': pending_colleges.count() + pending_accommodations.count(),
    }
    return render(request, 'admin_portal/moderation_dashboard.html', context)


@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_approve_college_view(request, college_id):
    if request.method == 'POST':
        college = get_object_or_404(College, id=college_id)
        college.status = 'Approved'
        college.admin_notes = request.POST.get('admin_notes', 'Approved by Admin')
        college.save()
        messages.success(request, f"College '{college.name}' has been APPROVED and is now live in the database!")
    return redirect('admin_moderation')


@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_reject_college_view(request, college_id):
    if request.method == 'POST':
        college = get_object_or_404(College, id=college_id)
        college.status = 'Rejected'
        college.admin_notes = request.POST.get('admin_notes', 'Rejected by Admin')
        college.save()
        messages.warning(request, f"College '{college.name}' has been REJECTED.")
    return redirect('admin_moderation')


@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_reset_college_view(request, college_id):
    if request.method == 'POST':
        college = get_object_or_404(College, id=college_id)
        college.status = 'Pending'
        college.admin_notes = request.POST.get('admin_notes', 'Reset to Pending for re-moderation')
        college.save()
        messages.info(request, f"College '{college.name}' has been reset to PENDING for re-moderation.")
    return redirect('admin_moderation')


@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_approve_acc_view(request, acc_id):
    if request.method == 'POST':
        acc = get_object_or_404(Accommodation, id=acc_id)
        acc.status = 'Approved'
        acc.admin_notes = request.POST.get('admin_notes', 'Approved by Admin')
        acc.save()
        messages.success(request, f"Accommodation '{acc.name}' has been APPROVED and is now live for students!")
    return redirect('admin_moderation')


@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_reject_acc_view(request, acc_id):
    if request.method == 'POST':
        acc = get_object_or_404(Accommodation, id=acc_id)
        acc.status = 'Rejected'
        acc.admin_notes = request.POST.get('admin_notes', 'Rejected by Admin')
        acc.save()
        messages.warning(request, f"Accommodation '{acc.name}' has been REJECTED.")
    return redirect('admin_moderation')


# ==============================================================================
# LIVE AUTO-SUGGEST SEARCH API
# ==============================================================================

def api_search_suggest(request):
    """
    JSON auto-suggest endpoint returning live suggestions for Universities,
    Approved Colleges, and Academic Courses as the user types.
    """
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 1:
        return JsonResponse({'query': '', 'results': {'universities': [], 'colleges': [], 'courses': []}})

    # 1. Matching Universities
    universities = University.objects.filter(
        Q(name__icontains=query) | Q(city__icontains=query)
    ).order_by('-rating')[:4]

    # 2. Matching Approved Colleges
    colleges = College.objects.filter(status='Approved').filter(
        Q(name__icontains=query) | Q(city__icontains=query) | Q(university__name__icontains=query)
    ).select_related('university').order_by('-rating')[:5]

    # 3. Matching Academic Courses
    courses = Course.objects.filter(
        college__status='Approved',
        name__icontains=query
    ).values('name').distinct()[:3]

    results = {
        'universities': [
            {
                'id': u.id,
                'name': u.name,
                'city': u.city,
                'state': u.state,
                'rating': str(u.rating),
                'url': reverse('university_detail', kwargs={'slug': u.slug}),
                'logo_url': u.logo.url if u.logo else None,
            }
            for u in universities
        ],
        'colleges': [
            {
                'id': c.id,
                'name': c.name,
                'university': c.university.name,
                'city': c.city,
                'fees': str(c.fees),
                'rating': str(c.rating),
                'url': reverse('college_detail', kwargs={'slug': c.slug}),
                'is_registered': c.is_registered,
                'logo_url': c.logo.url if c.logo else None,
            }
            for c in colleges
        ],
        'courses': [
            {
                'name': cr['name'],
                'url': f"{reverse('college_list')}?course_name={cr['name']}",
            }
            for cr in courses
        ],
    }

    return JsonResponse({'query': query, 'results': results})


def about_view(request):
    """
    Dedicated About CollegeClue presentation view highlighting the platform's
    mission, direct-to-college admissions engine, verified housing network,
    and key institutional metrics.
    """
    total_colleges = College.objects.filter(status='Approved').count()
    registered_colleges = College.objects.filter(status='Approved').filter(
        Q(admin_email__gt='') | Q(submitted_by__isnull=False)
    ).count()
    total_accommodations = Accommodation.objects.filter(status='Approved').count()
    total_universities = University.objects.count()

    context = {
        'total_colleges': total_colleges,
        'registered_colleges': registered_colleges,
        'total_accommodations': total_accommodations,
        'total_universities': total_universities,
    }
    return render(request, 'core/about.html', context)



