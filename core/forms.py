from decimal import Decimal
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import University, College, Course, Accommodation, StudentRegistration, UserProfile


class UniversityFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search university name or keywords...'
        })
    )
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City (e.g. New Delhi)'
        })
    )
    state = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'State'
        })
    )
    min_rating = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'placeholder': 'Min Rating (e.g. 4.0)'
        })
    )
    established_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Established after year'
        })
    )


class CollegeFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'College name or facility...'
        })
    )
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    course_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Course (e.g. B.Tech, MBA)'
        })
    )
    max_fee = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max Annual Fee (₹)'
        })
    )


class AccommodationFilterForm(forms.Form):
    college = forms.ModelChoiceField(
        queryset=College.objects.filter(status='Approved').order_by('name'),
        required=False,
        empty_label='All Nearby Colleges',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_filter_college'})
    )
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + Accommodation.TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_filter_type'})
    )
    room_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Room Types')] + Accommodation.ROOM_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_filter_room_type'})
    )
    min_rent = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min Monthly Rent (₹)',
            'id': 'id_filter_min_rent'
        })
    )
    max_rent = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max Monthly Rent (₹)',
            'id': 'id_filter_max_rent'
        })
    )


class StudentRegistrationForm(forms.ModelForm):
    college = forms.ModelChoiceField(
        queryset=College.objects.all(),
        empty_label="-- Select College --",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_college'})
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        empty_label="-- Select Course (choose college first) --",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_course'})
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name', 'id': 'id_first_name'})
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name', 'id': 'id_last_name'})
    )
    full_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full legal name (auto-filled)', 'id': 'id_full_name'})
    )
    father_or_guardian_name = forms.CharField(
        required=True,
        label="Father / Guardian Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Father or Guardian's full name", 'id': 'id_father_or_guardian_name'})
    )
    date_of_birth = forms.DateField(
        required=False,
        label="Date of Birth",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'id_date_of_birth'})
    )
    gender = forms.ChoiceField(
        choices=StudentRegistration.GENDER_CHOICES,
        initial='Male',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_gender'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Permanent / residential street address', 'id': 'id_address'})
    )
    class_10_school = forms.CharField(
        required=True,
        label="Class X (10th) School / Board",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. St. Xavier High School / CBSE Board', 'id': 'id_class_10_school'})
    )
    class_10_percentage = forms.DecimalField(
        required=True,
        min_value=0,
        max_value=100,
        label="Class X (10th) Percentage (%)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 75.50', 'id': 'id_class_10_percentage'})
    )
    class_12_school = forms.CharField(
        required=True,
        label="Class XII (12th / +2) School / Board",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Delhi Public School / CBSE Board', 'id': 'id_class_12_school'})
    )
    class_12_percentage = forms.DecimalField(
        required=True,
        min_value=0,
        max_value=100,
        label="Class XII (12th / +2) Percentage (%)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 80.00', 'id': 'id_class_12_percentage'})
    )

    class Meta:
        model = StudentRegistration
        fields = [
            'college', 'course',
            'first_name', 'last_name', 'full_name',
            'email', 'phone', 'father_or_guardian_name',
            'date_of_birth', 'gender', 'address',
            'class_10_school', 'class_10_percentage',
            'class_12_school', 'class_12_percentage'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@example.com', 'id': 'id_email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile number', 'id': 'id_phone'}),
        }
        error_messages = {
            'first_name': {
                'required': 'First name is required.'
            },
            'last_name': {
                'required': 'Last name is required.'
            },
            'email': {
                'required': 'A valid contact email is required for registration updates.',
                'invalid': 'Please enter a valid email address.'
            },
            'phone': {
                'required': 'Mobile phone number is mandatory for SMS notifications.'
            },
            'father_or_guardian_name': {
                'required': "Father or Guardian's name is required."
            },
            'class_10_school': {
                'required': 'Class X school or board name is required.'
            },
            'class_10_percentage': {
                'required': 'Class X percentage is required to verify admission eligibility.'
            },
            'class_12_school': {
                'required': 'Class XII school or board name is required.'
            },
            'class_12_percentage': {
                'required': 'Class XII percentage is required to verify admission eligibility.'
            },
            'college': {
                'required': 'Please choose a target college from the list.'
            },
            'course': {
                'required': 'Please select the academic course you wish to enroll in.'
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['college'].queryset = College.objects.filter(status='Approved', admissions_status='Open')
        if 'college' in self.data:
            try:
                college_id = int(self.data.get('college'))
                self.fields['course'].queryset = Course.objects.filter(college_id=college_id).order_by('name')
            except (ValueError, TypeError):
                self.fields['course'].queryset = Course.objects.none()
        elif self.instance.pk and self.instance.college:
            self.fields['course'].queryset = self.instance.college.courses.order_by('name')
        elif 'initial' in kwargs and 'college' in kwargs['initial']:
            college_id = kwargs['initial']['college']
            self.fields['course'].queryset = Course.objects.filter(college_id=college_id).order_by('name')

    def clean_college(self):
        college = self.cleaned_data.get('college')
        if college and not college.is_admission_open:
            raise forms.ValidationError(
                f"Admissions are currently closed for {college.name}."
            )
        return college

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        cleaned_digits = ''.join(c for c in phone if c.isdigit())
        if len(cleaned_digits) < 10:
            raise forms.ValidationError("Phone number must contain at least 10 digits.")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email, profile__role='university').exists() or College.objects.filter(admin_email__iexact=email).exists():
            raise forms.ValidationError(
                "This email address belongs to a registered University Administrator. Student admission applications must use a personal student email."
            )
        return email

    def clean(self):
        cleaned_data = super().clean()
        first_name = (cleaned_data.get('first_name') or '').strip()
        last_name = (cleaned_data.get('last_name') or '').strip()
        full_name = (cleaned_data.get('full_name') or '').strip()

        if not full_name and (first_name or last_name):
            full_name = f"{first_name} {last_name}".strip()
            cleaned_data['full_name'] = full_name
        elif full_name and not first_name:
            parts = full_name.split(' ', 1)
            cleaned_data['first_name'] = parts[0]
            cleaned_data['last_name'] = parts[1] if len(parts) > 1 else ''

        college = cleaned_data.get('college')
        course = cleaned_data.get('course')
        if college and course:
            if course.college_id != college.id:
                raise forms.ValidationError({
                    'course': "The selected course is not offered by the chosen college."
                })

        # Academic Eligibility Verification
        c10_pct = cleaned_data.get('class_10_percentage')
        c12_pct = cleaned_data.get('class_12_percentage')

        if college:
            min_10 = college.min_10th_percentage
            min_12 = college.min_12th_percentage

            if c10_pct is not None and min_10 is not None:
                if c10_pct < min_10:
                    self.add_error(
                        'class_10_percentage',
                        f"Eligibility criteria not met: {college.name} requires a minimum of {min_10}% in Class X (10th). You entered {c10_pct}%."
                    )

            if c12_pct is not None and min_12 is not None:
                if c12_pct < min_12:
                    self.add_error(
                        'class_12_percentage',
                        f"Eligibility criteria not met: {college.name} requires a minimum of {min_12}% in Class XII (12th / +2). You entered {c12_pct}%."
                    )

        return cleaned_data


class CustomUserRegistrationForm(UserCreationForm):
    ROLE_CHOICES = [
        ('student', 'Student (Explore & Apply for Admissions)'),
        ('university', 'University / College Partner (List Colleges & Courses)'),
        ('accommodation', 'Accommodation Provider / PG Owner (List Student Housing)'),
    ]
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial='student',
        widget=forms.Select(attrs={'class': 'form-select fw-semibold'})
    )
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name (optional)'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name (optional)'}))
    organization_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'University / College or PG Property Name (if partner)'})
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile number (10 digits)'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists. Only one unique account per email is allowed."
            )
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if not user.first_name:
            user.first_name = user.username.title()
            if commit:
                user.save(update_fields=['first_name'])
        if commit:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data.get('role', 'student')
            profile.organization_name = self.cleaned_data.get('organization_name', '')
            profile.phone = self.cleaned_data.get('phone', '')
            profile.save()
        return user


class CollegeSubmissionForm(forms.ModelForm):
    new_university_name = forms.CharField(
        required=False,
        label="Or Create New University",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'If university is not in dropdown, enter name here'})
    )
    new_university_city = forms.CharField(
        required=False,
        label="New University City",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Bengaluru, New Delhi'})
    )
    new_university_state = forms.CharField(
        required=False,
        label="New University State",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Karnataka, Delhi'})
    )

    # Initial course fields to make submission comprehensive in one go
    course_1_name = forms.CharField(required=True, label="Primary Course Name", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. B.Tech Computer Science & Engineering'}))
    course_1_duration = forms.IntegerField(initial=4, label="Duration (Years)", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    course_1_fee = forms.DecimalField(initial=150000, label="Annual Course Fee (₹)", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    course_1_seats = forms.IntegerField(initial=60, label="Intake Seats", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    course_1_url = forms.URLField(required=False, label="Primary Course Link / Syllabus (Optional)", widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://university.edu/syllabus/course-1 (Optional)'}))

    course_2_name = forms.CharField(required=False, label="Secondary Course Name (Optional)", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MBA / Master of Business Administration'}))
    course_2_duration = forms.IntegerField(required=False, initial=2, label="Duration (Years)", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    course_2_fee = forms.DecimalField(required=False, initial=200000, label="Annual Course Fee (₹)", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    course_2_seats = forms.IntegerField(required=False, initial=60, label="Intake Seats", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    course_2_url = forms.URLField(required=False, label="Secondary Course Link / Syllabus (Optional)", widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://university.edu/syllabus/course-2 (Optional)'}))

    min_10th_percentage = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=100,
        initial=50.00,
        label="Minimum Class X (10th) % Required",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 50.00'})
    )
    min_12th_percentage = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=100,
        initial=50.00,
        label="Minimum Class XII (12th) % Required",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 50.00'})
    )

    class Meta:
        model = College
        fields = [
            'university', 'name', 'city', 'fees', 'min_10th_percentage', 'min_12th_percentage',
            'admissions_status', 'admission_open_date', 'admission_close_date',
            'rating', 'facilities', 'description', 'gmap_location',
            'highest_package', 'average_package', 'median_package', 'placement_rate',
            'total_offers', 'summer_stipend', 'top_recruiters', 'placement_highlights'
        ]
        widgets = {
            'university': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Faculty of Technology / School of Business'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Bengaluru'}),
            'fees': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Annual base tuition in ₹'}),
            'admissions_status': forms.Select(attrs={'class': 'form-select'}),
            'admission_open_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'admission_close_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'e.g. 4.5'}),
            'facilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Modern laboratories, library, Wi-Fi campus, sports center...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed background, NAAC/NIRF accreditation, and student placements...'}),
            'gmap_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Google Maps share link, embed code, or coordinates (e.g. 28.5450, 77.1926)'}),
            'highest_package': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ₹44.00 LPA'}),
            'average_package': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ₹14.80 LPA'}),
            'median_package': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ₹12.50 LPA'}),
            'placement_rate': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 96.4%'}),
            'total_offers': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 820+'}),
            'summer_stipend': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ₹80,000 / mo'}),
            'top_recruiters': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Google, Microsoft, Amazon, Adobe, Deloitte, Goldman Sachs...'}),
            'placement_highlights': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Placement cell & pre-placement training highlights (one per line)...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['university'].required = False
        self.fields['university'].empty_label = "-- Select Affiliated University (or enter new below) --"
        if 'min_10th_percentage' in self.fields:
            self.fields['min_10th_percentage'].required = False
            self.fields['min_10th_percentage'].initial = 50.00
        if 'min_12th_percentage' in self.fields:
            self.fields['min_12th_percentage'].required = False
            self.fields['min_12th_percentage'].initial = 50.00
        if 'admissions_status' in self.fields:
            self.fields['admissions_status'].required = False
            self.fields['admissions_status'].initial = 'Open'
        if 'admission_close_date' in self.fields:
            self.fields['admission_close_date'].required = False
        if 'admission_open_date' in self.fields:
            self.fields['admission_open_date'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('min_10th_percentage'):
            cleaned_data['min_10th_percentage'] = 50.00
        if not cleaned_data.get('min_12th_percentage'):
            cleaned_data['min_12th_percentage'] = 50.00
        if not cleaned_data.get('admissions_status'):
            cleaned_data['admissions_status'] = 'Open'
        uni = cleaned_data.get('university')
        new_uni = cleaned_data.get('new_university_name', '').strip()
        if not uni and not new_uni:
            raise forms.ValidationError("Please select an existing university or enter a new university name.")
        return cleaned_data


class AccommodationSubmissionForm(forms.ModelForm):
    class Meta:
        model = Accommodation
        fields = [
            'name', 'type', 'college', 'city', 'address', 'rent', 'room_type',
            'gender', 'food_included', 'security_deposit', 'notice_period', 'gate_closing_time',
            'facilities', 'contact_phone', 'contact_email'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Royal Student PG / St. Mary Hostel'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'college': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Bengaluru'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Street address, landmark, proximity to campus'}),
            'rent': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monthly rent in ₹'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'food_included': forms.Select(attrs={'class': 'form-select'}),
            'security_deposit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Security deposit in ₹ (e.g. 5000)'}),
            'notice_period': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1 Month / 15 Days'}),
            'gate_closing_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 10:30 PM / No Curfew'}),
            'facilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Wi-Fi, 3 Homely Meals, AC, Power Backup, 24/7 Security, RO Water...'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Landlord / Manager mobile number'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contact@property.com'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['college'].required = False
        self.fields['college'].empty_label = "-- Select Nearest Campus (Optional) --"
        self.fields['college'].queryset = College.objects.filter(status='Approved')
        self.fields['contact_email'].required = True
        self.fields['facilities'].required = True
        self.fields['security_deposit'].required = False
        self.fields['notice_period'].required = False
        self.fields['gate_closing_time'].required = False
        self.fields['gender'].required = False
        self.fields['food_included'].required = False

    def clean_security_deposit(self):
        val = self.cleaned_data.get('security_deposit')
        return val if val is not None else Decimal('0.00')

    def clean_notice_period(self):
        val = (self.cleaned_data.get('notice_period') or '').strip()
        return val if val else '1 Month'

    def clean_gate_closing_time(self):
        val = (self.cleaned_data.get('gate_closing_time') or '').strip()
        return val if val else '10:30 PM'

    def clean_gender(self):
        val = (self.cleaned_data.get('gender') or '').strip()
        return val if val else 'Co-ed'

    def clean_food_included(self):
        val = (self.cleaned_data.get('food_included') or '').strip()
        return val if val else 'Included'


class CollegeEditForm(forms.ModelForm):
    """
    Self-service edit form for University Partners to update their approved college details.
    """
    min_10th_percentage = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=100,
        initial=50.00,
        label="Minimum Class X (10th) % Required",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 50.00'})
    )
    min_12th_percentage = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=100,
        initial=50.00,
        label="Minimum Class XII (12th) % Required",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 50.00'})
    )

    class Meta:
        model = College
        fields = [
            'name', 'city', 'fees', 'min_10th_percentage', 'min_12th_percentage',
            'admissions_status', 'admission_open_date', 'admission_close_date',
            'rating', 'facilities', 'description', 'logo', 'gmap_location',
            'highest_package', 'average_package', 'median_package', 'placement_rate',
            'total_offers', 'summer_stipend', 'top_recruiters', 'placement_highlights'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'College name', 'id': 'id_name'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City', 'id': 'id_city'}),
            'fees': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Base annual tuition in ₹', 'id': 'id_fees'}),
            'admissions_status': forms.Select(attrs={'class': 'form-select', 'id': 'id_admissions_status'}),
            'admission_open_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'id_admission_open_date'}),
            'admission_close_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'id_admission_close_date'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Rating (out of 5.0)', 'id': 'id_rating'}),
            'facilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Campus facilities'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'College overview, history, and academic focus'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'gmap_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Google Maps share link, embed code, or coordinates (e.g. 28.5450, 77.1926)'}),
            'highest_package': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ₹44.00 LPA', 'id': 'id_highest_package'}),
            'average_package': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ₹14.80 LPA', 'id': 'id_average_package'}),
            'median_package': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ₹12.50 LPA', 'id': 'id_median_package'}),
            'placement_rate': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 96.4%', 'id': 'id_placement_rate'}),
            'total_offers': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 820+', 'id': 'id_total_offers'}),
            'summer_stipend': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ₹80,000 / mo', 'id': 'id_summer_stipend'}),
            'top_recruiters': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Google, Microsoft, Amazon, Adobe, Deloitte, McKinsey, Goldman Sachs...', 'id': 'id_top_recruiters'}),
            'placement_highlights': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Placement & pre-placement training highlights (one per line)...', 'id': 'id_placement_highlights'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'min_10th_percentage' in self.fields:
            self.fields['min_10th_percentage'].required = False
            self.fields['min_10th_percentage'].initial = 50.00
        if 'min_12th_percentage' in self.fields:
            self.fields['min_12th_percentage'].required = False
            self.fields['min_12th_percentage'].initial = 50.00
        if 'admissions_status' in self.fields:
            self.fields['admissions_status'].required = False
        if 'admission_close_date' in self.fields:
            self.fields['admission_close_date'].required = False
        if 'admission_open_date' in self.fields:
            self.fields['admission_open_date'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('min_10th_percentage'):
            cleaned_data['min_10th_percentage'] = 50.00
        if not cleaned_data.get('min_12th_percentage'):
            cleaned_data['min_12th_percentage'] = 50.00
        if not cleaned_data.get('admissions_status'):
            cleaned_data['admissions_status'] = getattr(self.instance, 'admissions_status', 'Open') or 'Open'
        return cleaned_data


class CollegeAdmissionDatesForm(forms.ModelForm):
    """
    Dedicated quick-edit form for University Partners to update their campus admission dates and status.
    """
    class Meta:
        model = College
        fields = ['admissions_status', 'admission_open_date', 'admission_close_date']
        widgets = {
            'admissions_status': forms.Select(attrs={'class': 'form-select'}),
            'admission_open_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'admission_close_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class CourseForm(forms.ModelForm):
    """
    Form for University Partners to add or edit academic courses under their approved college.
    """
    course_url = forms.URLField(
        required=False,
        label="Course Link / Syllabus URL (Optional)",
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://university.edu/syllabus/course (Optional)'
        })
    )

    class Meta:
        model = Course
        fields = ['name', 'duration_years', 'fee', 'seats', 'course_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Name (e.g. B.Tech Data Science)'}),
            'duration_years': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duration in years'}),
            'fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Annual course fee in ₹'}),
            'seats': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Intake seats'}),
            'course_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://university.edu/syllabus/course (Optional)'}),
        }


class UniversityLocationForm(forms.ModelForm):
    """
    Quick self-service form for University Partners to update the university's Google Maps location.
    """
    class Meta:
        model = University
        fields = ['gmap_location']
        widgets = {
            'gmap_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Google Maps share URL, embed code, or coordinates (e.g. 28.5450, 77.1926)'
            })
        }


class AccommodationEditForm(forms.ModelForm):
    """
    Self-service edit form for Accommodation Providers to update their approved PG/hostel,
    photos, pricing, and required room/facility specifications.
    """
    class Meta:
        model = Accommodation
        fields = [
            'name', 'type', 'college', 'city', 'address', 'rent', 'room_type',
            'gender', 'food_included', 'security_deposit', 'notice_period', 'gate_closing_time',
            'facilities', 'image', 'contact_phone', 'contact_email'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PG / Hostel name'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'college': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Full address & landmark'}),
            'rent': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monthly rent in ₹'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'food_included': forms.Select(attrs={'class': 'form-select'}),
            'security_deposit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Security deposit in ₹ (e.g. 5000)'}),
            'notice_period': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1 Month / 15 Days'}),
            'gate_closing_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 10:30 PM / No Curfew'}),
            'facilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Amenities & facilities'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact phone'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Contact email'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['college'].required = False
        self.fields['college'].empty_label = "-- Select Nearest Campus (Optional) --"
        self.fields['college'].queryset = College.objects.filter(status='Approved')
        self.fields['contact_email'].required = True
        self.fields['facilities'].required = True
        self.fields['security_deposit'].required = False
        self.fields['notice_period'].required = False
        self.fields['gate_closing_time'].required = False
        self.fields['gender'].required = False
        self.fields['food_included'].required = False

    def clean_security_deposit(self):
        val = self.cleaned_data.get('security_deposit')
        return val if val is not None else Decimal('0.00')

    def clean_notice_period(self):
        val = (self.cleaned_data.get('notice_period') or '').strip()
        return val if val else '1 Month'

    def clean_gate_closing_time(self):
        val = (self.cleaned_data.get('gate_closing_time') or '').strip()
        return val if val else '10:30 PM'

    def clean_gender(self):
        val = (self.cleaned_data.get('gender') or '').strip()
        return val if val else 'Co-ed'

    def clean_food_included(self):
        val = (self.cleaned_data.get('food_included') or '').strip()
        return val if val else 'Included'


class UserLoginForm(AuthenticationForm):
    """
    Standardized, clean authentication form supporting browser saved credentials
    without forced dummy suggestions or autofill blockers.
    """
    username = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg rounded-3',
            'placeholder': 'Enter username or email',
            'autocomplete': 'username',
            'id': 'id_username',
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg rounded-3',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
            'id': 'id_password',
        })
    )

    def __init__(self, *args, **kwargs):
        portal_role = kwargs.pop('portal_role', 'student')
        super().__init__(*args, **kwargs)
        if portal_role == 'university':
            self.fields['username'].widget.attrs['placeholder'] = 'Enter university partner email or username'
        elif portal_role == 'accommodation':
            self.fields['username'].widget.attrs['placeholder'] = 'Enter housing provider email or username'
        elif portal_role == 'admin':
            self.fields['username'].widget.attrs['placeholder'] = 'Enter administrator username or email'
        else:
            self.fields['username'].widget.attrs['placeholder'] = 'Enter student username or email'



