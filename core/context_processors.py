from django.db.models import Q, Count, Min, Max
from .models import StudentRegistration, College, Course, Accommodation


def group_courses_by_headline(courses):
    headlines = [
        {
            'id': 'eng',
            'headline': 'Engineering & Technology',
            'icon': 'bi-gear-fill',
            'badge': 'Engineering',
            'keywords': ['tech', 'eng', 'b.e.', 'diploma', 'polytechnic', 'civil', 'mech', 'aero'],
            'courses': []
        },
        {
            'id': 'comm',
            'headline': 'Commerce & Management (B.Com, BBA, MBA)',
            'icon': 'bi-briefcase-fill',
            'badge': 'B.Com / MBA',
            'keywords': ['b.com', 'm.com', 'bba', 'mba', 'commerce', 'finance', 'account', 'banking'],
            'courses': []
        },
        {
            'id': 'sci',
            'headline': 'Sciences & Information Tech (BCA, B.Sc)',
            'icon': 'bi-cpu-fill',
            'badge': 'Science / IT',
            'keywords': ['bca', 'mca', 'b.sc', 'm.sc', 'data', 'ai', 'computer', 'science', 'cyber', 'software'],
            'courses': []
        },
        {
            'id': 'arts',
            'headline': 'Arts, Design & Law (BA, B.Des, LLB)',
            'icon': 'bi-palette-fill',
            'badge': 'Arts & Law',
            'keywords': ['ba', 'ma', 'llb', 'law', 'arts', 'design', 'b.des', 'journalism', 'media'],
            'courses': []
        },
        {
            'id': 'other',
            'headline': 'Other Specialized Programs',
            'icon': 'bi-journal-bookmark-fill',
            'badge': 'Specialized',
            'keywords': [],
            'courses': []
        }
    ]

    for c in courses:
        matched = False
        name_lower = c.name.lower()
        for h in headlines[:-1]:
            if any(k in name_lower for k in h['keywords']):
                h['courses'].append(c)
                matched = True
                break
        if not matched:
            headlines[-1]['courses'].append(c)

    return headlines


def user_applications(request):
    """
    Context processor providing:
    - applied_count: Count of submitted applications for the current student/session.
    - partner_pending_applications_count: Count of pending applications for the logged-in university partner's colleges.
    - filter_cities: Distinct cities for search & filter modal.
    - filter_courses: Distinct available courses for search & filter modal.
    - popular_course_tags: Quick course tag buttons for filter modal.
    - partner_colleges_data: For university partners, list of colleges with categorized department headlines.
    - partner_accommodations_data: For accommodation providers, list of their properties.
    """
    session_ids = request.session.get('my_registration_ids', [])
    count = len(session_ids)

    if hasattr(request, 'user') and request.user.is_authenticated and request.user.email:
        email_count = StudentRegistration.objects.filter(email__iexact=request.user.email).count()
        count = max(email_count, len(session_ids))

    partner_pending_count = 0
    partner_colleges_data = []
    partner_accommodations_data = []

    if hasattr(request, 'user') and request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        is_uni = (profile and profile.role == 'university') or request.user.is_staff or request.user.is_superuser
        is_acc = (profile and profile.role == 'accommodation') or request.user.is_staff or request.user.is_superuser

        if is_uni:
            if request.user.is_staff or request.user.is_superuser:
                partner_pending_count = StudentRegistration.objects.filter(status='Pending').count()
                admin_colleges = College.objects.filter(status='Approved').prefetch_related('courses')[:5]
            else:
                user_colleges = College.objects.filter(
                    Q(submitted_by=request.user) |
                    Q(admin_email__iexact=request.user.email) |
                    Q(team_members__user=request.user) |
                    Q(team_members__email__iexact=request.user.email)
                ).distinct()
                first_col = user_colleges.prefetch_related('courses').first()
                if first_col:
                    admin_colleges = [first_col]
                    partner_pending_count = StudentRegistration.objects.filter(
                        college=first_col,
                        status='Pending'
                    ).count()
                else:
                    admin_colleges = []
                    partner_pending_count = 0

            for col in admin_colleges:
                partner_colleges_data.append({
                    'college': col,
                    'courses': list(col.courses.all()),
                    'categorized_headlines': group_courses_by_headline(col.courses.all()),
                })

        if is_acc:
            if request.user.is_staff or request.user.is_superuser:
                partner_accommodations_data = list(Accommodation.objects.filter(status='Approved')[:5])
            else:
                partner_accommodations_data = list(Accommodation.objects.filter(submitted_by=request.user))

    # Search & Filter Modal global datasets
    filter_cities = list(
        College.objects.filter(status='Approved')
        .values_list('city', flat=True)
        .distinct()
        .order_by('city')
    )
    filter_courses = list(
        Course.objects.filter(college__status='Approved')
        .values_list('name', flat=True)
        .distinct()
        .order_by('name')[:35]
    )

    popular_course_tags = [
        'B.Tech Computer Science',
        'B.Com',
        'MBA',
        'MBBS',
        'BBA',
        'B.Sc Data Science',
        'BCA',
        'B.Des',
        'BA',
    ]

    return {
        'applied_count': count,
        'partner_pending_applications_count': partner_pending_count,
        'partner_colleges_data': partner_colleges_data,
        'partner_accommodations_data': partner_accommodations_data,
        'filter_cities': filter_cities,
        'filter_courses': filter_courses,
        'popular_course_tags': popular_course_tags,
    }

