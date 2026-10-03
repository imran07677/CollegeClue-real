import uuid
from django.db import models
from django.utils.text import slugify
from django.conf import settings


class University(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    description = models.TextField()
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    established_year = models.PositiveIntegerField()
    website = models.URLField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    gmap_location = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Google Maps Location",
        help_text="Google Maps share link, embed code, or coordinates (e.g. 28.5450, 77.1926)"
    )

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Universities'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while University.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class College(models.Model):
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='colleges'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    city = models.CharField(max_length=100)
    description = models.TextField()
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    facilities = models.TextField(blank=True, help_text="Comma-separated or narrative facilities")
    STATUS_CHOICES = [
        ('Pending', 'Pending Review'),
        ('Approved', 'Approved & Published'),
        ('Rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Approved')
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_colleges'
    )
    admin_notes = models.TextField(blank=True, help_text="Reason or notes from admin review")
    admin_email = models.EmailField(blank=True, help_text="Official admin contact email for this college (e.g. xyz@svr.edu.in)")
    max_team_members = models.PositiveIntegerField(default=1, help_text="Maximum authorized team admin emails allowed (e.g. 1, 4, 6)")
    min_10th_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50.00,
        help_text="Minimum Class X (10th) percentage required to apply"
    )
    min_12th_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50.00,
        help_text="Minimum Class XII (12th / +2) percentage required to apply"
    )
    gmap_location = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Google Maps Location",
        help_text="Google Maps share link, embed code, or coordinates (e.g. 28.5450, 77.1926)"
    )
    # Admissions Schedule & Availability
    admissions_status = models.CharField(
        max_length=20,
        choices=[
            ('Open', 'Open for Admissions'),
            ('Closed', 'Admissions Closed')
        ],
        default='Open',
        verbose_name="Admissions Status"
    )
    admission_open_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Admissions Open Date",
        help_text="Date when admission applications open"
    )
    admission_close_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Admissions Close Date (Opened Till)",
        help_text="Last date to apply for admission (e.g. 2026-12-31)"
    )
    # Institutional Placements & Visiting Recruiter Insights
    highest_package = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        verbose_name="Highest Package (CTC)",
        help_text="e.g. ₹44.00 LPA"
    )
    average_package = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        verbose_name="Average Package (CTC)",
        help_text="e.g. ₹14.80 LPA"
    )
    median_package = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        verbose_name="Median Package",
        help_text="e.g. ₹12.50 LPA"
    )
    placement_rate = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Placement Rate (%)",
        help_text="e.g. 96.4%"
    )
    total_offers = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Total Job Offers",
        help_text="e.g. 820+"
    )
    summer_stipend = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        verbose_name="Highest Summer Stipend",
        help_text="e.g. ₹80,000 / mo"
    )
    top_recruiters = models.TextField(
        blank=True,
        null=True,
        verbose_name="Top Recruiters",
        help_text="Comma-separated recruiter company names (e.g. Google, Microsoft, Amazon, Deloitte, Goldman Sachs)"
    )
    placement_highlights = models.TextField(
        blank=True,
        null=True,
        verbose_name="Placement Cell Highlights",
        help_text="Key placement and corporate relations highlights (one per line)"
    )

    class Meta:
        ordering = ['name']
        unique_together = ('university', 'name')

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while College.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def is_admin_or_team(self, user):
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        if self.submitted_by_id == user.id:
            return True
        if self.admin_email and user.email and self.admin_email.lower() == user.email.lower():
            return True
        return self.team_members.filter(models.Q(user=user) | models.Q(email__iexact=user.email)).exists()

    @property
    def is_registered(self):
        """Returns True if the college has a designated official admin email or registered partner."""
        return bool(self.admin_email or self.submitted_by_id)

    @property
    def email_domain(self):
        """
        Calculates the official institutional email domain according to this college, e.g.:
        - If admin_email is set (e.g. 'xyz@svr.edu.in') -> 'svr.edu.in'
        - If university has a website (e.g. 'https://dtu.ac.in') -> 'dtu.ac.in'
        - Or derived from college name acronym / slug -> e.g. 'asob.edu.in' or 'alliance.edu.in'
        """
        if self.admin_email and '@' in self.admin_email:
            return self.admin_email.split('@')[-1].lower().strip()
        if self.university and self.university.website:
            clean = self.university.website.replace('https://', '').replace('http://', '').strip('/').split('/')[0]
            if clean and '.' in clean:
                return clean.lower()
        words = [w for w in self.name.split() if w.lower() not in ('of', '&', 'and', 'the', 'for', 'in', 'at')]
        if len(words) >= 2:
            acronym = ''.join(w[0] for w in words).lower()
            if len(acronym) >= 3:
                return f"{acronym}.edu.in"
        slug_clean = self.slug.split('-')[0].lower() if self.slug else 'college'
        return f"{slug_clean}.edu.in"

    @property
    def is_admission_open(self):
        """
        Determines whether admission applications are currently open for this college.
        Returns False if admissions_status is 'Closed'.
        Returns False if today is before admission_open_date or after admission_close_date.
        Otherwise returns True.
        """
        if self.admissions_status == 'Closed':
            return False
        from django.utils import timezone
        today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
        if self.admission_open_date and today < self.admission_open_date:
            return False
        if self.admission_close_date and today > self.admission_close_date:
            return False
        return True

    @property
    def admission_dates_display(self):
        """
        Returns a friendly label for students describing current admission status and dates.
        """
        from django.utils import timezone
        today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()

        if self.admissions_status == 'Closed':
            return "Admissions Closed"

        if self.admission_open_date and today < self.admission_open_date:
            return f"Admissions Open on {self.admission_open_date.strftime('%d %b %Y')}"

        if self.admission_close_date and today > self.admission_close_date:
            return f"Admissions Closed ({self.admission_close_date.strftime('%d %b %Y')})"

        if self.admission_close_date:
            return f"Admissions Open Till {self.admission_close_date.strftime('%d %b %Y')}"
        elif self.admission_open_date:
            return f"Admissions Open (From {self.admission_open_date.strftime('%d %b %Y')})"
        return "Admissions Open"

    def __str__(self):
        return f"{self.name} ({self.university.name})"


class Course(models.Model):
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    name = models.CharField(max_length=255)
    duration_years = models.PositiveIntegerField(default=3)
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    seats = models.PositiveIntegerField(default=60)
    course_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Course Link / Syllabus URL",
        help_text="Optional external link or brochure URL for this course"
    )

    class Meta:
        ordering = ['name']
        unique_together = ('college', 'name')

    @property
    def confirmed_admissions_count(self):
        """Returns the number of student applications with status 'Confirmed' for this course."""
        return self.registrations.filter(status='Confirmed').count()

    @property
    def available_seats(self):
        """Calculates available seats: intake capacity minus confirmed approved student admissions."""
        return max(0, self.seats - self.confirmed_admissions_count)

    def __str__(self):
        return f"{self.name} - {self.college.name}"


class CollegeTeamMember(models.Model):
    """
    Authorized staff/administrator team members for a college.
    Enables the primary admin holder to grant staff email access (e.g. 1, 4, 6 accounts)
    to manage the college and process admission applications.
    """
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name='team_members'
    )
    email = models.EmailField(help_text="Authorized staff team email address (e.g. admissions@svr.edu.in)")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='college_memberships'
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='added_team_members'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('college', 'email')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} -> {self.college.name}"


class Accommodation(models.Model):
    TYPE_CHOICES = [
        ('PG', 'Paying Guest (PG)'),
        ('Flat', 'Flat / Apartment'),
        ('Hostel', 'Hostel'),
    ]

    ROOM_TYPE_CHOICES = [
        ('Single', 'Single Room'),
        ('Double', 'Double Sharing'),
        ('Triple', 'Triple Sharing'),
    ]

    GENDER_CHOICES = [
        ('Boys', 'Boys Only'),
        ('Girls', 'Girls Only'),
        ('Co-ed', 'Co-ed / Anyone'),
    ]

    FOOD_CHOICES = [
        ('Included', '3 Meals Included (Breakfast, Lunch & Dinner)'),
        ('Optional', 'Food Available (Optional)'),
        ('SelfCooking', 'Self Cooking / No Food Included'),
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    college = models.ForeignKey(
        College,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accommodations'
    )
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='Co-ed', verbose_name="Resident Category")
    food_included = models.CharField(max_length=20, choices=FOOD_CHOICES, default='Included', verbose_name="Food & Meals")
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Security Deposit (₹)")
    notice_period = models.CharField(max_length=50, default='1 Month', verbose_name="Notice Period")
    gate_closing_time = models.CharField(max_length=50, default='10:30 PM', verbose_name="Gate Closing Time")
    address = models.TextField()
    city = models.CharField(max_length=100)
    rent = models.DecimalField(max_digits=10, decimal_places=2)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    facilities = models.TextField(blank=True)
    image = models.ImageField(upload_to='accommodations/', blank=True, null=True)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    is_available = models.BooleanField(default=True)
    STATUS_CHOICES = [
        ('Pending', 'Pending Review'),
        ('Approved', 'Approved & Published'),
        ('Rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Approved')
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_accommodations'
    )
    admin_notes = models.TextField(blank=True, help_text="Reason or notes from admin review")

    class Meta:
        ordering = ['-is_available', 'rent']

    def __str__(self):
        return f"{self.name} ({self.type} - {self.city})"


class StudentRegistration(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]

    registration_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    first_name = models.CharField(max_length=120, blank=True)
    last_name = models.CharField(max_length=120, blank=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    father_or_guardian_name = models.CharField(max_length=255, blank=True, verbose_name="Father / Guardian Name")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Date of Birth")
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='Male', blank=True)
    address = models.TextField(blank=True, verbose_name="Residential Address")
    class_10_school = models.CharField(max_length=255, blank=True, verbose_name="Class X School / Board")
    class_10_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Class X Percentage (%)")
    class_12_school = models.CharField(max_length=255, blank=True, verbose_name="Class XII School / Board")
    class_12_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Class XII Percentage (%)")
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name='registrations'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='registrations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )
    admin_notes = models.TextField(
        blank=True,
        help_text="Review remarks or feedback from college admissions committee"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_registrations'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.registration_id} - {self.full_name}"


class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist'
    )
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'university')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} -> {self.university.name}"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('university', 'University / College Partner'),
        ('accommodation', 'Accommodation Provider / PG Owner'),
        ('admin', 'Administrator'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    organization_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class EmailVerificationOTP(models.Model):
    email = models.EmailField(db_index=True)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        from django.utils import timezone
        return not self.is_verified and timezone.now() <= self.expires_at

    def __str__(self):
        status = "Verified" if self.is_verified else "Pending"
        return f"OTP for {self.email} - {status}"

