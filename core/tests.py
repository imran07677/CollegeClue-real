import json
import datetime
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import (
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
from core.forms import (
    StudentRegistrationForm,
    CustomUserRegistrationForm,
    CourseForm,
    UniversityLocationForm,
)


class UniversityModelTest(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Delhi University Test",
            city="New Delhi",
            state="Delhi",
            description="Leading central university in India.",
            established_year=1922,
            website="https://du.ac.in",
            rating=Decimal("4.5")
        )

    def test_str_representation(self):
        self.assertEqual(str(self.university), "Delhi University Test")

    def test_slug_auto_generation(self):
        self.assertEqual(self.university.slug, "delhi-university-test")


class CollegeModelTest(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Mumbai University Test",
            city="Mumbai",
            state="Maharashtra",
            description="Historic coastal university.",
            established_year=1857,
            rating=Decimal("4.3")
        )
        self.college = College.objects.create(
            university=self.university,
            name="St. Xavier's College",
            city="Mumbai",
            description="Autonomous arts and science college.",
            fees=Decimal("85000.00"),
            rating=Decimal("4.7"),
            facilities="Library, Canteen, Auditorium, Science Labs"
        )

    def test_foreign_key_relationship(self):
        self.assertEqual(self.college.university, self.university)
        self.assertEqual(self.university.colleges.count(), 1)

    def test_fees_and_str(self):
        self.assertEqual(self.college.fees, Decimal("85000.00"))
        self.assertIn("St. Xavier's College", str(self.college))


class StudentRegistrationFormTest(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Anna University",
            city="Chennai",
            state="Tamil Nadu",
            established_year=1978,
            rating=Decimal("4.4")
        )
        self.college1 = College.objects.create(
            university=self.university,
            name="College of Engineering Guindy",
            city="Chennai",
            fees=Decimal("60000.00"),
            rating=Decimal("4.8"),
            admin_email="admin1@annauniv.edu"
        )
        self.college2 = College.objects.create(
            university=self.university,
            name="Alagappa College of Technology",
            city="Chennai",
            fees=Decimal("55000.00"),
            rating=Decimal("4.5"),
            admin_email="admin2@annauniv.edu"
        )
        self.course1 = Course.objects.create(
            college=self.college1,
            name="B.Tech Computer Science",
            duration_years=4,
            fee=Decimal("70000.00"),
            seats=120
        )
        self.course2 = Course.objects.create(
            college=self.college2,
            name="B.Tech Chemical Engineering",
            duration_years=4,
            fee=Decimal("65000.00"),
            seats=60
        )

    def test_valid_registration_form(self):
        form_data = {
            'college': self.college1.id,
            'course': self.course1.id,
            'first_name': 'Aarav',
            'last_name': 'Sharma',
            'full_name': 'Aarav Sharma',
            'email': 'aarav@example.com',
            'phone': '9876543210',
            'father_or_guardian_name': 'Rajesh Sharma',
            'gender': 'Male',
            'class_10_school': 'Kendriya Vidyalaya',
            'class_10_percentage': '85.00',
            'class_12_school': 'Kendriya Vidyalaya',
            'class_12_percentage': '88.00',
        }
        form = StudentRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_registration_form_ineligible_class_10_percentage_fails(self):
        self.college1.min_10th_percentage = Decimal('75.00')
        self.college1.save()

        form_data = {
            'college': self.college1.id,
            'course': self.course1.id,
            'first_name': 'Aarav',
            'last_name': 'Sharma',
            'full_name': 'Aarav Sharma',
            'email': 'aarav@example.com',
            'phone': '9876543210',
            'father_or_guardian_name': 'Rajesh Sharma',
            'gender': 'Male',
            'class_10_school': 'Kendriya Vidyalaya',
            'class_10_percentage': '65.00',  # Below cutoff 75%
            'class_12_school': 'Kendriya Vidyalaya',
            'class_12_percentage': '88.00',
        }
        form = StudentRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('class_10_percentage', form.errors)
        self.assertIn('Eligibility criteria not met', form.errors['class_10_percentage'][0])

    def test_registration_form_ineligible_class_12_percentage_fails(self):
        self.college1.min_12th_percentage = Decimal('80.00')
        self.college1.save()

        form_data = {
            'college': self.college1.id,
            'course': self.course1.id,
            'first_name': 'Aarav',
            'last_name': 'Sharma',
            'full_name': 'Aarav Sharma',
            'email': 'aarav@example.com',
            'phone': '9876543210',
            'father_or_guardian_name': 'Rajesh Sharma',
            'gender': 'Male',
            'class_10_school': 'Kendriya Vidyalaya',
            'class_10_percentage': '85.00',
            'class_12_school': 'Kendriya Vidyalaya',
            'class_12_percentage': '70.00',  # Below cutoff 80%
        }
        form = StudentRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('class_12_percentage', form.errors)
        self.assertIn('Eligibility criteria not met', form.errors['class_12_percentage'][0])

    def test_invalid_registration_mismatched_college_course(self):
        # course2 belongs to college2, not college1
        form_data = {
            'college': self.college1.id,
            'course': self.course2.id,
            'first_name': 'Aarav',
            'last_name': 'Sharma',
            'full_name': 'Aarav Sharma',
            'email': 'aarav@example.com',
            'phone': '9876543210',
            'father_or_guardian_name': 'Rajesh Sharma',
            'gender': 'Male',
            'class_10_school': 'Kendriya Vidyalaya',
            'class_10_percentage': '85.00',
            'class_12_school': 'Kendriya Vidyalaya',
            'class_12_percentage': '88.00',
        }
        form = StudentRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue('course' in form.errors or '__all__' in form.errors)


class StudentRegistrationViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.university = University.objects.create(
            name="Jadavpur University",
            city="Kolkata",
            state="West Bengal",
            established_year=1955,
            rating=Decimal("4.6")
        )
        self.college = College.objects.create(
            university=self.university,
            name="Faculty of Engineering & Tech",
            city="Kolkata",
            fees=Decimal("30000.00"),
            rating=Decimal("4.7"),
            admin_email="admin@jadavpur.edu"
        )
        self.course = Course.objects.create(
            college=self.college,
            name="B.E. Information Technology",
            duration_years=4,
            fee=Decimal("30000.00"),
            seats=60
        )
        self.student_user = User.objects.create_user(
            username="student_user",
            email="student@example.com",
            password="password123",
            first_name="Rohan",
            last_name="Gupta"
        )
        # Profile is created via post_save signal with role='student'

        self.uni_user = User.objects.create_user(
            username="uni_user",
            email="partner@example.com",
            password="password123"
        )
        self.uni_user.profile.role = 'university'
        self.uni_user.profile.save()

    def test_unauthenticated_user_redirected_to_student_login(self):
        response = self.client.get(reverse('registration_form'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
        self.assertIn('role=student', response.url)

    def test_non_student_user_redirected_to_student_login(self):
        self.client.login(username="uni_user", password="password123")
        response = self.client.get(reverse('registration_form'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('university_dashboard'), response.url)

    def test_get_registration_page_when_logged_in_as_student(self):
        self.client.login(username="student_user", password="password123")
        response = self.client.get(reverse('registration_form'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/registration_form.html')
        self.assertEqual(response.context['form'].initial.get('full_name'), 'Rohan Gupta')
        self.assertEqual(response.context['form'].initial.get('email'), 'student@example.com')

    def test_post_creates_registration_and_sends_email(self):
        self.client.login(username="student_user", password="password123")
        mail.outbox.clear()

        post_data = {
            'college': self.college.id,
            'course': self.course.id,
            'first_name': 'Rohan',
            'last_name': 'Gupta',
            'full_name': 'Rohan Gupta',
            'email': 'rohan.gupta@example.com',
            'phone': '9988776655',
            'father_or_guardian_name': 'Mr. Gupta',
            'gender': 'Male',
            'class_10_school': 'Delhi Public School',
            'class_10_percentage': '82.00',
            'class_12_school': 'Delhi Public School',
            'class_12_percentage': '85.00',
        }
        response = self.client.post(reverse('registration_form'), post_data)

        self.assertEqual(StudentRegistration.objects.count(), 1)
        registration = StudentRegistration.objects.first()
        self.assertEqual(registration.full_name, 'Rohan Gupta')
        self.assertEqual(registration.status, 'Pending')

        # Check redirect to success page
        expected_url = reverse('registration_success', kwargs={'registration_id': registration.registration_id})
        self.assertRedirects(response, expected_url)

        # Check email sent
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertIn("Admission Registration Confirmation", sent_email.subject)
        self.assertIn(registration.full_name, sent_email.body)
        self.assertIn(str(registration.registration_id), sent_email.body)
        self.assertEqual(sent_email.to, ['rohan.gupta@example.com'])

    def test_post_ineligible_percentages_blocked_and_no_record_created(self):
        self.college.min_10th_percentage = Decimal('80.00')
        self.college.min_12th_percentage = Decimal('80.00')
        self.college.save()

        self.client.login(username="student_user", password="password123")
        mail.outbox.clear()

        # Ineligible applicant: 70% in Class X and 75% in Class XII (below 80% cutoffs)
        post_data = {
            'college': self.college.id,
            'course': self.course.id,
            'first_name': 'Rohan',
            'last_name': 'Gupta',
            'full_name': 'Rohan Gupta',
            'email': 'rohan.gupta@example.com',
            'phone': '9988776655',
            'father_or_guardian_name': 'Mr. Gupta',
            'gender': 'Male',
            'class_10_school': 'Delhi Public School',
            'class_10_percentage': '70.00',
            'class_12_school': 'Delhi Public School',
            'class_12_percentage': '75.00',
        }
        response = self.client.post(reverse('registration_form'), post_data)

        # Form must return 200 with validation errors and block registration
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StudentRegistration.objects.count(), 0)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('class_10_percentage', response.context['form'].errors)
        self.assertIn('class_12_percentage', response.context['form'].errors)
        self.assertEqual(len(mail.outbox), 0)


class CompareSessionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.university = University.objects.create(
            name="Pune University",
            city="Pune",
            state="Maharashtra",
            established_year=1949,
            rating=Decimal("4.2")
        )
        self.colleges = [
            College.objects.create(
                university=self.university,
                name=f"College {i}",
                city="Pune",
                fees=Decimal("100000.00"),
                rating=Decimal("4.0")
            )
            for i in range(1, 6)
        ]

    def test_add_remove_clear_comparison(self):
        c1 = self.colleges[0]
        c2 = self.colleges[1]

        # Add college 1
        self.client.get(reverse('compare_add', kwargs={'college_id': c1.id}))
        session = self.client.session
        self.assertIn(c1.id, session['compare_colleges'])

        # Add college 2
        self.client.get(reverse('compare_add', kwargs={'college_id': c2.id}))
        session = self.client.session
        self.assertEqual(len(session['compare_colleges']), 2)

        # Remove college 1
        self.client.get(reverse('compare_remove', kwargs={'college_id': c1.id}))
        session = self.client.session
        self.assertNotIn(c1.id, session['compare_colleges'])
        self.assertIn(c2.id, session['compare_colleges'])

        # Clear comparison
        self.client.get(reverse('compare_clear'))
        session = self.client.session
        self.assertEqual(session['compare_colleges'], [])


class APITest(APITestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Hyderabad Central University",
            city="Hyderabad",
            state="Telangana",
            established_year=1974,
            rating=Decimal("4.6")
        )
        self.college = College.objects.create(
            university=self.university,
            name="School of Computer and Information Sciences",
            city="Hyderabad",
            fees=Decimal("50000.00"),
            rating=Decimal("4.7")
        )
        self.course = Course.objects.create(
            college=self.college,
            name="Integrated M.Tech Computer Science",
            duration_years=5,
            fee=Decimal("60000.00"),
            seats=40
        )

    def test_get_universities_api(self):
        url = reverse('api-university-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that result contains university name
        results = response.data.get('results', response.data)
        self.assertTrue(any(u['name'] == "Hyderabad Central University" for u in results))

    def test_post_registration_api(self):
        mail.outbox.clear()
        url = reverse('api-register')
        payload = {
            'full_name': 'Meera Nair',
            'email': 'meera@example.com',
            'phone': '9123456780',
            'college': self.college.id,
            'course': self.course.id,
        }
        response = self.client.post(url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('registration_id', response.data)
        self.assertEqual(StudentRegistration.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)


class CollegeAccommodationsWorkflowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.university = University.objects.create(
            name="Delhi Technological University",
            city="New Delhi",
            state="Delhi",
            established_year=1941,
            rating=Decimal("4.6")
        )
        self.college = College.objects.create(
            university=self.university,
            name="Delhi College of Engineering",
            city="New Delhi",
            fees=Decimal("190000.00"),
            rating=Decimal("4.7")
        )
        self.course = Course.objects.create(
            college=self.college,
            name="B.Tech Software Engineering",
            duration_years=4,
            fee=Decimal("190000.00"),
            seats=120
        )
        self.acc1 = Accommodation.objects.create(
            college=self.college,
            name="DTU Campus Hostel",
            type="Hostel",
            address="Shahbad Daulatpur, Bawana Road",
            city="New Delhi",
            rent=Decimal("4500.00"),
            room_type="Double",
            facilities="Wi-Fi, Mess, Gym, 24/7 Security",
            contact_phone="9811002233",
            contact_email="hostel@dtu.ac.in",
            is_available=True
        )
        self.acc2 = Accommodation.objects.create(
            name="Rohini Student PG",
            type="PG",
            address="Sector 16, Rohini",
            city="New Delhi",
            rent=Decimal("7500.00"),
            room_type="Single",
            facilities="AC, Wi-Fi, Food Included",
            contact_phone="9877001122",
            contact_email="rohini.pg@example.com",
            is_available=True
        )

    def test_college_accommodations_view(self):
        url = reverse('college_accommodations', kwargs={'slug': self.college.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DTU Campus Hostel")
        self.assertContains(response, "Rohini Student PG")
        self.assertContains(response, "Delhi College of Engineering")

    def test_registration_success_links_to_college_accommodations(self):
        registration = StudentRegistration.objects.create(
            full_name="Rohan Verma",
            email="rohan@example.com",
            phone="9876501234",
            college=self.college,
            course=self.course
        )
        url = reverse('registration_success', kwargs={'registration_id': registration.registration_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        target_acc_url = reverse('college_accommodations', kwargs={'slug': self.college.slug})
        self.assertContains(response, target_acc_url)
        self.assertContains(response, "Explore PGs &amp; Hostels")

    def test_api_location_colleges(self):
        url = f"{reverse('api_location_colleges')}?city=New Delhi"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('colleges', data)
        self.assertTrue(any(c['name'] == "Delhi College of Engineering" for c in data['colleges']))

    def test_api_college_recommendations(self):
        url = reverse('api_college_recommendations', kwargs={'college_id': self.college.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('college', data)
        self.assertIn('accommodations', data)
        self.assertEqual(len(data['accommodations']), 2)

    def test_my_applications_view_and_session(self):
        registration = StudentRegistration.objects.create(
            full_name="Aanya Gupta",
            email="aanya@example.com",
            phone="9811223344",
            college=self.college,
            course=self.course
        )
        url = reverse('my_applications')
        # 1. Direct page view
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Applied")

        # 2. Search by registration UUID
        resp_search = self.client.get(f"{url}?q={registration.registration_id}")
        self.assertEqual(resp_search.status_code, 200)
        self.assertContains(resp_search, "Aanya Gupta")
        self.assertContains(resp_search, "Delhi College of Engineering")

        # 3. View with session stored id
        session = self.client.session
        session['my_registration_ids'] = [str(registration.registration_id)]
        session.save()
        resp_session = self.client.get(url)
        self.assertEqual(resp_session.status_code, 200)
        self.assertContains(resp_session, "Aanya Gupta")
        self.assertContains(resp_session, str(registration.registration_id))

    def test_my_applications_unauthenticated_shows_login_card(self):
        """Unauthenticated visitor to /applications/ without search query sees prominent login card and login buttons."""
        url = reverse('my_applications')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Please Log In to View Your Applications")
        self.assertContains(resp, "Log In to Student Account")
        self.assertContains(resp, "Create Free Account")
        self.assertNotContains(resp, "No college applications found")


class PartnerSubmissionAndApprovalTest(TestCase):
    def setUp(self):
        # Admin user
        self.admin_user = User.objects.create_superuser(
            username='admin_moderator',
            email='admin@collegeclue.local',
            password='Password123!'
        )
        # University partner user
        self.uni_user = User.objects.create_user(
            username='uni_partner',
            email='partner@university.org',
            password='Password123!'
        )
        self.uni_user.profile.role = 'university'
        self.uni_user.profile.save()

        # Accommodation provider user
        self.acc_user = User.objects.create_user(
            username='acc_provider',
            email='owner@stayhostel.com',
            password='Password123!'
        )
        self.acc_user.profile.role = 'accommodation'
        self.acc_user.profile.save()

        # Base university
        self.university = University.objects.create(
            name="Bangalore Central University",
            city="Bengaluru",
            state="Karnataka",
            established_year=2015,
            rating=Decimal("4.4")
        )

    def test_partner_college_submission_and_admin_approval(self):
        # 1. Partner logs in and submits a college
        self.client.login(username='uni_partner', password='Password123!')
        submit_url = reverse('college_submit')
        post_data = {
            'university': self.university.id,
            'name': 'Bengaluru Institute of Advanced Tech',
            'city': 'Bengaluru',
            'fees': '180000.00',
            'rating': '4.6',
            'facilities': 'Robotics Lab, Cloud Computing Center',
            'description': 'Modern engineering and computer science campus.',
            'course_1_name': 'B.Tech Artificial Intelligence',
            'course_1_duration': 4,
            'course_1_fee': '190000.00',
            'course_1_seats': 60,
        }
        resp = self.client.post(submit_url, post_data)
        self.assertEqual(resp.status_code, 302)  # Redirects to university dashboard

        # 2. Verify college is saved with status Pending
        college = College.objects.get(name='Bengaluru Institute of Advanced Tech')
        self.assertEqual(college.status, 'Pending')
        self.assertEqual(college.submitted_by, self.uni_user)
        self.assertEqual(college.courses.count(), 1)

        # 3. Check public college list with a fresh guest client: Pending college should NOT appear in queryset
        guest_client = Client()
        public_resp = guest_client.get(reverse('college_list'))
        self.assertNotIn(college, public_resp.context['colleges'])
        self.assertNotContains(public_resp, 'Bengaluru Institute of Advanced Tech')

        # 4. Admin logs in and checks moderation queue
        self.client.logout()
        self.client.login(username='admin_moderator', password='Password123!')
        mod_resp = self.client.get(reverse('admin_moderation'))
        self.assertEqual(mod_resp.status_code, 200)
        self.assertContains(mod_resp, 'Bengaluru Institute of Advanced Tech')

        # 5. Admin approves the college
        approve_url = reverse('admin_approve_college', kwargs={'college_id': college.id})
        approve_resp = self.client.post(approve_url, {'admin_notes': 'Verified accredited university'})
        self.assertEqual(approve_resp.status_code, 302)

        college.refresh_from_db()
        self.assertEqual(college.status, 'Approved')

        # 6. Now the college MUST appear on the public college list
        public_resp_after = guest_client.get(reverse('college_list'))
        self.assertIn(college, public_resp_after.context['colleges'])
        self.assertContains(public_resp_after, 'Bengaluru Institute of Advanced Tech')

    def test_accommodation_submission_and_admin_approval(self):
        # 1. Base approved college
        college = College.objects.create(
            university=self.university,
            name="Alliance Tech College",
            city="Bengaluru",
            fees=Decimal("200000.00"),
            rating=Decimal("4.5"),
            status='Approved'
        )

        # 2. Housing partner logs in and submits accommodation
        self.client.login(username='acc_provider', password='Password123!')
        submit_url = reverse('accommodation_submit')
        post_data = {
            'name': 'Alliance Green Student Residency',
            'type': 'PG',
            'college': college.id,
            'city': 'Bengaluru',
            'address': 'Plot 45, Near Tech Park, Electronic City',
            'rent': '9500.00',
            'room_type': 'Double',
            'facilities': 'Wi-Fi, 3 Meals, Security, Study Desk',
            'contact_phone': '9876543210',
            'contact_email': 'stay@allianceresidency.in',
        }
        resp = self.client.post(submit_url, post_data)
        self.assertEqual(resp.status_code, 302)

        # 3. Verify accommodation is Pending
        acc = Accommodation.objects.get(name='Alliance Green Student Residency')
        self.assertEqual(acc.status, 'Pending')
        self.assertEqual(acc.submitted_by, self.acc_user)

        # 4. Check public accommodation list: Pending accommodation should NOT appear
        guest_client = Client()
        public_resp = guest_client.get(reverse('accommodation_list'))
        self.assertNotIn(acc, public_resp.context['accommodations'])
        self.assertNotContains(public_resp, 'Alliance Green Student Residency')

        # 5. Admin approves the accommodation
        self.client.logout()
        self.client.login(username='admin_moderator', password='Password123!')
        approve_url = reverse('admin_approve_acc', kwargs={'acc_id': acc.id})
        approve_resp = self.client.post(approve_url, {'admin_notes': 'Property inspected and verified'})
        self.assertEqual(approve_resp.status_code, 302)

        acc.refresh_from_db()
        self.assertEqual(acc.status, 'Approved')

        # 6. Now accommodation appears on the public list
        public_resp_after = guest_client.get(reverse('accommodation_list'))
        self.assertIn(acc, public_resp_after.context['accommodations'])
        self.assertContains(public_resp_after, 'Alliance Green Student Residency')

    def test_role_access_guard_blocks_student(self):
        # Create student user
        student_user = User.objects.create_user(
            username='student_riya',
            email='riya@student.edu',
            password='Password123!'
        )
        student_user.profile.role = 'student'
        student_user.profile.save()

        self.client.login(username='student_riya', password='Password123!')

        # Student trying to access University Partner dashboard is redirected to home
        resp_uni = self.client.get(reverse('university_dashboard'))
        self.assertEqual(resp_uni.status_code, 302)
        self.assertRedirects(resp_uni, reverse('home'))

        # Student trying to access Housing dashboard is redirected to home
        resp_acc = self.client.get(reverse('accommodation_dashboard'))
        self.assertEqual(resp_acc.status_code, 302)
        self.assertRedirects(resp_acc, reverse('home'))

        # Student trying to access Admin Moderation is blocked
        resp_mod = self.client.get(reverse('admin_moderation'))
        self.assertEqual(resp_mod.status_code, 302)

    def test_approved_college_edit_and_course_addition(self):
        college = College.objects.create(
            university=self.university,
            name="Bangalore School of Design",
            city="Bengaluru",
            fees=Decimal("150000.00"),
            rating=Decimal("4.3"),
            status='Approved',
            submitted_by=self.uni_user
        )

        self.client.login(username='uni_partner', password='Password123!')

        # 1. Open edit page
        edit_url = reverse('college_edit', kwargs={'college_id': college.id})
        resp = self.client.get(edit_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Bangalore School of Design")

        # 2. Update college details
        update_data = {
            'name': 'Bangalore School of Design & Media',
            'city': 'Bengaluru',
            'fees': '175000.00',
            'rating': '4.5',
            'facilities': '3D Printing Studio, Animation Lab, Sound Studio',
            'description': 'Premier design and media institute.',
        }
        resp_post = self.client.post(edit_url, update_data)
        self.assertEqual(resp_post.status_code, 302)

        college.refresh_from_db()
        self.assertEqual(college.name, 'Bangalore School of Design & Media')
        self.assertEqual(college.fees, Decimal('175000.00'))

        # 3. Add new course
        add_course_url = reverse('course_add', kwargs={'college_id': college.id})
        course_data = {
            'name': 'B.Des User Experience & Interaction',
            'duration_years': 4,
            'fee': '180000.00',
            'seats': 45,
        }
        resp_course = self.client.post(add_course_url, course_data)
        self.assertEqual(resp_course.status_code, 302)

        new_course = Course.objects.get(name='B.Des User Experience & Interaction', college=college)
        self.assertEqual(new_course.seats, 45)

        # 4. Delete course
        del_url = reverse('course_delete', kwargs={'college_id': college.id, 'course_id': new_course.id})
        resp_del = self.client.post(del_url)
        self.assertEqual(resp_del.status_code, 302)
        self.assertFalse(Course.objects.filter(id=new_course.id).exists())

    def test_approved_accommodation_edit_and_vacancy_toggle(self):
        acc = Accommodation.objects.create(
            name="Green Valley Student PG",
            type="PG",
            city="Bengaluru",
            address="Near Metro Station, Electronic City",
            rent=Decimal("8000.00"),
            room_type="Single",
            facilities="Wi-Fi, 3 Meals",
            contact_phone="9876500000",
            contact_email="pg@greenvalley.com",
            is_available=True,
            status='Approved',
            submitted_by=self.acc_user
        )

        self.client.login(username='acc_provider', password='Password123!')

        # 1. Open edit page
        edit_url = reverse('accommodation_edit', kwargs={'acc_id': acc.id})
        resp = self.client.get(edit_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Green Valley Student PG")

        # 2. Update details
        post_data = {
            'name': 'Green Valley Premium Student Residency',
            'type': 'PG',
            'city': 'Bengaluru',
            'address': 'Near Metro Station, Electronic City Phase 1',
            'rent': '8500.00',
            'room_type': 'Single',
            'is_available': True,
            'facilities': 'High-speed Wi-Fi, 3 North/South Meals, Gym, CCTV',
            'contact_phone': '9876500000',
            'contact_email': 'pg@greenvalley.com',
        }
        resp_post = self.client.post(edit_url, post_data)
        self.assertEqual(resp_post.status_code, 302)

        acc.refresh_from_db()
        self.assertEqual(acc.name, 'Green Valley Premium Student Residency')
        self.assertEqual(acc.rent, Decimal('8500.00'))

        # 3. Quick Vacancy Toggle: True -> False
        toggle_url = reverse('accommodation_toggle_vacancy', kwargs={'acc_id': acc.id})
        resp_toggle = self.client.post(toggle_url)
        self.assertEqual(resp_toggle.status_code, 302)

        acc.refresh_from_db()
        self.assertFalse(acc.is_available)

        # 4. Quick Vacancy Toggle: False -> True
        resp_toggle_back = self.client.post(toggle_url)
        self.assertEqual(resp_toggle_back.status_code, 302)

        acc.refresh_from_db()
        self.assertTrue(acc.is_available)

    def test_live_search_suggest_api(self):
        # Create sample approved college
        College.objects.create(
            university=self.university,
            name="Bangalore Institute of Management Studies",
            city="Bengaluru",
            fees=Decimal("220000.00"),
            rating=Decimal("4.7"),
            status='Approved'
        )

        # Call auto-suggest API for "Bangalore"
        api_url = f"{reverse('api_search_suggest')}?q=Bangalore"
        resp = self.client.get(api_url)
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIn('results', data)
        self.assertIn('universities', data['results'])
        self.assertIn('colleges', data['results'])

        # Verify matching results are returned
        uni_names = [u['name'] for u in data['results']['universities']]
        self.assertIn("Bangalore Central University", uni_names)

        col_names = [c['name'] for c in data['results']['colleges']]
        self.assertIn("Bangalore Institute of Management Studies", col_names)


class UniversityAdminAndApplicationWorkflowTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.university = University.objects.create(
            name="SVR Technical University",
            city="Bengaluru",
            state="Karnataka",
            established_year=1998,
            rating=Decimal("4.6")
        )

        # Primary admin for College 1
        self.primary_admin_1 = User.objects.create_user(
            username="svr_admin",
            email="admin@svr.edu.in",
            password="Password123!"
        )
        self.primary_admin_1.profile.role = 'university'
        self.primary_admin_1.profile.save()

        # Primary admin for College 2
        self.primary_admin_2 = User.objects.create_user(
            username="other_admin",
            email="admin@other.edu.in",
            password="Password123!"
        )
        self.primary_admin_2.profile.role = 'university'
        self.primary_admin_2.profile.save()

        # Student user
        self.student = User.objects.create_user(
            username="applicant_student",
            email="student.applicant@example.com",
            password="Password123!",
            first_name="Pooja",
            last_name="Hegde"
        )
        # Student role assigned automatically by signal

        # College 1
        self.college_1 = College.objects.create(
            university=self.university,
            name="SVR College of Engineering",
            city="Bengaluru",
            fees=Decimal("120000.00"),
            rating=Decimal("4.5"),
            status='Approved',
            submitted_by=self.primary_admin_1,
            admin_email="admin@svr.edu.in",
            max_team_members=1
        )
        self.course_1 = Course.objects.create(
            college=self.college_1,
            name="B.Tech Artificial Intelligence",
            duration_years=4,
            fee=Decimal("150000.00"),
            seats=60
        )

        # College 2
        self.college_2 = College.objects.create(
            university=self.university,
            name="Other Metropolitan College",
            city="Bengaluru",
            fees=Decimal("90000.00"),
            rating=Decimal("4.0"),
            status='Approved',
            submitted_by=self.primary_admin_2,
            admin_email="admin@other.edu.in",
            max_team_members=1
        )

    def test_college_admin_and_team_authorization(self):
        # 1. Primary admin has authority
        self.assertTrue(self.college_1.is_admin_or_team(self.primary_admin_1))

        # 2. Other college admin does NOT have authority over College 1
        self.assertFalse(self.college_1.is_admin_or_team(self.primary_admin_2))

        # 3. Add team member
        staff_user = User.objects.create_user(
            username="svr_staff",
            email="admissions@svr.edu.in",
            password="Password123!"
        )
        CollegeTeamMember.objects.create(
            college=self.college_1,
            email="admissions@svr.edu.in",
            user=staff_user,
            added_by=self.primary_admin_1
        )
        self.assertTrue(self.college_1.is_admin_or_team(staff_user))

    def test_team_management_capacity_and_staff_addition(self):
        self.client.login(username="svr_admin", password="Password123!")

        team_url = reverse('college_team', kwargs={'college_id': self.college_1.id})

        # 1. Update team capacity from 1 to 4
        resp = self.client.post(team_url, {
            'action': 'update_settings',
            'admin_email': 'principal@svr.edu.in',
            'max_team_members': '4',
        })
        self.assertEqual(resp.status_code, 302)
        self.college_1.refresh_from_db()
        self.assertEqual(self.college_1.max_team_members, 4)
        self.assertEqual(self.college_1.admin_email, 'principal@svr.edu.in')

        # 2. Add staff member
        resp_add = self.client.post(team_url, {
            'action': 'add_member',
            'staff_email': 'admissions.officer@svr.edu.in',
        })
        self.assertEqual(resp_add.status_code, 302)
        self.assertEqual(self.college_1.team_members.count(), 1)
        member = self.college_1.team_members.first()
        self.assertEqual(member.email, 'admissions.officer@svr.edu.in')

        # 3. Remove staff member
        resp_remove = self.client.post(team_url, {
            'action': 'remove_member',
            'member_id': member.id,
        })
        self.assertEqual(resp_remove.status_code, 302)
        self.assertEqual(self.college_1.team_members.count(), 0)

    def test_team_capacity_limit_enforced(self):
        self.client.login(username="svr_admin", password="Password123!")
        team_url = reverse('college_team', kwargs={'college_id': self.college_1.id})

        # College 1 max_team_members is 1
        self.assertEqual(self.college_1.max_team_members, 1)

        # Add 1st member
        self.client.post(team_url, {
            'action': 'add_member',
            'staff_email': 'staff1@svr.edu.in',
        })
        self.assertEqual(self.college_1.team_members.count(), 1)

        # Try to add 2nd member exceeding quota
        self.client.post(team_url, {
            'action': 'add_member',
            'staff_email': 'staff2@svr.edu.in',
        })
        # Should remain at 1
        self.assertEqual(self.college_1.team_members.count(), 1)

    def test_application_routing_and_approval_workflow(self):
        # 1. Student applies for College 1
        reg = StudentRegistration.objects.create(
            full_name="Pooja Hegde",
            email="student.applicant@example.com",
            phone="9876543210",
            college=self.college_1,
            course=self.course_1,
            status='Pending'
        )

        # 2. Login as Admin of College 1
        self.client.login(username="svr_admin", password="Password123!")
        app_list_url = reverse('university_applications')
        resp = self.client.get(app_list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Pooja Hegde")
        self.assertContains(resp, "B.Tech Artificial Intelligence")
        self.assertContains(resp, str(reg.registration_id))

        # 3. Login as Admin of College 2 -> Should NOT see College 1's application
        self.client.login(username="other_admin", password="Password123!")
        resp_other = self.client.get(app_list_url)
        self.assertEqual(resp_other.status_code, 200)
        self.assertNotContains(resp_other, "Pooja Hegde")

        # 4. Admin 1 approves application
        self.client.login(username="svr_admin", password="Password123!")
        mail.outbox.clear()

        approve_url = reverse('university_application_approve', kwargs={'registration_id': reg.registration_id})
        resp_approve = self.client.post(approve_url, {
            'admin_notes': 'Document verification cleared. Welcome to SVR!'
        })
        self.assertEqual(resp_approve.status_code, 302)

        reg.refresh_from_db()
        self.assertEqual(reg.status, 'Confirmed')
        self.assertEqual(reg.reviewed_by, self.primary_admin_1)
        self.assertIn("Document verification cleared", reg.admin_notes)

        # Verify confirmation email sent to student
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertIn("Admission Approved", sent_email.subject)
        self.assertEqual(sent_email.to, ["student.applicant@example.com"])

        # 5. Admin 1 rejects / cancels application
        mail.outbox.clear()
        reject_url = reverse('university_application_reject', kwargs={'registration_id': reg.registration_id})
        resp_reject = self.client.post(reject_url, {
            'admin_notes': 'Seats filled for this batch.'
        })
        self.assertEqual(resp_reject.status_code, 302)

        reg.refresh_from_db()
        self.assertEqual(reg.status, 'Cancelled')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Admission Update", mail.outbox[0].subject)

    def test_portal_isolation_on_college_detail(self):
        college_detail_url = reverse('college_detail', kwargs={'slug': self.college_1.slug})

        # 1. As Student: sees "Apply for Admission"
        self.client.login(username="applicant_student", password="Password123!")
        resp_student = self.client.get(college_detail_url)
        self.assertEqual(resp_student.status_code, 200)
        self.assertContains(resp_student, "Apply for Admission")
        self.assertContains(resp_student, "Enroll Now")

        # 2. As College Admin: sees "Review Applications" and "Manage Campus", NOT "Apply for Admission"
        self.client.login(username="svr_admin", password="Password123!")
        resp_admin = self.client.get(college_detail_url)
        self.assertEqual(resp_admin.status_code, 200)
        self.assertContains(resp_admin, "Review Applications")
        self.assertContains(resp_admin, "Manage Campus")
        self.assertNotContains(resp_admin, "Apply for Admission")
        self.assertNotContains(resp_admin, "Enroll Now")


class CollegeRegistrationStatusAndDisclaimerTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.university = University.objects.create(
            name="Alliance National University",
            city="Bengaluru",
            state="Karnataka",
            established_year=2010,
            rating=Decimal("4.5")
        )

        self.student = User.objects.create_user(
            username="student_user",
            email="student@example.com",
            password="Password123!"
        )

        # 1. Registered College (has admin_email)
        self.registered_college = College.objects.create(
            university=self.university,
            name="Alliance Tech Engineering",
            city="Bengaluru",
            fees=Decimal("250000.00"),
            rating=Decimal("4.5"),
            status='Approved',
            admin_email="admissions@alliance.edu.in"
        )
        self.reg_course = Course.objects.create(
            college=self.registered_college,
            name="B.Tech Computer Science",
            duration_years=4,
            fee=Decimal("250000.00"),
            seats=60
        )

        # 2. Unregistered College (no admin_email, no submitted_by)
        self.unregistered_college = College.objects.create(
            university=self.university,
            name="Alliance Arts & Science Directory",
            city="Bengaluru",
            fees=Decimal("150000.00"),
            rating=Decimal("4.2"),
            status='Approved',
            admin_email="",
            submitted_by=None
        )
        self.unreg_course = Course.objects.create(
            college=self.unregistered_college,
            name="B.Sc Mathematics",
            duration_years=3,
            fee=Decimal("150000.00"),
            seats=40
        )

    def test_is_registered_property(self):
        self.assertTrue(self.registered_college.is_registered)
        self.assertFalse(self.unregistered_college.is_registered)

    def test_unregistered_college_shows_disclaimer_and_disables_apply(self):
        self.client.login(username="student_user", password="Password123!")
        url = reverse('college_detail', kwargs={'slug': self.unregistered_college.slug})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Application will be open Soon")
        self.assertContains(resp, "View on Google Maps")
        self.assertContains(resp, "Application Unavailable")
        self.assertNotContains(resp, f"{reverse('registration_form')}?college={self.unregistered_college.id}")

    def test_registered_college_shows_active_apply_and_partner_badge(self):
        self.client.login(username="student_user", password="Password123!")
        url = reverse('college_detail', kwargs={'slug': self.registered_college.slug})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Registered Official Partner")
        self.assertContains(resp, "Apply for Admission")
        self.assertContains(resp, f"{reverse('registration_form')}?college={self.registered_college.id}")
        self.assertNotContains(resp, "This particular college is not registered here, so application to apply is not available.")

    def test_registration_form_blocks_unregistered_college(self):
        self.client.login(username="student_user", password="Password123!")
        # Attempt to access registration form with unregistered college id
        url = f"{reverse('registration_form')}?college={self.unregistered_college.id}"
        resp = self.client.get(url, follow=True)

        # Redirected back to college detail with disclaimer message
        self.assertRedirects(resp, reverse('college_detail', kwargs={'slug': self.unregistered_college.slug}))
        self.assertContains(resp, "This particular college")
        self.assertContains(resp, "is not registered here, so application to apply is not available.")

    def test_api_search_suggest_includes_is_registered_and_logo(self):
        url = f"{reverse('api_search_suggest')}?q=Alliance"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        colleges = data['results']['colleges']
        self.assertTrue(len(colleges) >= 2)

        reg_match = next((c for c in colleges if c['id'] == self.registered_college.id), None)
        unreg_match = next((c for c in colleges if c['id'] == self.unregistered_college.id), None)

        self.assertIsNotNone(reg_match)
        self.assertIsNotNone(unreg_match)
        self.assertTrue(reg_match['is_registered'])
        self.assertFalse(unreg_match['is_registered'])
        self.assertIn('logo_url', reg_match)


class AboutPageAndSidebarTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="sidebar_student",
            email="sidebar_student@example.com",
            password="Password123!",
            first_name="Rohan"
        )
        self.profile = self.user.profile
        self.profile.role = "student"
        self.profile.save()
        self.university = University.objects.create(
            name="Apex National University",
            city="Bengaluru",
            state="Karnataka",
            established_year=2000,
            rating=Decimal("4.5")
        )
        self.college = College.objects.create(
            university=self.university,
            name="Apex Institute of Technology",
            city="Bengaluru",
            fees=Decimal("150000.00"),
            rating=Decimal("4.6"),
            admin_email="apex_admin@example.com"
        )
        self.accommodation = Accommodation.objects.create(
            name="Apex Luxury Student PG",
            type="PG",
            address="12 Main Rd, Koramangala",
            city="Bengaluru",
            rent=Decimal("8500.00"),
            room_type="Single",
            contact_phone="9876543210",
            contact_email="apex_pg@example.com",
            status="Approved"
        )

    def test_about_page_renders_successfully(self):
        resp = self.client.get(reverse('about'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'core/about.html')
        self.assertContains(resp, "About CollegeClue")
        self.assertContains(resp, "Student Trust Guarantee")
        self.assertContains(resp, "Zero Brokerage on Housing")
        self.assertContains(resp, "Direct Routing to College Admins")
        self.assertEqual(resp.context['total_colleges'], 1)
        self.assertEqual(resp.context['registered_colleges'], 1)
        self.assertEqual(resp.context['total_accommodations'], 1)
        self.assertEqual(resp.context['total_universities'], 1)

    def test_sidebar_menu_rendered_with_required_elements_guest(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        # Verify sidebar element and title
        self.assertContains(resp, "id=\"collegeClueSidebar\"")
        self.assertContains(resp, "College<span class=\"text-warning\">Clue</span>")
        self.assertContains(resp, "MENU")

        # Verify 6 core required sidebar sections/links
        self.assertContains(resp, reverse('university_list'))
        self.assertContains(resp, "Universities")
        self.assertContains(resp, reverse('accommodation_list'))
        self.assertContains(resp, "Near by PG/Flats")
        self.assertContains(resp, reverse('wishlist'))
        self.assertContains(resp, "Wishlists")
        self.assertContains(resp, reverse('my_applications'))
        self.assertContains(resp, "Applied Status")
        self.assertContains(resp, reverse('about'))
        self.assertContains(resp, "About CollegeClue")

        # Guest status card
        self.assertContains(resp, "Guest Visitor")
        self.assertContains(resp, "Student Sign In")

    def test_sidebar_menu_rendered_with_authenticated_student(self):
        self.client.login(username="sidebar_student", password="Password123!")
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)

        # Authenticated student card in sidebar
        self.assertContains(resp, "id=\"collegeClueSidebar\"")
        self.assertContains(resp, "Student")
        self.assertContains(resp, "sidebar_student@example.com")
        self.assertContains(resp, "Rohan")
        self.assertContains(resp, reverse('logout'))


class AnimationRemovedAndStreamlinedNavbarTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="anim_student",
            email="anim_student@example.com",
            password="Password123!",
            first_name="Aarav"
        )

    def test_login_does_not_trigger_intro_animation(self):
        resp = self.client.post(reverse('login'), {
            'username': 'anim_student',
            'password': 'Password123!'
        }, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context.get('show_logo_animation', False))
        self.assertNotContains(resp, 'id="collegeClueIntroOverlay"')
        self.assertContains(resp, 'Welcome back, Aarav!')

    def test_overlay_and_animation_script_removed(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'id="collegeClueIntroOverlay"')
        self.assertNotContains(resp, 'ccRoamingCanvas')
        self.assertNotContains(resp, 'logo-animation.js')

    def test_top_navbar_streamlined_search_and_wishlist_only(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        # Verify Search bar exists
        self.assertContains(resp, 'id="navCollegeSearchInput"')
        # Verify Wishlist pill exists
        self.assertContains(resp, reverse('wishlist'))
        # Verify uncluttered top bar (no notification dropdown)
        self.assertNotContains(resp, 'id="notificationDropdown"')


class UniversityAdminEligibilityAndStatusReevaluationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_superuser(
            username="super_mod",
            email="super_mod@collegeclue.com",
            password="AdminPassword123!"
        )
        self.partner_user = User.objects.create_user(
            username="univ_admin_holder",
            email="dean@apex.edu.in",
            password="PartnerPassword123!"
        )
        self.partner_user.profile.role = 'university'
        self.partner_user.profile.organization_name = "Apex University"
        self.partner_user.profile.save()

        self.university = University.objects.create(
            name="Apex State University",
            slug="apex-state-university",
            city="Hyderabad",
            state="Telangana",
            established_year=1995
        )
        self.college = College.objects.create(
            university=self.university,
            name="Apex Institute of Engineering & Technology",
            slug="apex-iet",
            city="Hyderabad",
            fees=Decimal("120000.00"),
            min_10th_percentage=Decimal("50.00"),
            min_12th_percentage=Decimal("50.00"),
            status='Approved',
            submitted_by=self.partner_user,
            admin_email="dean@apex.edu.in"
        )
        self.course = Course.objects.create(
            college=self.college,
            name="B.Tech Computer Science",
            duration_years=4,
            fee=Decimal("125000.00"),
            seats=120
        )
        self.student = User.objects.create_user(
            username="applicant_rohit",
            email="rohit@example.com",
            password="Password123!",
            first_name="Rohit"
        )
        self.student.profile.role = 'student'
        self.student.profile.save()

    def test_university_admin_can_set_and_update_eligibility_cutoffs(self):
        self.client.login(username="univ_admin_holder", password="PartnerPassword123!")
        edit_url = reverse('college_edit', kwargs={'college_id': self.college.id})

        # Verify initial cutoffs in edit form
        resp_get = self.client.get(edit_url)
        self.assertEqual(resp_get.status_code, 200)
        self.assertContains(resp_get, "Academic Eligibility Cutoffs")
        self.assertContains(resp_get, 'name="min_10th_percentage"')
        self.assertContains(resp_get, 'name="min_12th_percentage"')

        # Update cutoffs to 65% and 75%
        update_data = {
            'name': 'Apex Institute of Engineering & Technology',
            'city': 'Hyderabad',
            'fees': '135000.00',
            'min_10th_percentage': '65.00',
            'min_12th_percentage': '75.00',
            'rating': '4.6',
            'facilities': 'AI Research Lab, Smart Classrooms, Library',
            'description': 'Leading technology institute in Hyderabad.',
        }
        resp_post = self.client.post(edit_url, update_data, follow=True)
        self.assertEqual(resp_post.status_code, 200)

        self.college.refresh_from_db()
        self.assertEqual(self.college.min_10th_percentage, Decimal('65.00'))
        self.assertEqual(self.college.min_12th_percentage, Decimal('75.00'))

        # Public detail page should reflect the new cutoffs
        detail_url = reverse('college_detail', kwargs={'slug': self.college.slug})
        resp_detail = self.client.get(detail_url)
        self.assertContains(resp_detail, "65.00%")
        self.assertContains(resp_detail, "75.00%")

    def test_university_application_status_update_and_re_evaluation(self):
        # Create an application
        app = StudentRegistration.objects.create(
            college=self.college,
            course=self.course,
            first_name="Rohit",
            last_name="Sharma",
            full_name="Rohit Sharma",
            email="rohit@example.com",
            phone="9876543210",
            father_or_guardian_name="Suresh Sharma",
            date_of_birth="2005-04-12",
            gender="Male",
            class_10_percentage=Decimal("78.50"),
            class_12_percentage=Decimal("82.00"),
            status='Pending'
        )

        self.client.login(username="univ_admin_holder", password="PartnerPassword123!")
        update_url = reverse('university_application_status_update', kwargs={'registration_id': app.registration_id})

        # 1. Approve Application
        resp_approve = self.client.post(update_url, {
            'status': 'Confirmed',
            'admin_notes': 'Provisional admission approved. Report on August 10.'
        }, follow=True)
        self.assertEqual(resp_approve.status_code, 200)
        app.refresh_from_db()
        self.assertEqual(app.status, 'Confirmed')
        self.assertEqual(app.admin_notes, 'Provisional admission approved. Report on August 10.')
        self.assertEqual(app.reviewed_by, self.partner_user)

        # 2. Change Decision: Cancel / Reject application
        resp_cancel = self.client.post(update_url, {
            'status': 'Cancelled',
            'admin_notes': 'Document mismatch detected during board verification.'
        }, follow=True)
        self.assertEqual(resp_cancel.status_code, 200)
        app.refresh_from_db()
        self.assertEqual(app.status, 'Cancelled')
        self.assertEqual(app.admin_notes, 'Document mismatch detected during board verification.')

        # 3. Change Decision again: Reset to Pending for re-evaluation
        resp_pending = self.client.post(update_url, {
            'status': 'Pending',
            'admin_notes': 'Candidate submitted revised marksheet. Re-verifying.'
        }, follow=True)
        self.assertEqual(resp_pending.status_code, 200)
        app.refresh_from_db()
        self.assertEqual(app.status, 'Pending')
        self.assertEqual(app.admin_notes, 'Candidate submitted revised marksheet. Re-verifying.')

    def test_admin_moderation_college_status_reset_and_toggle(self):
        self.client.login(username="super_mod", password="AdminPassword123!")

        # 1. Reject college
        reject_url = reverse('admin_reject_college', kwargs={'college_id': self.college.id})
        resp_reject = self.client.post(reject_url, {'admin_notes': 'Accreditation query'}, follow=True)
        self.assertEqual(resp_reject.status_code, 200)
        self.college.refresh_from_db()
        self.assertEqual(self.college.status, 'Rejected')

        # 2. Reset college to Pending
        reset_url = reverse('admin_reset_college', kwargs={'college_id': self.college.id})
        resp_reset = self.client.post(reset_url, {'admin_notes': 'Partner submitted compliance details'}, follow=True)
        self.assertEqual(resp_reset.status_code, 200)
        self.college.refresh_from_db()
        self.assertEqual(self.college.status, 'Pending')

        # 3. Approve college again
        approve_url = reverse('admin_approve_college', kwargs={'college_id': self.college.id})
        resp_approve = self.client.post(approve_url, {'admin_notes': 'Compliance verified'}, follow=True)
        self.assertEqual(resp_approve.status_code, 200)
        self.college.refresh_from_db()
        self.assertEqual(self.college.status, 'Approved')


class SidebarRoleNavAndFilterModalTests(TestCase):
    """
    Test suite for:
    1. Strict email uniqueness across registrations.
    2. Login via email or username with strict role redirection to partner dashboard.
    3. Multi-field search filters (city, course, max_fee) on college_list.
    4. Rapid course creation (course_add_view) supporting 'next' parameter.
    5. Course categorization by department headlines in context processor.
    """
    def setUp(self):
        self.client = Client()
        self.university = University.objects.create(name="Karnataka Technological University", state="Karnataka", established_year=1995)
        self.college = College.objects.create(
            university=self.university,
            name="SVR College of Technology & Management",
            city="Bangalore",
            fees=Decimal('85000.00'),
            rating=Decimal('4.5'),
            status='Approved',
            min_10th_percentage=Decimal('60.00'),
            min_12th_percentage=Decimal('60.00'),
        )
        self.course_bcom = Course.objects.create(
            college=self.college,
            name="B.Com in Banking and Insurance",
            duration_years=3,
            fee=Decimal('55000.00'),
            seats=60,
        )
        self.course_btech = Course.objects.create(
            college=self.college,
            name="B.Tech Computer Science & Engineering",
            duration_years=4,
            fee=Decimal('120000.00'),
            seats=120,
        )

        # University Partner user
        self.uni_user = User.objects.create_user(
            username="svr_admin",
            email="admin@svr.edu.in",
            password="PartnerPassword123!"
        )
        self.uni_user.profile.role = 'university'
        self.uni_user.profile.organization_name = 'SVR Group of Institutions'
        self.uni_user.profile.save()
        self.college.submitted_by = self.uni_user
        self.college.admin_email = "admin@svr.edu.in"
        self.college.save()

    def test_strict_email_uniqueness_in_registration_form(self):
        """Disallows creating another account with the same email (case-insensitive)."""
        form = CustomUserRegistrationForm(data={
            'username': 'new_user_attempt',
            'email': 'Admin@Svr.Edu.In',  # Same as self.uni_user in different casing
            'role': 'student',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn("An account with this email address already exists", form.errors['email'][0])

    def test_login_via_email_address_and_role_redirect(self):
        """User can log in using their email directly on university portal and is routed to university dashboard."""
        resp = self.client.post(f"{reverse('login')}?role=university", {
            'username': 'admin@svr.edu.in',  # using email
            'password': 'PartnerPassword123!',
            'portal_role': 'university',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('university_dashboard'), resp.url)

    def test_university_partner_cannot_login_in_student_portal(self):
        """University partners are blocked from logging in via the student login portal."""
        resp = self.client.post(f"{reverse('login')}?role=student", {
            'username': 'admin@svr.edu.in',
            'password': 'PartnerPassword123!',
            'portal_role': 'student',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Access Denied: This login portal is for Students only")

    def test_student_cannot_login_in_university_portal(self):
        """Students are blocked from logging in via the university login portal."""
        student_user = User.objects.create_user(username="alex_student", email="alex@student.com", password="StudentPass123!")
        student_user.profile.role = 'student'
        student_user.profile.save()

        resp = self.client.post(f"{reverse('login')}?role=university", {
            'username': 'alex_student',
            'password': 'StudentPass123!',
            'portal_role': 'university',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Access Denied: This login portal is for University Partners only")

    def test_admin_staff_cannot_login_in_student_portal_and_must_use_admin_portal(self):
        """Admin/staff users attempting student portal are rejected; must use admin tab."""
        admin_user = User.objects.create_superuser(username="admin_super", email="admin@clue.org", password="SuperAdmin123!")
        # Attempt student portal -> rejected
        resp_student = self.client.post(f"{reverse('login')}?role=student", {
            'username': 'admin_super',
            'password': 'SuperAdmin123!',
            'portal_role': 'student',
        })
        self.assertEqual(resp_student.status_code, 200)
        self.assertContains(resp_student, "Access Denied: This login portal is for Students only")

        # Use admin portal -> success
        resp_admin = self.client.post(f"{reverse('login')}?role=admin", {
            'username': 'admin_super',
            'password': 'SuperAdmin123!',
            'portal_role': 'admin',
        })
        self.assertEqual(resp_admin.status_code, 302)
        self.assertIn(reverse('admin_moderation'), resp_admin.url)

    def test_navbar_and_sidebar_role_presentation(self):
        """Navbar hides search & filter for partners; sidebar has no submit new campus link."""
        self.client.login(username="svr_admin", password="PartnerPassword123!")
        resp = self.client.get(reverse('university_dashboard'))
        self.assertEqual(resp.status_code, 200)
        # Search bar and filter button hidden for university partner
        self.assertNotContains(resp, 'id="navCollegeSearchInput"')
        self.assertNotContains(resp, 'data-bs-target="#searchFilterModal"')
        # Submit New Campus removed from sidebar
        self.assertNotContains(resp, 'Submit New Campus')


    def test_college_list_filters_by_city_course_and_budget(self):
        """Search filter modal parameters (city, course, max_fee) filter college directory."""
        # Match Bangalore
        resp_city = self.client.get(reverse('college_list'), {'city': 'Bangalore'})
        self.assertEqual(resp_city.status_code, 200)
        self.assertIn(self.college, resp_city.context['colleges'])

        # Non-matching city
        resp_nomatch = self.client.get(reverse('college_list'), {'city': 'Hyderabad'})
        self.assertEqual(resp_nomatch.status_code, 200)
        self.assertNotIn(self.college, resp_nomatch.context['colleges'])

        # Filter by course name
        resp_course = self.client.get(reverse('college_list'), {'course': 'Banking'})
        self.assertEqual(resp_course.status_code, 200)
        self.assertIn(self.college, resp_course.context['colleges'])

        # Filter by tuition budget max_fee
        resp_budget_low = self.client.get(reverse('college_list'), {'max_fee': '50000'})
        self.assertEqual(resp_budget_low.status_code, 200)
        self.assertNotIn(self.college, resp_budget_low.context['colleges'])

        resp_budget_high = self.client.get(reverse('college_list'), {'max_fee': '100000'})
        self.assertEqual(resp_budget_high.status_code, 200)
        self.assertIn(self.college, resp_budget_high.context['colleges'])

    def test_quick_add_course_with_next_redirect(self):
        """University partner can quickly add a course and be redirected to next parameter."""
        self.client.login(username="svr_admin", password="PartnerPassword123!")
        add_url = reverse('course_add', kwargs={'college_id': self.college.id})
        
        post_data = {
            'name': 'B.Com Honors in Financial Analytics',
            'fee': '75000.00',
            'duration_years': 3,
            'seats': 50,
            'next': '/campuses/',
        }
        resp = self.client.post(add_url, post_data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/campuses/')

        course = Course.objects.get(name='B.Com Honors in Financial Analytics', college=self.college)
        self.assertEqual(course.fee, Decimal('75000.00'))
        self.assertEqual(course.seats, 50)

    def test_context_processor_headlines_grouping(self):
        """Context processor organizes courses into department headlines."""
        from core.context_processors import group_courses_by_headline
        courses = [self.course_bcom, self.course_btech]
        headlines = group_courses_by_headline(courses)

        eng_headline = next(h for h in headlines if h['id'] == 'eng')
        comm_headline = next(h for h in headlines if h['id'] == 'comm')

        self.assertIn(self.course_btech, eng_headline['courses'])
        self.assertIn(self.course_bcom, comm_headline['courses'])


class CompareToggleAndCollegeEmailTests(TestCase):
    def setUp(self):
        self.partner_user = User.objects.create_user(
            username="svr_head",
            email="admin@svr.edu.in",
            password="PartnerPassword123!"
        )
        self.partner_profile = self.partner_user.profile
        self.partner_profile.role = "university"
        self.partner_profile.organization_name = "SVR Group of Institutions"
        self.partner_profile.save()
        self.university = University.objects.create(
            name="SVR University",
            city="Bangalore",
            state="Karnataka",
            established_year=1998,
            rating=Decimal("4.5"),
            website="https://svr.edu.in"
        )
        self.colleges = [
            College.objects.create(
                university=self.university,
                name=f"SVR Institute of Technology {i}",
                city="Bangalore",
                fees=Decimal("120000.00"),
                rating=Decimal("4.2"),
                status="Approved",
                submitted_by=self.partner_user,
                admin_email=f"contact{i}@svr.edu.in"
            )
            for i in range(1, 6)
        ]

    def test_college_email_domain_property(self):
        """College email domain is correctly derived from admin_email or university website."""
        col1 = self.colleges[0]
        self.assertEqual(col1.email_domain, "svr.edu.in")

        # Test fallback from website
        col_no_email = College.objects.create(
            university=self.university,
            name="Alliance School of Business",
            city="Bangalore",
            fees=Decimal("150000.00"),
            rating=Decimal("4.4"),
            status="Approved"
        )
        self.assertEqual(col_no_email.email_domain, "svr.edu.in")

    def test_compare_toggle_ajax_add_and_remove(self):
        """Toggling compare via AJAX returns JSON without reloads or screen shaking."""
        c1 = self.colleges[0]
        toggle_url = reverse('compare_toggle', kwargs={'college_id': c1.id})

        # 1. First click: Add to compare
        resp = self.client.get(toggle_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'added')
        self.assertTrue(data['is_in_compare'])
        self.assertEqual(data['count'], 1)
        self.assertIn(c1.id, self.client.session.get('compare_colleges', []))

        # 2. Second click: Remove from compare
        resp2 = self.client.get(toggle_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertTrue(data2['success'])
        self.assertEqual(data2['status'], 'removed')
        self.assertFalse(data2['is_in_compare'])
        self.assertEqual(data2['count'], 0)
        self.assertNotIn(c1.id, self.client.session.get('compare_colleges', []))

    def test_compare_maximum_4_colleges_limit(self):
        """Cannot compare more than 4 colleges at a time; 5th addition returns limit_reached."""
        for c in self.colleges[:4]:
            resp = self.client.get(reverse('compare_toggle', kwargs={'college_id': c.id}), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()['status'], 'added')

        session_list = self.client.session.get('compare_colleges', [])
        self.assertEqual(len(session_list), 4)

        # Attempt to add a 5th college
        c5 = self.colleges[4]
        resp5 = self.client.get(reverse('compare_toggle', kwargs={'college_id': c5.id}), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp5.status_code, 200)
        data5 = resp5.json()
        self.assertFalse(data5['success'])
        self.assertEqual(data5['status'], 'limit_reached')
        self.assertFalse(data5['is_in_compare'])
        self.assertEqual(data5['count'], 4)
        self.assertIn("Maximum 4 colleges", data5['message'])
        self.assertNotIn(c5.id, self.client.session.get('compare_colleges', []))

    def test_college_email_creation_and_partner_user_provisioning(self):
        """University partner can create college-domain emails and automatically provisions partner user."""
        self.client.login(username="svr_head", password="PartnerPassword123!")
        col = self.colleges[0]
        team_url = reverse('college_team', kwargs={'college_id': col.id})

        # Add member using department prefix 'admissions'
        post_data = {
            'action': 'add_member',
            'staff_email': 'admissions',
        }
        resp = self.client.post(team_url, post_data, follow=True)
        self.assertEqual(resp.status_code, 200)

        # Verify college team member has domain appended
        from core.models import CollegeTeamMember
        member = CollegeTeamMember.objects.get(college=col, email="admissions@svr.edu.in")
        self.assertIsNotNone(member)
        self.assertIsNotNone(member.user)
        self.assertEqual(member.user.email, "admissions@svr.edu.in")
        self.assertEqual(member.user.profile.role, "university")


class StudentEmailOTPVerificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        mail.outbox.clear()

    def test_send_registration_otp_success_and_email_dispatched(self):
        """Student can request OTP, email is dispatched, and OTP record is created."""
        send_url = reverse('send_registration_otp')
        post_data = {
            'email': 'rahul_student@example.com',
            'username': 'rahul_student',
        }
        resp = self.client.post(
            send_url,
            data=json.dumps(post_data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertIn("A 6-digit OTP code has been sent", data['message'])

        # Check that email was dispatched
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEqual(sent_mail.to, ['rahul_student@example.com'])
        self.assertIn("Your CollegeClue Student Verification Code", sent_mail.subject)

        # Check OTP database record
        otp_rec = EmailVerificationOTP.objects.filter(email='rahul_student@example.com').first()
        self.assertIsNotNone(otp_rec)
        self.assertFalse(otp_rec.is_verified)
        self.assertEqual(len(otp_rec.otp_code), 6)
        self.assertIn(otp_rec.otp_code, sent_mail.body)

    def test_send_registration_otp_duplicate_email_rejected(self):
        """Cannot request OTP with an email that is already registered."""
        User.objects.create_user(
            username="existing_user",
            email="existing@example.com",
            password="Password123!"
        )
        send_url = reverse('send_registration_otp')
        resp = self.client.post(
            send_url,
            data=json.dumps({'email': 'existing@example.com', 'username': 'new_person'}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data['success'])
        self.assertIn("already exists", data['message'])
        self.assertEqual(len(mail.outbox), 0)

    def test_verify_registration_otp_valid_and_invalid(self):
        """Invalid OTP is rejected; correct OTP marks verification and session."""
        # 1. Dispatch OTP
        self.client.post(
            reverse('send_registration_otp'),
            data=json.dumps({'email': 'priya_student@example.com', 'username': 'priya'}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        otp_rec = EmailVerificationOTP.objects.get(email='priya_student@example.com')
        correct_otp = otp_rec.otp_code

        verify_url = reverse('verify_registration_otp')

        # 2. Test incorrect code
        resp_bad = self.client.post(
            verify_url,
            data=json.dumps({'email': 'priya_student@example.com', 'otp': '000000'}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(resp_bad.status_code, 400)
        self.assertFalse(resp_bad.json()['success'])
        otp_rec.refresh_from_db()
        self.assertFalse(otp_rec.is_verified)

        # 3. Test correct code
        resp_good = self.client.post(
            verify_url,
            data=json.dumps({'email': 'priya_student@example.com', 'otp': correct_otp}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(resp_good.status_code, 200)
        self.assertTrue(resp_good.json()['success'])
        otp_rec.refresh_from_db()
        self.assertTrue(otp_rec.is_verified)
        self.assertEqual(self.client.session.get('verified_student_email'), 'priya_student@example.com')

    def test_student_registration_blocked_without_otp_verification(self):
        """Student registration form is rejected if email was not verified via OTP."""
        reg_url = reverse('register') + '?role=student'
        form_data = {
            'role': 'student',
            'username': 'unverified_student',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'email': 'unverified@example.com',
        }
        resp = self.client.post(reg_url, form_data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Email verification required")
        self.assertFalse(User.objects.filter(username='unverified_student').exists())

    def test_student_registration_with_verified_otp_creates_user_and_redirects_to_student_login(self):
        """When OTP is verified, student account is created and redirected to student login page."""
        # 1. Send and verify OTP
        self.client.post(
            reverse('send_registration_otp'),
            data=json.dumps({'email': 'verified_student@example.com', 'username': 'verified_student'}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        otp_rec = EmailVerificationOTP.objects.get(email='verified_student@example.com')
        self.client.post(
            reverse('verify_registration_otp'),
            data=json.dumps({'email': 'verified_student@example.com', 'otp': otp_rec.otp_code}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # 2. Submit student registration
        reg_url = reverse('register') + '?role=student'
        form_data = {
            'role': 'student',
            'username': 'verified_student',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'email': 'verified_student@example.com',
        }
        resp = self.client.post(reg_url, form_data)

        # 3. Assert redirected directly to student login page
        expected_redirect = reverse('login') + '?role=student'
        self.assertRedirects(resp, expected_redirect)

        # 4. Assert user and student profile created
        user = User.objects.get(username='verified_student')
        self.assertEqual(user.email, 'verified_student@example.com')
        self.assertEqual(user.profile.role, 'student')

    def test_partner_registration_unaffected_by_student_otp(self):
        """University partner registration proceeds normally without requiring student OTP."""
        reg_url = reverse('register') + '?role=university'
        form_data = {
            'role': 'university',
            'username': 'uni_partner_demo',
            'first_name': 'Dean',
            'last_name': 'Office',
            'password1': 'PartnerPass123!',
            'password2': 'PartnerPass123!',
            'email': 'dean_demo@alliance.edu.in',
            'organization_name': 'Alliance University',
        }
        resp = self.client.post(reg_url, form_data)
        self.assertRedirects(resp, reverse('university_dashboard'))

        user = User.objects.get(username='uni_partner_demo')
        self.assertEqual(user.profile.role, 'university')


class NearbyPgFlatsSearchAndFilterTests(TestCase):
    def setUp(self):
        self.uni = University.objects.create(
            name="Premier Tech University",
            city="Bangalore",
            state="Karnataka",
            established_year=2000,
            description="Premier University"
        )
        self.college1 = College.objects.create(
            university=self.uni,
            name="School of Computing",
            city="Bangalore",
            fees=120000,
            description="Top computing college",
            status="Approved"
        )
        self.college2 = College.objects.create(
            university=self.uni,
            name="Delhi Institute of Science",
            city="New Delhi",
            fees=90000,
            description="Top science college",
            status="Approved"
        )
        self.pg1 = Accommodation.objects.create(
            name="Green Valley Student PG",
            type="PG",
            college=self.college1,
            city="Bangalore",
            address="Koramangala 4th Block",
            rent=6000,
            room_type="Single",
            facilities="Wi-Fi, Food, Power Backup",
            contact_phone="9988776655",
            contact_email="gv@example.com",
            is_available=True,
            status="Approved"
        )
        self.flat1 = Accommodation.objects.create(
            name="Palm Meadows 2BHK Flat",
            type="Flat",
            college=self.college1,
            city="Bangalore",
            address="Whitefield",
            rent=12000,
            room_type="Double",
            facilities="Furnished 2BHK, Wi-Fi, Security",
            contact_phone="9988776644",
            contact_email="pm@example.com",
            is_available=True,
            status="Approved"
        )
        self.hostel1 = Accommodation.objects.create(
            name="Campus Scholars Hostel",
            type="Hostel",
            college=self.college2,
            city="New Delhi",
            address="North Campus",
            rent=4500,
            room_type="Triple",
            facilities="Hostel Mess, Library",
            contact_phone="9988776633",
            contact_email="cs@example.com",
            is_available=True,
            status="Approved"
        )

    def test_nearby_pgs_navbar_search_hidden_and_page_search_bar_present(self):
        resp = self.client.get(reverse('accommodation_list'))
        self.assertEqual(resp.status_code, 200)
        # Navbar search bar is hidden
        self.assertNotContains(resp, 'id="navCollegeSearchInput"')
        # On-page search bar is present
        self.assertContains(resp, 'name="q"')
        self.assertContains(resp, 'data-bs-target="#pgFilterModal"')
        self.assertContains(resp, 'Near by PG/Flats')

    def test_home_page_navbar_search_is_present(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'id="navCollegeSearchInput"')

    def test_filter_by_college(self):
        resp = self.client.get(reverse('accommodation_list'), {'college': self.college1.id})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.pg1, resp.context['accommodations'])
        self.assertIn(self.flat1, resp.context['accommodations'])
        self.assertNotIn(self.hostel1, resp.context['accommodations'])

    def test_filter_by_room_type(self):
        resp = self.client.get(reverse('accommodation_list'), {'room_type': 'Single'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.pg1, resp.context['accommodations'])
        self.assertNotIn(self.flat1, resp.context['accommodations'])

    def test_filter_by_price_range(self):
        resp = self.client.get(reverse('accommodation_list'), {'min_rent': '5000', 'max_rent': '8000'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.pg1, resp.context['accommodations'])
        self.assertNotIn(self.flat1, resp.context['accommodations'])
        self.assertNotIn(self.hostel1, resp.context['accommodations'])

    def test_search_by_query_text(self):
        resp = self.client.get(reverse('accommodation_list'), {'q': 'Flat'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.flat1, resp.context['accommodations'])
        self.assertNotIn(self.pg1, resp.context['accommodations'])


class CollegeDetailInsightsAndNewAppRedirectionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.uni = University.objects.create(
            name="Apex National University",
            city="Bengaluru",
            state="Karnataka",
            established_year=2000,
            rating=Decimal("4.6")
        )
        self.college = College.objects.create(
            university=self.uni,
            name="Apex Institute of Technology",
            city="Bengaluru",
            fees=Decimal("200000.00"),
            rating=Decimal("4.7"),
            status='Approved',
            admin_email="admissions@ait.edu.in",
            min_10th_percentage=Decimal("60.00"),
            min_12th_percentage=Decimal("65.00")
        )
        self.course = Course.objects.create(
            college=self.college,
            name="B.Tech Computer Science & AI",
            duration_years=4,
            fee=Decimal("200000.00"),
            seats=120
        )
        self.student = User.objects.create_user(
            username="test_student_user",
            email="teststudent@example.com",
            password="Password123!"
        )

    def test_new_college_application_button_redirects_to_university_list(self):
        self.client.login(username="test_student_user", password="Password123!")
        resp = self.client.get(reverse('my_applications'))
        self.assertEqual(resp.status_code, 200)
        # Verify the "New College Application" button links to university_list
        expected_url = reverse('university_list')
        self.assertContains(resp, f'href="{expected_url}"')
        self.assertContains(resp, "New College Application")

    def test_college_detail_renders_all_four_required_sections(self):
        resp = self.client.get(reverse('college_detail', kwargs={'slug': self.college.slug}))
        self.assertEqual(resp.status_code, 200)

        # 1. About College
        self.assertContains(resp, "About College")
        self.assertContains(resp, f"About {self.college.name}")
        self.assertContains(resp, "Campus &amp; Academic Focus Highlights")
        self.assertContains(resp, "Accreditations &amp; Recognition")

        # 2. About Courses
        self.assertContains(resp, "About Courses")
        self.assertContains(resp, "B.Tech Computer Science &amp; AI")
        self.assertContains(resp, "120 Seats")

        # 3. About Placements
        self.assertContains(resp, "About Placements")
        self.assertContains(resp, "Highest Package (CTC)")
        self.assertContains(resp, "Average Package (CTC)")
        self.assertContains(resp, "Placement Success")

        # 4. About Companies Came
        self.assertContains(resp, "About Companies Came")
        self.assertContains(resp, "Google")
        self.assertContains(resp, "Microsoft")
        self.assertContains(resp, "Deloitte")
        self.assertContains(resp, "Tata Consultancy Services (TCS)")
        self.assertContains(resp, "Tier 1 Tech &amp; Product Companies")


class UniversityEnhancementsAndHousingFilterTests(TestCase):
    def setUp(self):
        self.partner_user = User.objects.create_user(
            username="partner_admin",
            email="partner@iitd.ac.in",
            password="PartnerPass123!"
        )
        self.partner_user.profile.role = "university"
        self.partner_user.profile.save()

        self.uni_a = University.objects.create(
            name="Apex University Delhi",
            city="New Delhi",
            state="Delhi",
            established_year=1995,
            rating=Decimal("4.8"),
            website="https://apexdelhi.edu.in",
            gmap_location="28.5450, 77.1926"
        )
        self.uni_b = University.objects.create(
            name="Capital University Delhi",
            city="New Delhi",
            state="Delhi",
            established_year=2005,
            rating=Decimal("4.1"),
            website="https://capitaldelhi.edu.in"
        )

        self.college_a = College.objects.create(
            university=self.uni_a,
            name="Apex Institute of Technology",
            city="New Delhi",
            fees=Decimal("180000.00"),
            rating=Decimal("4.7"),
            status="Approved",
            submitted_by=self.partner_user,
            admin_email="partner@iitd.ac.in",
            gmap_location="https://maps.google.com/?q=28.5450,77.1926"
        )
        self.college_b = College.objects.create(
            university=self.uni_b,
            name="Capital College of Management",
            city="New Delhi",
            fees=Decimal("140000.00"),
            rating=Decimal("4.0"),
            status="Approved"
        )

        # Accommodation strictly affiliated with Uni A's college
        self.acc_a = Accommodation.objects.create(
            name="Apex Scholars Hostel",
            type="Hostel",
            college=self.college_a,
            city="New Delhi",
            address="Near Gate 2, Apex Tech Campus",
            rent=Decimal("8000.00"),
            room_type="Single",
            status="Approved",
            is_available=True
        )

        # Accommodation affiliated with Uni B's college (same city)
        self.acc_b = Accommodation.objects.create(
            name="Capital Executive PG",
            type="PG",
            college=self.college_b,
            city="New Delhi",
            address="Near Capital Management Campus",
            rent=Decimal("7500.00"),
            room_type="Double",
            status="Approved",
            is_available=True
        )

    def test_course_optional_url_model_form_and_views(self):
        """Course link / syllabus URL is optional, saves properly, and is displayed on details."""
        # 1. Course with optional URL
        course_with_url = Course.objects.create(
            college=self.college_a,
            name="B.Tech Artificial Intelligence",
            duration_years=4,
            fee=Decimal("190000.00"),
            seats=60,
            course_url="https://apexdelhi.edu.in/syllabus/ai-btech"
        )
        # 2. Course without optional URL
        course_without_url = Course.objects.create(
            college=self.college_a,
            name="B.Tech Mechanical Engineering",
            duration_years=4,
            fee=Decimal("170000.00"),
            seats=60
        )
        self.assertEqual(course_with_url.course_url, "https://apexdelhi.edu.in/syllabus/ai-btech")
        self.assertIsNone(course_without_url.course_url)

        # 3. Test CourseForm validation
        form_valid = CourseForm(data={
            'name': 'M.Tech Data Science',
            'duration_years': 2,
            'fee': 220000,
            'seats': 30,
            'course_url': 'https://apexdelhi.edu.in/syllabus/mtech-ds'
        })
        self.assertTrue(form_valid.is_valid())

        form_no_url = CourseForm(data={
            'name': 'M.Tech Robotics',
            'duration_years': 2,
            'fee': 210000,
            'seats': 30,
            'course_url': ''
        })
        self.assertTrue(form_no_url.is_valid())

        # 4. View college_detail displays the URL badge
        resp = self.client.get(reverse('college_detail', kwargs={'slug': self.college_a.slug}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'https://apexdelhi.edu.in/syllabus/ai-btech')
        self.assertContains(resp, 'Syllabus &amp; Curriculum Link')

    def test_universities_page_search_bar_and_filter_modal(self):
        """The /universities/ page displays search bar, filter button, and modal."""
        resp = self.client.get(reverse('university_list'))
        self.assertEqual(resp.status_code, 200)
        # On-page search bar and filter button
        self.assertContains(resp, 'id="universitySearchForm"')
        self.assertContains(resp, 'data-bs-target="#universityFilterModal"')
        self.assertContains(resp, 'id="universityFilterModal"')
        # hide_navbar_search in context
        self.assertTrue(resp.context.get('hide_navbar_search'))

        # Filtering by city
        resp_city = self.client.get(reverse('university_list') + '?city=New+Delhi')
        self.assertContains(resp_city, "Apex University Delhi")
        self.assertContains(resp_city, "Capital University Delhi")

        # Filtering by rating >= 4.5
        resp_rating = self.client.get(reverse('university_list') + '?min_rating=4.5')
        self.assertContains(resp_rating, "Apex University Delhi")
        self.assertNotContains(resp_rating, "Capital University Delhi")

    def test_home_page_removes_filter_button(self):
        """Normal home page does not display the navbar filter button, but other pages do."""
        resp_home = self.client.get(reverse('home'))
        self.assertEqual(resp_home.status_code, 200)
        # Search input is present on home
        self.assertContains(resp_home, 'name="search"')
        # Filter button (#searchFilterModal) is removed on normal home page
        self.assertNotContains(resp_home, 'data-bs-target="#searchFilterModal"')

        # On college list, the filter modal button is present
        resp_colleges = self.client.get(reverse('college_list'))
        self.assertEqual(resp_colleges.status_code, 200)
        self.assertContains(resp_colleges, 'data-bs-target="#searchFilterModal"')

    def test_google_maps_location_selector_and_embed(self):
        """University portal admin can set Google Maps location and it displays on university detail."""
        self.client.force_login(self.partner_user)

        # 1. Update university location via partner endpoint
        update_url = reverse('university_location_update', kwargs={'university_id': self.uni_a.id})
        resp = self.client.post(update_url, {'gmap_location': '28.5450, 77.1926'})
        self.assertEqual(resp.status_code, 302)
        self.uni_a.refresh_from_db()
        self.assertEqual(self.uni_a.gmap_location, '28.5450, 77.1926')

        # 2. University detail displays View on Google Maps button with coordinates
        resp_detail = self.client.get(reverse('university_detail', kwargs={'slug': self.uni_a.slug}))
        self.assertEqual(resp_detail.status_code, 200)
        self.assertContains(resp_detail, "View on Google Maps")
        self.assertContains(resp_detail, "maps.google.com/?q=")
        self.assertContains(resp_detail, "28.5450")
        self.assertContains(resp_detail, "77.1926")
        self.assertNotContains(resp_detail, "Campus Location &amp; Google Map")

    def test_university_detail_strictly_recommends_nearby_pgs(self):
        """University detail strictly shows only PGs near its affiliated colleges."""
        resp_uni_a = self.client.get(reverse('university_detail', kwargs={'slug': self.uni_a.slug}))
        self.assertEqual(resp_uni_a.status_code, 200)

        # Acc A belongs to college_a (under uni_a) -> MUST BE INCLUDED
        self.assertIn(self.acc_a, resp_uni_a.context['accommodations'])
        self.assertContains(resp_uni_a, "Apex Scholars Hostel")

        # Acc B belongs to college_b (under uni_b) -> MUST NOT BE INCLUDED under Uni A
        self.assertNotIn(self.acc_b, resp_uni_a.context['accommodations'])
        self.assertNotContains(resp_uni_a, "Capital Executive PG")

        # Test Uni B detail
        resp_uni_b = self.client.get(reverse('university_detail', kwargs={'slug': self.uni_b.slug}))
        self.assertEqual(resp_uni_b.status_code, 200)
        self.assertIn(self.acc_b, resp_uni_b.context['accommodations'])
        self.assertNotIn(self.acc_a, resp_uni_b.context['accommodations'])


class UniversityPlacementsAndMenuTests(TestCase):
    def setUp(self):
        self.partner_user = User.objects.create_user(
            username="portal_partner",
            email="partner@inst.edu.in",
            password="TestPassword123!"
        )
        self.profile = self.partner_user.profile
        self.profile.role = "university"
        self.profile.organization_name = "Excellence University Group"
        self.profile.save()
        self.university = University.objects.create(
            name="Excellence Central University",
            slug="excellence-central-university",
            city="Bengaluru",
            state="Karnataka",
            rating=Decimal("4.8"),
            established_year=1995,
            website="https://excellence.edu.in"
        )
        self.college = College.objects.create(
            university=self.university,
            name="Faculty of Engineering & Computing",
            slug="faculty-of-engineering-computing",
            city="Bengaluru",
            description="Leading premier technological institute with specialized engineering programs.",
            fees=Decimal("220000.00"),
            rating=Decimal("4.6"),
            status="Approved",
            submitted_by=self.partner_user,
            admin_email="partner@inst.edu.in"
        )
        self.course = Course.objects.create(
            college=self.college,
            name="B.Tech Computer Science & AI",
            duration_years=4,
            fee=Decimal("220000.00"),
            seats=120
        )
        self.accommodation = Accommodation.objects.create(
            name="Serene Campus Stay PG",
            type="PG",
            college=self.college,
            city="Bengaluru",
            rent=Decimal("9500.00"),
            room_type="Double",
            is_available=True,
            status="Approved",
            contact_phone="9876543210"
        )

    def test_menu_bar_removes_colleges_and_campuses(self):
        """Offcanvas sidebar menu does not contain 'Colleges & Campuses', but retains Universities & Nearby PG/Flats."""
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)

        # 'Colleges & Campuses' link is removed from sidebar menu
        self.assertNotContains(resp, 'Colleges &amp; Campuses')
        # Universities and Nearby PG/Flats remain intact
        self.assertContains(resp, 'Universities')
        self.assertContains(resp, 'Near by PG/Flats')

    def test_university_portal_can_edit_and_save_placements(self):
        """University portal admin can edit and publish placement metrics and visiting recruiters."""
        self.client.force_login(self.partner_user)
        edit_url = reverse('college_edit', kwargs={'college_id': self.college.id})

        # Check that the edit page renders the placement controls
        resp_get = self.client.get(edit_url)
        self.assertEqual(resp_get.status_code, 200)
        self.assertContains(resp_get, 'Placement Audit &amp; Recruiter Benchmarks')
        self.assertContains(resp_get, 'id="btnAutoCalculate"')
        self.assertContains(resp_get, 'id_highest_package')
        self.assertContains(resp_get, 'id_average_package')
        self.assertContains(resp_get, 'id_top_recruiters')

        # Submit updated placement details
        post_data = {
            'name': self.college.name,
            'city': self.college.city,
            'fees': '220000.00',
            'rating': '4.6',
            'min_10th_percentage': '60.00',
            'min_12th_percentage': '65.00',
            'highest_package': '₹52.00 LPA',
            'average_package': '₹18.50 LPA',
            'median_package': '₹15.00 LPA',
            'placement_rate': '97.6%',
            'total_offers': '920+',
            'summer_stipend': '₹95,000 / mo',
            'top_recruiters': 'Google, Microsoft, Amazon, Adobe, McKinsey & Company',
            'placement_highlights': '100% placement assistance facilitated by Corporate Relations.\nOver 48% PPOs converted from summer internships.',
            'facilities': 'Modern computing clusters, robotics lab, incubation center',
            'description': 'Updated premier computing campus.'
        }
        resp_post = self.client.post(edit_url, post_data)
        self.assertEqual(resp_post.status_code, 302)

        self.college.refresh_from_db()
        self.assertEqual(self.college.highest_package, '₹52.00 LPA')
        self.assertEqual(self.college.average_package, '₹18.50 LPA')
        self.assertEqual(self.college.median_package, '₹15.00 LPA')
        self.assertEqual(self.college.placement_rate, '97.6%')
        self.assertEqual(self.college.total_offers, '920+')
        self.assertEqual(self.college.summer_stipend, '₹95,000 / mo')
        self.assertIn('Google', self.college.top_recruiters)
        self.assertIn('Over 48% PPOs', self.college.placement_highlights)

    def test_college_insights_uses_custom_and_fallback_calculation(self):
        """College insights prioritize custom saved values and fallback to auto-calculation when blank."""
        from core.college_insights import get_college_placements, get_college_companies

        # 1. Custom values provided
        self.college.highest_package = '₹60.00 LPA'
        self.college.average_package = '₹22.00 LPA'
        self.college.placement_rate = '99.1%'
        self.college.save()

        custom_stats = get_college_placements(self.college)
        self.assertEqual(custom_stats['highest_ctc'], '₹60.00 LPA')
        self.assertEqual(custom_stats['average_ctc'], '₹22.00 LPA')
        self.assertEqual(custom_stats['placement_rate'], '99.1%')

        # 2. When blank, automatically calculates realistic benchmarks
        self.college.highest_package = ''
        self.college.average_package = ''
        self.college.placement_rate = ''
        self.college.save()

        calc_stats = get_college_placements(self.college)
        self.assertTrue(len(calc_stats['highest_ctc']) > 0)
        self.assertTrue('LPA' in calc_stats['highest_ctc'])
        self.assertTrue('LPA' in calc_stats['average_ctc'])
        self.assertTrue('%' in calc_stats['placement_rate'])

        # 3. Custom companies list parsing
        self.college.top_recruiters = 'Google, Deloitte, InnovateTech'
        companies_cats = get_college_companies(self.college)
        all_comp_names = [comp['name'] for cat in companies_cats for comp in cat['companies']]
        self.assertIn('Google', all_comp_names)
        self.assertIn('Deloitte', all_comp_names)
        self.assertIn('InnovateTech', all_comp_names)

    def test_accommodation_list_links_near_college_to_college_detail(self):
        """On Near by PG/Flats list, the 'Near [College]' tag links directly to college_detail."""
        resp = self.client.get(reverse('accommodation_list'))
        self.assertEqual(resp.status_code, 200)
        expected_url = reverse('college_detail', kwargs={'slug': self.college.slug})
        self.assertContains(resp, f'href="{expected_url}"')
        self.assertContains(resp, 'Near Faculty of Engineering')

    def test_college_detail_view_renders_all_tabs_and_insights(self):
        """Detail profile view renders all 5 tabs and placement figures."""
        detail_url = reverse('college_detail', kwargs={'slug': self.college.slug})
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, 200)

        # Tab navigation items
        self.assertContains(resp, 'About College')
        self.assertContains(resp, 'About Courses')
        self.assertContains(resp, 'About Placements')
        self.assertContains(resp, 'About Companies Came')
        self.assertContains(resp, 'Nearby PG / Flats')

        # Placement stats
        self.assertContains(resp, 'Highest Package (CTC)')
        self.assertContains(resp, 'Average Package (CTC)')
        self.assertContains(resp, 'Median Package')
        self.assertContains(resp, 'Total Job Offers')

    def test_university_list_youtube_style_search_and_filter_dropdowns(self):
        """University list page renders YouTube-style search, pill row, and 3 filter dropdowns."""
        resp = self.client.get(reverse('university_list'))
        self.assertEqual(resp.status_code, 200)

        # 1. YouTube-style search bar and beside Filter button
        self.assertContains(resp, 'id="universitySearchForm"')
        self.assertContains(resp, 'Search universities, courses, campuses, or locations...')
        self.assertContains(resp, 'data-bs-target="#universityFilterModal"')
        self.assertContains(resp, 'Filter')

        # 2. Category pill row
        self.assertContains(resp, 'Engineering &amp; B.Tech')
        self.assertContains(resp, 'Management &amp; MBA')
        self.assertContains(resp, 'Computer &amp; AI')

        # 3. Filter modal with 3 dropdown selects
        self.assertContains(resp, 'id="modalUniLocation"')
        self.assertContains(resp, 'id="modalUniCourseType"')
        self.assertContains(resp, 'id="modalUniBudget"')

        # 4. Direct college profile link on university card
        college_url = reverse('college_detail', kwargs={'slug': self.college.slug})
        self.assertContains(resp, f'href="{college_url}"')
        self.assertContains(resp, 'View College Profile')

    def test_university_list_filtering_by_location_course_and_budget(self):
        """University list filters properly by location, course_type, and budget."""
        # Setup another university & college with different attributes
        other_uni = University.objects.create(
            name="Mumbai Business University",
            slug="mumbai-business-university",
            city="Mumbai",
            state="Maharashtra",
            rating=Decimal("4.6"),
            established_year=1990
        )
        mgmt_college = College.objects.create(
            university=other_uni,
            name="Mumbai School of Management",
            slug="mumbai-school-of-management",
            city="Mumbai",
            fees=Decimal("380000.00"),
            rating=Decimal("4.6"),
            status='Approved'
        )
        Course.objects.create(
            college=mgmt_college,
            name="MBA in Strategic Leadership",
            fee=Decimal("380000.00"),
            duration_years=2
        )

        # Test location filter
        resp_loc = self.client.get(reverse('university_list'), {'location': 'Mumbai'})
        self.assertEqual(resp_loc.status_code, 200)
        self.assertContains(resp_loc, 'Mumbai Business University')
        self.assertNotContains(resp_loc, 'Test State University')

        # Test course_type filter
        resp_course = self.client.get(reverse('university_list'), {'course_type': 'management'})
        self.assertEqual(resp_course.status_code, 200)
        self.assertContains(resp_course, 'Mumbai Business University')

        # Test budget filter
        resp_budget = self.client.get(reverse('university_list'), {'budget': 'above_350k'})
        self.assertEqual(resp_budget.status_code, 200)
        self.assertContains(resp_budget, 'Mumbai Business University')

    def test_university_detail_omits_map_iframe_and_affiliated_colleges(self):
        """University detail view does not embed Google Map iframe or affiliated colleges list."""
        uni_url = reverse('university_detail', kwargs={'slug': self.university.slug})
        resp = self.client.get(uni_url)
        self.assertEqual(resp.status_code, 200)

        # Does NOT have embedded Google Map iframe card
        self.assertNotContains(resp, '<iframe')
        self.assertNotContains(resp, 'Campus Location &amp; Google Map')

        # Keeps View on Google Maps button
        self.assertContains(resp, 'View on Google Maps')

        # Does NOT have Affiliated Colleges list
        self.assertNotContains(resp, 'Affiliated Colleges &amp; Faculties')


class SidebarAndUnregisteredCollegeDetailTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.university = University.objects.create(
            name="Apex University",
            slug="apex-university",
            city="Pune",
            state="Maharashtra",
            established_year=1998,
            rating=Decimal("4.5"),
            gmap_location="https://maps.google.com/?q=Apex+University+Pune"
        )
        self.registered_college = College.objects.create(
            university=self.university,
            name="Apex Engineering College",
            slug="apex-engineering-college",
            city="Pune",
            fees=Decimal("120000.00"),
            rating=Decimal("4.6"),
            admin_email="admin@apex.edu",
            status="Approved"
        )
        self.unregistered_college = College.objects.create(
            university=self.university,
            name="Apex Institute of Pharmacy",
            slug="apex-institute-of-pharmacy",
            city="Pune",
            fees=Decimal("80000.00"),
            rating=Decimal("4.1"),
            admin_email="",
            submitted_by=None,
            status="Approved"
        )
        self.uni_user = User.objects.create_user(
            username="partner_admin",
            email="partner@apex.edu",
            password="password123",
            first_name="PartnerAdmin"
        )
        self.uni_user.profile.role = 'university'
        self.uni_user.profile.organization_name = 'Apex University System'
        self.uni_user.profile.save()
        self.registered_college.submitted_by = self.uni_user
        self.registered_college.save()

        self.acc_user = User.objects.create_user(
            username="acc_provider",
            email="housing@example.com",
            password="password123",
            first_name="HostelManager"
        )
        self.acc_user.profile.role = 'accommodation'
        self.acc_user.profile.organization_name = 'Pune Student Stays'
        self.acc_user.profile.save()

    def test_unregistered_college_action_bar_and_open_soon_alert(self):
        """College with closed admissions displays Application Unavailable, View on Google Maps, and Application will be open Soon alert."""
        self.unregistered_college.admissions_status = 'Closed'
        self.unregistered_college.save()
        url = reverse('college_detail', kwargs={'slug': self.unregistered_college.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # Has Application Unavailable button
        self.assertContains(resp, 'Application Unavailable')

        # Has View University Location button beside it
        self.assertContains(resp, 'View University Location')

        # Does NOT have Nearby PGs in admission action bar
        self.assertNotContains(resp, 'Nearby PGs (')

        # Clean alert below action bar
        self.assertContains(resp, 'Application will be open Soon')

    def test_university_dashboard_has_no_submit_new_college(self):
        """University dashboard has removed 'Submit New College' and 'Review Applications' button from header."""
        self.client.login(username="partner_admin", password="password123")
        resp = self.client.get(reverse('university_dashboard'))
        self.assertEqual(resp.status_code, 200)

        # Should not contain Submit New College
        self.assertNotContains(resp, 'Submit New College')
        self.assertNotContains(resp, 'Submit Your College')

        # Header banner should NOT contain Review Applications button
        self.assertNotContains(resp, 'Review Applications')

        # Should contain Create New Course / Program trigger
        self.assertContains(resp, 'Create New Course / Program')

        # User dropdown in navbar should only have Log Out (not Campus Dashboard or Admissions Hub)
        self.assertContains(resp, reverse('logout'))

    def test_admin_can_have_only_one_university_to_create(self):
        """A university admin is limited to managing only 1 university/college; cannot create another."""
        self.client.login(username="partner_admin", password="password123")
        # partner_admin already administers self.registered_college
        resp = self.client.get(reverse('college_submit'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('university_dashboard'))

        # Dashboard limits administered_universities to 1
        dash_resp = self.client.get(reverse('university_dashboard'))
        self.assertEqual(dash_resp.context['administered_universities'].count(), 1)
        self.assertEqual(dash_resp.context['submitted_colleges'].count(), 1)

    def test_university_partner_sidebar_dedicated_controls(self):
        """University partner sidebar has dedicated campus controls without mixing student explore menu."""
        self.client.login(username="partner_admin", password="password123")
        resp = self.client.get(reverse('university_dashboard'))
        self.assertEqual(resp.status_code, 200)

        # University Partner top card
        self.assertContains(resp, 'UNIVERSITY PARTNER')
        self.assertContains(resp, 'partner@apex.edu')

        # Section 1: Campus Controls
        self.assertContains(resp, 'CAMPUS CONTROLS')
        self.assertContains(resp, 'Campus Dashboard')
        self.assertNotContains(resp, 'Admissions Hub')

        # Should NOT contain student explore directory
        self.assertNotContains(resp, 'EXPLORE INSTITUTES &amp; HOUSING')

        # Section 3: About & Transparency
        self.assertContains(resp, 'ABOUT &amp; TRANSPARENCY')
        self.assertContains(resp, 'About CollegeClue')

        # Bottom card displays University Partner role badge
        self.assertContains(resp, 'University Partner')

        # Submit College is hidden from footer for logged in university partner
        self.assertNotContains(resp, 'Submit College</a>')

    def test_accommodation_provider_sidebar_dedicated_controls(self):
        """Accommodation provider sidebar has dedicated housing controls without mixing student explore menu."""
        self.client.login(username="acc_provider", password="password123")
        resp = self.client.get(reverse('accommodation_dashboard'))
        self.assertEqual(resp.status_code, 200)

        # Housing Partner top card
        self.assertContains(resp, 'HOUSING PARTNER')
        self.assertContains(resp, 'housing@example.com')

        # Section 1: Housing Controls
        self.assertContains(resp, 'HOUSING CONTROLS')
        self.assertContains(resp, 'Housing Dashboard')
        self.assertContains(resp, 'List New PG / Hostel')

        # Should NOT contain student explore directory
        self.assertNotContains(resp, 'EXPLORE INSTITUTES &amp; HOUSING')

        # Section 2: About & Transparency
        self.assertContains(resp, 'ABOUT &amp; TRANSPARENCY')
        self.assertContains(resp, 'About CollegeClue')

        # Bottom card displays Housing Partner role badge
        self.assertContains(resp, 'Housing Partner')

    def test_login_by_email_prioritizes_portal_role(self):
        """When an email is associated with both student and university accounts, login resolves according to portal_role."""
        shared_email = "dual_user@example.com"
        uni_user = User.objects.create_user(username="uni_partner_user", email=shared_email, password="password123")
        uni_user.profile.role = "university"
        uni_user.profile.organization_name = "Dual Campus"
        uni_user.profile.save()

        student_user = User.objects.create_user(username="student_dual_user", email=shared_email, password="password123")
        student_user.profile.role = "student"
        student_user.profile.save()

        # 1. Login under University tab with shared email
        resp = self.client.post(reverse('login'), {
            'portal_role': 'university',
            'username': shared_email,
            'password': 'password123',
        })
        self.assertRedirects(resp, reverse('university_dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), uni_user.id)

        self.client.logout()

        # 2. Login under Student tab with shared email
        resp = self.client.post(reverse('login'), {
            'portal_role': 'student',
            'username': shared_email,
            'password': 'password123',
        })
        self.assertRedirects(resp, reverse('home'))
        self.assertEqual(int(self.client.session['_auth_user_id']), student_user.id)


class LoginPortalRefinementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username="super_admin",
            email="admin@collegeclue.local",
            password="SuperPassword123!"
        )
        self.student_user = User.objects.create_user(
            username="student_syed",
            email="syed@example.com",
            password="StudentPassword123!"
        )

    def test_public_login_page_has_no_admin_portal_tab_or_hint(self):
        """Public login page only displays Student, University, Housing; Admin is completely removed."""
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)

        # Renders the 3 public portal tabs
        self.assertContains(resp, 'Student')
        self.assertContains(resp, 'University')
        self.assertContains(resp, 'Housing')

        # Admin tab removed from roleSelectorPills
        self.assertNotContains(resp, '<i class="bi bi-shield-lock me-1"></i>Admin')
        # Admin hint link removed from bottom of public login
        self.assertNotContains(resp, 'Platform Admin Login &rarr;')
        self.assertNotContains(resp, 'role=admin')

    def test_public_login_fields_clean_and_supports_saved_passwords(self):
        """Login form is clean, excludes random suggestions/datalists, hides navbar search, and enables saved passwords."""
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)

        # No random suggestions or datalist
        self.assertNotContains(resp, 'Suggestions:')
        self.assertNotContains(resp, 'login-suggestion-btn')
        self.assertNotContains(resp, 'usernameSuggestions')

        # Standard credentials autocomplete for password managers
        self.assertContains(resp, 'autocomplete="username"')
        self.assertContains(resp, 'autocomplete="current-password"')
        self.assertNotContains(resp, 'autocomplete="off"')
        self.assertNotContains(resp, 'autocomplete="new-password"')

        # Navbar search bar and filter are hidden on login page
        self.assertNotContains(resp, 'id="navCollegeSearchInput"')
        self.assertNotContains(resp, 'id="navbarSearchForm"')

    def test_get_role_admin_redirects_to_dedicated_admin_login(self):
        """Navigating to /account/login/?role=admin cleanly redirects to /admin-portal/login/."""
        resp = self.client.get(f"{reverse('login')}?role=admin")
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('admin_login'), resp.url)

    def test_dedicated_admin_login_portal_success(self):
        """Dedicated admin login page authenticates administrators and redirects to moderation center."""
        resp_get = self.client.get(reverse('admin_login'))
        self.assertEqual(resp_get.status_code, 200)
        self.assertContains(resp_get, 'ADMINISTRATOR ACCESS ONLY')
        self.assertContains(resp_get, 'Platform Admin Login')

        resp_post = self.client.post(reverse('admin_login'), {
            'username': 'super_admin',
            'password': 'SuperPassword123!',
        })
        self.assertEqual(resp_post.status_code, 302)
        self.assertIn(reverse('admin_moderation'), resp_post.url)

    def test_dedicated_admin_login_portal_rejects_regular_student(self):
        """Non-admin user cannot sign in through dedicated admin login portal."""
        resp_post = self.client.post(reverse('admin_login'), {
            'username': 'student_syed',
            'password': 'StudentPassword123!',
        })
        self.assertEqual(resp_post.status_code, 200)
        self.assertContains(resp_post, 'Access Denied: You do not have administrator credentials')


class UniversityPartnerStrictOneInstitutionAndDropdownTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.uni_admin = User.objects.create_user(
            username='uni_admin_user',
            email='admin@uniportal.edu',
            password='Password123!'
        )
        self.uni_admin.profile.role = 'university'
        self.uni_admin.profile.organization_name = 'Tech University Campus'
        self.uni_admin.profile.save()

        self.uni1 = University.objects.create(
            name="University One",
            city="Bengaluru",
            state="Karnataka",
            established_year=2000,
            rating=Decimal("4.5")
        )
        self.college1 = College.objects.create(
            university=self.uni1,
            name="College of Engineering One",
            city="Bengaluru",
            fees=Decimal("150000.00"),
            rating=Decimal("4.5"),
            admin_email="admin@uniportal.edu",
            submitted_by=self.uni_admin,
            status='Approved'
        )

    def test_user_dropdown_contains_only_logout(self):
        """Top navbar user menu should only display user info and Log Out, not dashboard/hub links."""
        self.client.login(username='uni_admin_user', password='Password123!')
        resp = self.client.get(reverse('university_dashboard'))
        self.assertEqual(resp.status_code, 200)

        # Verify dropdown menu specifically contains only Log Out and user role info
        content = resp.content.decode()
        self.assertIn('dropdown-menu dropdown-menu-end', content)
        dropdown_html = content.split('dropdown-menu dropdown-menu-end')[1].split('</ul>')[0]
        self.assertIn('Log Out', dropdown_html)
        self.assertNotIn('Campus Dashboard', dropdown_html)
        self.assertNotIn('Admissions Hub', dropdown_html)
        self.assertNotIn('Housing Dashboard', dropdown_html)

    def test_dashboard_header_banner_clean_no_action_buttons(self):
        """Dashboard header banner should be clean without Review Applications or Create New Course buttons."""
        self.client.login(username='uni_admin_user', password='Password123!')
        resp = self.client.get(reverse('university_dashboard'))
        self.assertEqual(resp.status_code, 200)

        self.assertNotContains(resp, 'Review Applications')

    def test_admin_limited_to_one_institution_on_dashboard(self):
        """Even if multiple colleges exist in DB for this email/user, the portal limits to 1 institution."""
        uni2 = University.objects.create(
            name="University Two",
            city="Mysuru",
            state="Karnataka",
            established_year=2005,
            rating=Decimal("4.2")
        )
        College.objects.create(
            university=uni2,
            name="College of Management Two",
            city="Mysuru",
            fees=Decimal("120000.00"),
            rating=Decimal("4.2"),
            admin_email="admin@uniportal.edu",
            submitted_by=self.uni_admin,
            status='Approved'
        )

        self.client.login(username='uni_admin_user', password='Password123!')
        resp = self.client.get(reverse('university_dashboard'))
        self.assertEqual(resp.status_code, 200)

        # Context has only 1 college and 1 university
        self.assertEqual(len(resp.context['submitted_colleges']), 1)
        self.assertEqual(len(resp.context['administered_universities']), 1)

    def test_submit_new_college_blocked_if_already_administering(self):
        """University partner cannot create a 2nd university/college campus."""
        self.client.login(username='uni_admin_user', password='Password123!')
        resp = self.client.get(reverse('college_submit'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('university_dashboard'), resp.url)


class UniversityPortalAdmissionDatesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.uni = University.objects.create(
            name="Apex National University",
            city="Hyderabad",
            state="Telangana",
            established_year=1998,
            rating=Decimal("4.6")
        )
        self.partner = User.objects.create_user(
            username='apex_admin',
            email='admin@apex.edu.in',
            password='Password123!'
        )
        self.partner.profile.role = 'university'
        self.partner.profile.organization_name = 'Apex Engineering'
        self.partner.profile.save()

        self.college = College.objects.create(
            university=self.uni,
            name="Apex Institute of Technology",
            city="Hyderabad",
            fees=Decimal("180000.00"),
            rating=Decimal("4.6"),
            admin_email="admin@apex.edu.in",
            submitted_by=self.partner,
            status='Approved',
            admissions_status='Open',
            admission_open_date=datetime.date(2026, 1, 1),
            admission_close_date=datetime.date(2026, 12, 31)
        )
        self.course = Course.objects.create(
            college=self.college,
            name="B.Tech Artificial Intelligence",
            duration_years=4,
            fee=Decimal("180000.00"),
            seats=60
        )
        self.student = User.objects.create_user(
            username='student_applicant',
            email='student.app@example.com',
            password='Password123!'
        )

    def test_admission_dates_properties(self):
        """Verifies is_admission_open and admission_dates_display calculation."""
        self.assertTrue(self.college.is_admission_open)
        self.assertIn("Admissions Open Till 31 Dec 2026", self.college.admission_dates_display)

        # Closed status
        self.college.admissions_status = 'Closed'
        self.assertFalse(self.college.is_admission_open)
        self.assertEqual(self.college.admission_dates_display, "Admissions Closed")

        # Reopen with expired deadline
        self.college.admissions_status = 'Open'
        self.college.admission_close_date = datetime.date(2025, 1, 1)
        self.assertFalse(self.college.is_admission_open)
        self.assertIn("Admissions Closed", self.college.admission_dates_display)

    def test_partner_updates_admission_dates_via_modal(self):
        """University portal admin updates admission dates via dedicated endpoint."""
        self.client.login(username='apex_admin', password='Password123!')
        resp = self.client.post(reverse('college_admission_dates_update', kwargs={'college_id': self.college.id}), {
            'admissions_status': 'Open',
            'admission_open_date': '2026-06-01',
            'admission_close_date': '2026-11-30',
        })
        self.assertEqual(resp.status_code, 302)
        self.college.refresh_from_db()
        self.assertEqual(self.college.admission_close_date, datetime.date(2026, 11, 30))
        self.assertEqual(self.college.admission_open_date, datetime.date(2026, 6, 1))

    def test_student_views_show_admission_dates_and_apply_button(self):
        """Student views display the active admission dates badge and enabled Apply button."""
        resp = self.client.get(reverse('college_detail', kwargs={'slug': self.college.slug}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Admissions Open Till 31 Dec 2026")
        self.assertContains(resp, "Apply for Admission")

        # Check college list
        resp_list = self.client.get(reverse('college_list'))
        self.assertEqual(resp_list.status_code, 200)
        self.assertContains(resp_list, "Admissions Open Till 31 Dec 2026")

    def test_student_blocked_when_admission_closed(self):
        """When admissions are closed, Apply is disabled and registration is blocked."""
        self.college.admissions_status = 'Closed'
        self.college.save()

        # College detail displays closed / unavailable
        resp = self.client.get(reverse('college_detail', kwargs={'slug': self.college.slug}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Application Unavailable")
        self.assertContains(resp, "Admissions Closed")

        # Student trying to register is rejected
        self.client.login(username='student_applicant', password='Password123!')
        resp_apply = self.client.get(f"{reverse('registration_form')}?college={self.college.id}")
        self.assertEqual(resp_apply.status_code, 302)
        self.assertIn(reverse('college_detail', kwargs={'slug': self.college.slug}), resp_apply.url)


class UniversityPortalSeparatePagesAndDynamicCourseTests(TestCase):
    """
    Tests for the separation of Campus Details and Academic Courses into distinct pages and menu items,
    along with dynamic '+' course creation functionality.
    """
    def setUp(self):
        self.uni_user = User.objects.create_user(
            username='partner_uni_admin',
            email='partner@institute.edu.in',
            password='Password123!'
        )
        self.uni_user.profile.role = 'university'
        self.uni_user.profile.organization_name = 'Tech Institute of Science'
        self.uni_user.profile.save()

        self.university = University.objects.create(
            name='Central Technical University',
            established_year=1995,
            city='Hyderabad'
        )

        self.college = College.objects.create(
            university=self.university,
            name='Tech Institute of Science Campus',
            city='Hyderabad',
            fees=Decimal('180000.00'),
            rating=Decimal('4.5'),
            status='Approved',
            submitted_by=self.uni_user,
            admin_email='partner@institute.edu.in',
            admissions_status='Open',
            admission_close_date=datetime.date(2026, 12, 31)
        )

        self.course1 = Course.objects.create(
            college=self.college,
            name='B.Tech Computer Science & Engineering',
            duration_years=4,
            fee=Decimal('180000.00'),
            seats=120
        )

    def test_campus_details_page_separated_from_courses(self):
        """Campus details page only has campus info, no course add form or course column."""
        self.client.login(username='partner_uni_admin', password='Password123!')
        edit_url = reverse('college_edit', kwargs={'college_id': self.college.id})
        resp = self.client.get(edit_url)
        self.assertEqual(resp.status_code, 200)

        # Campus details header and tabs are present
        self.assertContains(resp, "Edit Campus Details")
        self.assertContains(resp, "Academic Courses")
        self.assertContains(resp, reverse('college_courses', kwargs={'college_id': self.college.id}))

        # Course management form and list are separated out of this page
        self.assertNotContains(resp, "Add New Academic Course")
        self.assertNotContains(resp, "action=\"" + reverse('course_add', kwargs={'college_id': self.college.id}) + "\"")

    def test_academic_courses_page_rendering(self):
        """Dedicated Academic Courses page displays existing courses and dynamic course creator."""
        self.client.login(username='partner_uni_admin', password='Password123!')
        courses_url = reverse('college_courses', kwargs={'college_id': self.college.id})
        resp = self.client.get(courses_url)
        self.assertEqual(resp.status_code, 200)

        # Page title, tabs, and existing course
        self.assertContains(resp, "Academic Courses &amp; Programs")
        self.assertContains(resp, "B.Tech Computer Science &amp; Engineering")
        self.assertContains(resp, "Offered Courses")
        self.assertContains(resp, "Add Academic Courses")
        self.assertContains(resp, "+ Add Course")
        self.assertNotContains(resp, "+ Add Another Course")
        self.assertContains(resp, "Save All Courses")
        self.assertContains(resp, reverse('college_edit', kwargs={'college_id': self.college.id}))

    def test_dynamic_courses_submission_multi_rows(self):
        """Dynamic multi-row course submission creates all submitted courses in batch."""
        self.client.login(username='partner_uni_admin', password='Password123!')
        courses_url = reverse('college_courses', kwargs={'college_id': self.college.id})

        post_data = {
            'course_name[]': ['B.Tech Artificial Intelligence', 'M.Tech Data Science'],
            'course_duration[]': ['4', '2'],
            'course_fee[]': ['250000.00', '195000.00'],
            'course_seats[]': ['60', '30'],
            'course_url[]': ['https://example.com/ai', 'https://example.com/ds'],
        }

        resp = self.client.post(courses_url, post_data)
        self.assertRedirects(resp, courses_url)

        # Verify courses created in database
        ai_course = Course.objects.get(college=self.college, name='B.Tech Artificial Intelligence')
        self.assertEqual(ai_course.duration_years, 4)
        self.assertEqual(ai_course.fee, Decimal('250000.00'))
        self.assertEqual(ai_course.seats, 60)
        self.assertEqual(ai_course.course_url, 'https://example.com/ai')

        ds_course = Course.objects.get(college=self.college, name='M.Tech Data Science')
        self.assertEqual(ds_course.duration_years, 2)
        self.assertEqual(ds_course.fee, Decimal('195000.00'))
        self.assertEqual(ds_course.seats, 30)

        # Total courses under college is now 3
        self.assertEqual(self.college.courses.count(), 3)

    def test_course_delete_redirects_to_college_courses(self):
        """Deleting a course redirects back to the dedicated college_courses page."""
        self.client.login(username='partner_uni_admin', password='Password123!')
        del_url = reverse('course_delete', kwargs={'college_id': self.college.id, 'course_id': self.course1.id})
        resp = self.client.post(del_url)
        expected_url = reverse('college_courses', kwargs={'college_id': self.college.id})
        self.assertRedirects(resp, expected_url)
        self.assertFalse(Course.objects.filter(id=self.course1.id).exists())

    def test_sidebar_and_navbar_menu_links_divided(self):
        """Dashboard and base layout render divided Campus Details and Academic Courses menu items."""
        self.client.login(username='partner_uni_admin', password='Password123!')
        dash_url = reverse('university_dashboard')
        resp = self.client.get(dash_url)
        self.assertEqual(resp.status_code, 200)

        edit_url = reverse('college_edit', kwargs={'college_id': self.college.id})
        courses_url = reverse('college_courses', kwargs={'college_id': self.college.id})

        # Check menu bar links exist
        self.assertContains(resp, edit_url)
        self.assertContains(resp, courses_url)
        self.assertContains(resp, "Campus Details")
        self.assertContains(resp, "Academic Courses")

    def test_unauthorized_user_blocked_from_college_courses(self):
        """Non-partner user or unauthorized user cannot view or edit courses."""
        unauthorized_user = User.objects.create_user(
            username='other_student',
            password='Password123!'
        )
        self.client.login(username='other_student', password='Password123!')
        courses_url = reverse('college_courses', kwargs={'college_id': self.college.id})
        resp = self.client.get(courses_url)
        self.assertEqual(resp.status_code, 302)

    def test_course_edit_success(self):
        """Admin can edit an existing course's details."""
        self.client.login(username='partner_uni_admin', password='Password123!')
        edit_url = reverse('course_edit', kwargs={'college_id': self.college.id, 'course_id': self.course1.id})
        data = {
            'name': 'B.Tech AI & Data Science (Updated)',
            'duration_years': 4,
            'fee': '210000.00',
            'seats': 80,
            'course_url': 'https://university.edu/syllabus/ai-ds'
        }
        resp = self.client.post(edit_url, data)
        expected_url = reverse('college_courses', kwargs={'college_id': self.college.id})
        self.assertRedirects(resp, expected_url)

        self.course1.refresh_from_db()
        self.assertEqual(self.course1.name, 'B.Tech AI & Data Science (Updated)')
        self.assertEqual(self.course1.fee, Decimal('210000.00'))
        self.assertEqual(self.course1.seats, 80)
        self.assertEqual(self.course1.course_url, 'https://university.edu/syllabus/ai-ds')

    def test_college_courses_page_has_edit_button_and_no_hero_banner_buttons(self):
        """Verify Offered Courses list contains edit button/modal, and hero banner does not have the old buttons."""
        self.client.login(username='partner_uni_admin', password='Password123!')
        courses_url = reverse('college_courses', kwargs={'college_id': self.college.id})
        resp = self.client.get(courses_url)
        self.assertEqual(resp.status_code, 200)

        # Edit button and modal exist for course
        self.assertContains(resp, f'#editCourseModal{self.course1.id}')
        self.assertContains(resp, 'Edit Course Details')

        # Hero banner does not have the old redundant buttons
        self.assertNotContains(resp, 'Edit Campus Details</a>')

    def test_sidebar_menu_cleanup_and_manual_close(self):
        """Sidebar menu does not contain '+ Create New Course / Program' and has data-bs-backdrop='false'."""
        self.client.login(username='partner_uni_admin', password='Password123!')
        dash_url = reverse('university_dashboard')
        resp = self.client.get(dash_url)
        self.assertEqual(resp.status_code, 200)

        # Sidebar attributes for manual close and docking
        self.assertContains(resp, 'data-bs-backdrop="false"')
        self.assertContains(resp, 'data-bs-scroll="true"')

        # Removed button
        self.assertNotContains(resp, '+ Create New Course / Program')
        # Removed plus beside engineering
        self.assertNotContains(resp, 'title="Add Course to Engineering"')

    def test_guest_visitor_card_has_clean_login_only(self):
        """Guest visitor menu card only renders clean Login button, no Student Sign In or Partner Portal."""
        self.client.logout()
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Guest Visitor")
        self.assertContains(resp, "<span>Login</span>")
        self.assertNotContains(resp, "<span>Student Sign In</span>")
        self.assertNotContains(resp, "?role=university")
        self.assertNotContains(resp, '<i class="bi bi-person-plus"></i> Register')

    def test_home_card_has_know_more_and_wishlist_without_info_and_apply(self):
        """Home page college cards render 'Know More' and 'Wishlist' buttons, without old Info/Apply."""
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Know More")
        self.assertContains(resp, "Wishlist")
        self.assertNotContains(resp, ">Info<")
        self.assertNotContains(resp, ">Apply<")

    def test_approval_deducts_available_seats_in_view(self):
        """When an applicant is approved (Confirmed), available seats are deducted and displayed in views."""
        self.assertEqual(self.course1.seats, 120)
        self.assertEqual(self.course1.available_seats, 120)

        # Create a student application for course1
        student_reg = StudentRegistration.objects.create(
            full_name='Aarav Sharma',
            email='aarav.sharma@example.com',
            phone='9876543210',
            college=self.college,
            course=self.course1,
            class_10_percentage=Decimal('85.50'),
            class_12_percentage=Decimal('88.00'),
            status='Pending'
        )

        # Check college_courses view before approval
        self.client.login(username='partner_uni_admin', password='Password123!')
        courses_url = reverse('college_courses', kwargs={'college_id': self.college.id})
        resp_before = self.client.get(courses_url)
        self.assertContains(resp_before, "120</strong> seats available")

        # Approve applicant via university_application_approve_view
        approve_url = reverse('university_application_approve', kwargs={'registration_id': student_reg.registration_id})
        resp_approve = self.client.post(approve_url, {'admin_notes': 'Verified documents.'})
        self.assertRedirects(resp_approve, reverse('university_applications'))

        # Check DB state
        student_reg.refresh_from_db()
        self.assertEqual(student_reg.status, 'Confirmed')
        self.assertEqual(self.course1.confirmed_admissions_count, 1)
        self.assertEqual(self.course1.available_seats, 119)

        # Verify college_courses view reflects 119 available seats
        resp_after = self.client.get(courses_url)
        self.assertContains(resp_after, "119</strong> seats available")
        self.assertContains(resp_after, "(120 total)")

        # Verify college_detail view reflects 119 available seats
        detail_url = reverse('college_detail', kwargs={'slug': self.college.slug})
        resp_detail = self.client.get(detail_url)
        self.assertContains(resp_detail, "119</strong> / 120 Seats Available")


class UniversityPortalAdmissionToggleAndDetailEnhancementTests(TestCase):
    """
    Tests for:
    1. Removal of Nearby PGs and addition of View University Location button on college detail.
    2. High-contrast text styling for section navigation tabs.
    3. 1-click Admissions ON / OFF toggle button.
    """
    def setUp(self):
        self.uni_user = User.objects.create_user(
            username='partner_uni_admin_toggle',
            email='toggle_admin@institute.edu.in',
            password='Password123!'
        )
        self.uni_user.profile.role = 'university'
        self.uni_user.profile.save()

        self.university = University.objects.create(
            name='Hyderabad State University',
            established_year=2000,
            city='Hyderabad',
            gmap_location='https://maps.google.com/?q=Hyderabad+State+University'
        )

        self.college = College.objects.create(
            university=self.university,
            name='School of Computing & AI',
            city='Hyderabad',
            fees=Decimal('160000.00'),
            rating=Decimal('4.6'),
            status='Approved',
            submitted_by=self.uni_user,
            admin_email='toggle_admin@institute.edu.in',
            admissions_status='Open',
            admission_close_date=datetime.date(2026, 12, 31)
        )

    def test_college_detail_no_nearby_pgs_in_actions_and_has_location(self):
        """College detail action bar must not contain Nearby PGs, and must contain View University Location."""
        detail_url = reverse('college_detail', kwargs={'slug': self.college.slug})
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, 200)

        # Action bar contains View University Location
        self.assertContains(resp, "View University Location")
        # Action bar does NOT contain Nearby PGs button
        self.assertNotContains(resp, "Nearby PGs (")

    def test_college_detail_tabs_visibility_styling(self):
        """College detail page contains high-contrast styling for #collegeDetailTabs."""
        detail_url = reverse('college_detail', kwargs={'slug': self.college.slug})
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, 200)

        self.assertContains(resp, "#collegeDetailTabs .nav-link")
        self.assertContains(resp, "color: #0f172a !important")

    def test_admission_toggle_1_click(self):
        """1-click admission toggle switches status from Open to Closed and Closed to Open."""
        self.client.login(username='partner_uni_admin_toggle', password='Password123!')
        toggle_url = reverse('college_admission_toggle', kwargs={'college_id': self.college.id})

        # 1. Initially Open -> toggle to Closed (OFF)
        resp1 = self.client.post(toggle_url)
        self.assertEqual(resp1.status_code, 302)
        self.college.refresh_from_db()
        self.assertEqual(self.college.admissions_status, 'Closed')
        self.assertFalse(self.college.is_admission_open)

        # 2. Currently Closed -> toggle to Open (ON)
        resp2 = self.client.post(toggle_url)
        self.assertEqual(resp2.status_code, 302)
        self.college.refresh_from_db()
        self.assertEqual(self.college.admissions_status, 'Open')
        self.assertTrue(self.college.is_admission_open)

    def test_admission_toggle_rendered_on_dashboard_and_edit_page(self):
        """1-click Admissions ON / OFF button is present on both university dashboard and college edit page."""
        self.client.login(username='partner_uni_admin_toggle', password='Password123!')
        dash_url = reverse('university_dashboard')
        resp_dash = self.client.get(dash_url)
        self.assertEqual(resp_dash.status_code, 200)
        self.assertContains(resp_dash, "toggle-admission")
        self.assertContains(resp_dash, "Admissions: <strong>ON</strong> (Turn OFF)")

        edit_url = reverse('college_edit', kwargs={'college_id': self.college.id})
        resp_edit = self.client.get(edit_url)
        self.assertEqual(resp_edit.status_code, 200)
        self.assertContains(resp_edit, "toggle-admission")
        self.assertContains(resp_edit, "Admissions: ON (Turn OFF)")


class UniversitySidebarAndNavbarSimplificationTests(TestCase):
    """
    Tests for:
    1. Navbar clean beside login button (no shortcut pills like Campus Details, Academic Courses, Applications).
    2. Removal of Admissions Hub from sidebar CAMPUS CONTROLS.
    3. Departments & Courses in sidebar only keeps available categories (no 0-count items).
    4. College title and Engineering category have '+' symbol to add courses simply.
    """
    def setUp(self):
        self.uni_user = User.objects.create_user(
            username='partner_uni_clean',
            email='clean@engineering.edu.in',
            password='Password123!'
        )
        self.uni_user.profile.role = 'university'
        self.uni_user.profile.organization_name = 'Engineering College'
        self.uni_user.profile.save()

        self.university = University.objects.create(
            name='Technical University',
            city='Hyderabad',
            established_year=1990
        )

        self.college = College.objects.create(
            university=self.university,
            name='Engineering',
            city='Hyderabad',
            fees=Decimal('150000.00'),
            status='Approved',
            submitted_by=self.uni_user,
            admin_email='clean@engineering.edu.in'
        )

        # Create one Engineering course and one Science course
        Course.objects.create(
            college=self.college,
            name='B.Tech Computer Science',
            duration_years=4,
            fee=Decimal('150000.00'),
            seats=60
        )
        Course.objects.create(
            college=self.college,
            name='Data Science',
            duration_years=2,
            fee=Decimal('120000.00'),
            seats=20
        )

    def test_navbar_beside_login_is_clean(self):
        """Top navbar must not contain Campus Details, Academic Courses, or Applications shortcuts beside login."""
        self.client.login(username='partner_uni_clean', password='Password123!')
        dash_url = reverse('university_dashboard')
        resp = self.client.get(dash_url)
        self.assertEqual(resp.status_code, 200)

        # In navbar right nav items, there should not be shortcut pills
        # Check navbar right items specifically
        content = resp.content.decode('utf-8')
        navbar_part = content.split('<ul class="navbar-nav ms-auto align-items-center flex-row flex-wrap gap-2">')[1].split('</ul>')[0]
        self.assertNotIn('Campus Details', navbar_part)
        self.assertNotIn('Academic Courses', navbar_part)
        self.assertNotIn('Applications</span>', navbar_part)

    def test_sidebar_no_admission_hub(self):
        """Sidebar CAMPUS CONTROLS must not contain Admissions Hub."""
        self.client.login(username='partner_uni_clean', password='Password123!')
        resp = self.client.get(reverse('university_dashboard'))
        self.assertEqual(resp.status_code, 200)

        self.assertContains(resp, 'Campus Dashboard')
        self.assertContains(resp, 'Campus Details')
        self.assertContains(resp, 'Academic Courses')
        self.assertNotContains(resp, 'Admissions Hub')

    def test_departments_and_courses_only_available_and_has_plus(self):
        """Departments & Courses only displays available categories (>0) and includes '+' symbol beside Engineering."""
        self.client.login(username='partner_uni_clean', password='Password123!')
        resp = self.client.get(reverse('university_dashboard'))
        self.assertEqual(resp.status_code, 200)

        # Available categories should be present
        self.assertContains(resp, 'Engineering')
        self.assertContains(resp, 'Science / IT')

        # 0-count categories (Arts & Law, Specialized) must NOT be present
        self.assertNotContains(resp, 'Arts &amp; Law')
        self.assertNotContains(resp, 'Arts & Law')
        self.assertNotContains(resp, 'Specialized')

        # Per user request 8, '+' button beside engineering was removed
        self.assertNotContains(resp, 'title="Add Academic Course"')

    def test_university_dashboard_quick_stats_cards_removed(self):
        """Dashboard must not contain the 4 quick stats cards (Campuses Administered, Approved & Live, etc.)."""
        self.client.login(username='partner_uni_clean', password='Password123!')
        resp = self.client.get(reverse('university_dashboard'))
        self.assertEqual(resp.status_code, 200)

        self.assertNotContains(resp, 'Campuses Administered')
        self.assertNotContains(resp, 'Pending Applications')
        self.assertNotContains(resp, 'Total Applied Students')
        self.assertNotContains(resp, 'Quick Stats')


class UniversityAdminSharedAccountAndUniqueUsernameTests(TestCase):
    """
    Tests for creator admin accounts and creating shared sub-admin accounts with unique usernames:
    1. Creator can log in using email and password and access college data.
    2. Admin can create an account with a unique username, staff email, and password.
    3. Duplicate username is rejected with a validation error.
    4. The created user can log in with their unique username and access the exact same college, courses, and data.
    5. The new username is displayed on the Admin Team page and can be revoked.
    """
    def setUp(self):
        self.creator = User.objects.create_user(
            username='imransyd00',
            email='imransyd00@gmail.com',
            password='AdminPassword123!'
        )
        self.creator.profile.role = 'university'
        self.creator.profile.organization_name = 'Engineering College'
        self.creator.profile.save()

        self.university = University.objects.create(
            name='Engineering University',
            city='Hyderabad',
            established_year=2000
        )

        self.college = College.objects.create(
            university=self.university,
            name='Engineering',
            city='Hyderabad',
            fees=Decimal('150000.00'),
            rating=Decimal('4.5'),
            status='Approved',
            submitted_by=self.creator,
            admin_email='imransyd00@gmail.com',
            admissions_status='Open',
            admission_close_date=datetime.date(2026, 12, 31)
        )

        self.course = Course.objects.create(
            college=self.college,
            name='B.Tech AI & Data Science',
            duration_years=4,
            fee=Decimal('180000.00'),
            seats=60
        )

    def test_creator_login_with_email_accesses_same_data(self):
        """Creator can log in with email and access the administered college."""
        login_resp = self.client.post(reverse('login'), {
            'username': 'imransyd00@gmail.com',
            'password': 'AdminPassword123!',
            'portal_role': 'university'
        })
        self.assertEqual(login_resp.status_code, 302)
        self.assertRedirects(login_resp, reverse('university_dashboard'))

        dash_resp = self.client.get(reverse('university_dashboard'))
        self.assertEqual(dash_resp.status_code, 200)
        self.assertContains(dash_resp, 'Engineering')

    def test_admin_creates_subadmin_account_with_unique_username(self):
        """Admin can create an account with a unique username, email, and password."""
        self.client.login(username='imransyd00', password='AdminPassword123!')
        team_url = reverse('college_team', kwargs={'college_id': self.college.id})

        # Post new account
        resp = self.client.post(team_url, {
            'action': 'add_member',
            'staff_username': 'subadmin_dean',
            'staff_email': 'dean@engineering.edu.in',
            'staff_password': 'DeanSecurePass123!'
        })
        self.assertRedirects(resp, team_url)

        # User is created with unique username and university role
        sub_user = User.objects.filter(username='subadmin_dean').first()
        self.assertIsNotNone(sub_user)
        self.assertEqual(sub_user.email, 'dean@engineering.edu.in')
        self.assertEqual(sub_user.profile.role, 'university')

        # Linked to college team
        membership = CollegeTeamMember.objects.filter(college=self.college, user=sub_user).first()
        self.assertIsNotNone(membership)

        # Team page shows the unique username
        page_resp = self.client.get(team_url)
        self.assertContains(page_resp, 'subadmin_dean')
        self.assertContains(page_resp, 'dean@engineering.edu.in')
        self.assertContains(page_resp, 'Same Database (Full Access)')

    def test_duplicate_username_is_rejected(self):
        """Attempting to create an account with an existing username is rejected."""
        self.client.login(username='imransyd00', password='AdminPassword123!')
        team_url = reverse('college_team', kwargs={'college_id': self.college.id})

        # Try to use creator's username 'imransyd00'
        resp = self.client.post(team_url, {
            'action': 'add_member',
            'staff_username': 'imransyd00',
            'staff_email': 'hod@engineering.edu.in',
            'staff_password': 'SomePassword123!'
        })
        self.assertRedirects(resp, team_url)

        # Ensure no duplicate team member was created for that username
        self.assertEqual(CollegeTeamMember.objects.filter(college=self.college).count(), 0)

    def test_subadmin_can_login_with_username_and_access_same_database(self):
        """User created by admin can log in with their unique username and access the exact same college database."""
        # 1. Admin creates the account
        self.client.login(username='imransyd00', password='AdminPassword123!')
        team_url = reverse('college_team', kwargs={'college_id': self.college.id})
        self.client.post(team_url, {
            'action': 'add_member',
            'staff_username': 'assistant_admin',
            'staff_email': 'admissions@engineering.edu.in',
            'staff_password': 'SameSecretPass123!'
        })
        self.client.logout()

        # 2. Another user logs in using this unique username
        login_resp = self.client.post(reverse('login'), {
            'username': 'assistant_admin',
            'password': 'SameSecretPass123!',
            'portal_role': 'university'
        })
        self.assertEqual(login_resp.status_code, 302)
        self.assertRedirects(login_resp, reverse('university_dashboard'))

        # 3. User accesses the exact same dashboard and college data
        dash_resp = self.client.get(reverse('university_dashboard'))
        self.assertEqual(dash_resp.status_code, 200)
        self.assertContains(dash_resp, 'Engineering')

        # 4. User accesses the exact same courses
        courses_resp = self.client.get(reverse('college_courses', kwargs={'college_id': self.college.id}))
        self.assertEqual(courses_resp.status_code, 200)
        self.assertContains(courses_resp, 'B.Tech AI &amp; Data Science')

        # 5. User can toggle admissions for this college
        toggle_resp = self.client.post(reverse('college_admission_toggle', kwargs={'college_id': self.college.id}))
        self.assertEqual(toggle_resp.status_code, 302)
        self.college.refresh_from_db()
        self.assertEqual(self.college.admissions_status, 'Closed')


class ResponsiveSidebarAndSkiperDarkThemeTests(TestCase):
    """
    Tests for:
    1. Responsive sidebar docking avoiding any content overlap across desktop and split-screen viewports.
    2. Elimination of hardcoded inline sidebar width in base.html.
    3. Skiper UI and Vengeance AI ultra-modern dark theme color system and frosted elements.
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username='theme_partner',
            email='theme@college.edu',
            password='Password123!'
        )
        self.user.profile.role = 'university'
        self.user.profile.organization_name = 'Tech Institute'
        self.user.profile.save()

        self.university = University.objects.create(
            name='Global Tech University',
            city='Hyderabad',
            established_year=2000
        )
        self.college = College.objects.create(
            university=self.university,
            name='Engineering College',
            city='Hyderabad',
            fees=Decimal('120000.00'),
            status='Approved',
            submitted_by=self.user,
            admin_email='theme@college.edu'
        )
        self.course = Course.objects.create(
            college=self.college,
            name='B.Tech CSE',
            duration_years=4,
            fee=Decimal('120000.00'),
            seats=60
        )

    def test_sidebar_in_base_template_has_no_hardcoded_width(self):
        """Sidebar markup must not have a hardcoded inline width like style='width: 350px;'."""
        self.client.login(username='theme_partner', password='Password123!')
        resp = self.client.get(reverse('university_dashboard'))
        self.assertEqual(resp.status_code, 200)

        content = resp.content.decode('utf-8')
        self.assertIn('id="collegeClueSidebar"', content)
        self.assertNotIn('width: 350px;', content)
        self.assertIn('data-bs-backdrop="false"', content)

    def test_sidebar_docking_script_present(self):
        """base.html must contain the non-overlapping canDock script and sidebar-open handler."""
        self.client.login(username='theme_partner', password='Password123!')
        resp = self.client.get(reverse('university_dashboard'))
        content = resp.content.decode('utf-8')

        self.assertIn('canDock', content)
        self.assertIn('sidebar-open', content)
        self.assertIn('sidebar-open-init', content)

    def test_style_css_has_responsive_docking_and_skiper_palette(self):
        """style.css must have responsive sidebar widths and the unified Warm Linen palette."""
        import os
        from django.conf import settings

        css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'style.css')
        with open(css_path, 'r', encoding='utf-8') as f:
            css = f.read()

        # Responsive docking system
        self.assertIn('--cc-sidebar-width', css)
        self.assertIn('body.sidebar-open', css)
        self.assertIn('padding-left: var(--cc-sidebar-width)', css)

        # Unified Warm Linen & Earthy Olive palette
        self.assertIn('--cc-bg: #faf8f2;', css)
        self.assertIn('--cc-surface: #ffffff;', css)
        self.assertIn('--cc-primary: #525445;', css)

    def test_partner_campus_pages_render_cleanly(self):
        """Partner edit campus and courses pages render successfully with layout markers."""
        self.client.login(username='theme_partner', password='Password123!')

        edit_resp = self.client.get(reverse('college_edit', kwargs={'college_id': self.college.id}))
        self.assertEqual(edit_resp.status_code, 200)
        self.assertContains(edit_resp, 'Campus Details')
        self.assertContains(edit_resp, 'Academic Courses')

        courses_resp = self.client.get(reverse('college_courses', kwargs={'college_id': self.college.id}))
        self.assertEqual(courses_resp.status_code, 200)
        self.assertContains(courses_resp, 'Offered Courses')
        self.assertContains(courses_resp, 'B.Tech CSE')


class AsyncWishlistToggleTests(TestCase):
    """
    Tests for:
    1. Async wishlist toggle via AJAX without screen reload, screen shake, or scroll jump.
    2. Proper JSON response containing status, is_wishlisted, count, message, and university info.
    3. Proper 401 unauthenticated handling for AJAX requests.
    4. Button attributes (wishlist-toggle-btn and data-university-id) present on homepage cards.
    5. Base template script presence.
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username='wishlist_student',
            email='wishlist@test.edu',
            password='Password123!'
        )
        self.user.profile.role = 'student'
        self.user.profile.save()

        self.university = University.objects.create(
            name='Hyderabad Institute of Science',
            city='Hyderabad',
            established_year=2005
        )
        self.college = College.objects.create(
            university=self.university,
            name='Engineering Campus',
            city='Hyderabad',
            fees=Decimal('100000.00'),
            status='Approved'
        )

    def test_ajax_wishlist_add_and_remove(self):
        """AJAX request to wishlist_toggle must return JSON and toggle without full page reload."""
        self.client.login(username='wishlist_student', password='Password123!')

        # 1. Add to wishlist via AJAX
        toggle_url = reverse('wishlist_toggle', kwargs={'university_id': self.university.id})
        resp = self.client.get(toggle_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/json')
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['is_wishlisted'])
        self.assertEqual(data['wishlist_count'], 1)
        self.assertIn("Added Hyderabad Institute of Science", data['message'])
        self.assertTrue(Wishlist.objects.filter(user=self.user, university=self.university).exists())

        # 2. Remove from wishlist via AJAX
        resp2 = self.client.get(toggle_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertEqual(data2['status'], 'success')
        self.assertFalse(data2['is_wishlisted'])
        self.assertEqual(data2['wishlist_count'], 0)
        self.assertIn("Removed Hyderabad Institute of Science", data2['message'])
        self.assertFalse(Wishlist.objects.filter(user=self.user, university=self.university).exists())

    def test_ajax_wishlist_unauthenticated(self):
        """Unauthenticated AJAX request returns 401 with login URL."""
        toggle_url = reverse('wishlist_toggle', kwargs={'university_id': self.university.id})
        resp = self.client.get(toggle_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(resp.status_code, 401)
        data = resp.json()
        self.assertEqual(data['status'], 'unauthenticated')
        self.assertIn('login', data['login_url'])

    def test_homepage_college_cards_have_ajax_wishlist_attributes(self):
        """Home page college cards must render wishlist-toggle-btn class and data-university-id."""
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')

        self.assertIn('wishlist-toggle-btn', content)
        self.assertIn(f'data-university-id="{self.university.id}"', content)

    def test_base_template_has_async_wishlist_script(self):
        """base.html must contain the async wishlist handler and wishlist-count-badge."""
        resp = self.client.get(reverse('home'))
        content = resp.content.decode('utf-8')

        self.assertIn('Async Wishlist Toggle', content)
        self.assertIn('wishlist-count-badge', content)


class CollegeListSearchAndCompareRemovalTests(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Alliance University",
            slug="alliance-university",
            city="Bengaluru",
            established_year=2010
        )
        self.college = College.objects.create(
            university=self.university,
            name="Alliance College of Engineering",
            slug="alliance-college-of-engineering",
            city="Bengaluru",
            fees=Decimal("275000.00"),
            rating=Decimal("4.50"),
            status='Approved'
        )

    def test_college_list_removes_top_navbar_search(self):
        """Top navbar search is hidden on college list page ('renmove up side')."""
        resp = self.client.get(reverse('college_list'))
        self.assertEqual(resp.status_code, 200)
        # hide_navbar_search is set in context
        self.assertTrue(resp.context.get('hide_navbar_search'))
        # Center navbar search form is not rendered
        self.assertNotContains(resp, 'id="navbarSearchForm"')

    def test_college_list_has_search_bar_beside_filter(self):
        """College list header contains search form beside the filter button."""
        resp = self.client.get(reverse('college_list'))
        self.assertEqual(resp.status_code, 200)
        # On-page search bar
        self.assertContains(resp, 'id="collegeListSearchForm"')
        self.assertContains(resp, 'placeholder="Search colleges, degrees..."')
        # Filter button beside it
        self.assertContains(resp, 'data-bs-target="#searchFilterModal"')

    def test_college_list_removes_comparison_matrix(self):
        """Comparison matrix button, comparison floating reminder, and compare button on cards are removed."""
        resp = self.client.get(reverse('college_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "View Comparison Matrix")
        self.assertNotContains(resp, 'id="compareActiveReminderBar"')
        self.assertNotContains(resp, '>Compare</a>')
        self.assertNotContains(resp, '>In Compare</a>')
        self.assertContains(resp, "View Details")

    def test_college_list_search_query_execution(self):
        """Search query properly filters colleges list."""
        resp = self.client.get(reverse('college_list') + '?search=Alliance')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Alliance College of Engineering")

        resp_none = self.client.get(reverse('college_list') + '?search=NonExistentCollege123')
        self.assertEqual(resp_none.status_code, 200)
        self.assertNotContains(resp_none, "Alliance College of Engineering")
        self.assertContains(resp_none, "No Colleges Match Your Search Filters")


class SidebarAndAccommodationFormUpdatesTests(TestCase):
    def setUp(self):
        self.partner_user = User.objects.create_user(
            username='housing_owner',
            email='housingowner@example.com',
            password='Password123!'
        )
        self.partner_user.profile.role = 'accommodation'
        self.partner_user.profile.save()

        self.university = University.objects.create(
            name="Alliance University",
            slug="alliance-university-hostel",
            city="Bengaluru",
            established_year=2010
        )
        self.college = College.objects.create(
            university=self.university,
            name="Alliance School of Business",
            slug="alliance-school-of-business",
            city="Bengaluru",
            fees=Decimal("450000.00"),
            rating=Decimal("4.60"),
            status='Approved'
        )
        self.accommodation = Accommodation.objects.create(
            submitted_by=self.partner_user,
            name="Google PG",
            type="Hostel",
            college=self.college,
            city="Bangalore",
            address="Near Alliance campus, 5th Cross",
            rent=Decimal("23333.00"),
            room_type="Single",
            gender="Boys",
            food_included="Included",
            security_deposit=Decimal("10000.00"),
            notice_period="1 Month",
            gate_closing_time="10:30 PM",
            facilities="Wi-Fi, 3 Meals, Power Backup",
            contact_phone="9876543210",
            contact_email="wewee22@gmail.com",
            is_available=True,
            status="Approved"
        )

    def test_navbar_removes_dark_button(self):
        """Top navbar must not contain the dark theme toggle button beside login/user."""
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'id="ccThemeToggleBtn"')
        self.assertNotContains(resp, 'id="ccThemeLabel"')

    def test_sidebar_removes_into_close_symbol(self):
        """Sidebar header must not have the into/close symbol (btn-close) in its offcanvas-header."""
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        self.assertIn('id="collegeClueSidebar"', content)
        # Verify btn-close is not in the offcanvas header
        sidebar_start = content.find('id="collegeClueSidebar"')
        sidebar_header_end = content.find('class="offcanvas-body', sidebar_start)
        sidebar_header = content[sidebar_start:sidebar_header_end]
        self.assertNotIn('btn-close', sidebar_header)

    def test_sidebar_docking_styles_inline_in_head(self):
        """base.html head must contain collegeClueSidebarDockingStyles with padding-left docking."""
        resp = self.client.get(reverse('home'))
        content = resp.content.decode('utf-8')
        self.assertIn('id="collegeClueSidebarDockingStyles"', content)
        self.assertIn('padding-left: var(--cc-sidebar-width)', content)
        self.assertIn('sidebar-open', content)

    def test_accommodation_edit_removes_property_vacant_switch_button(self):
        """Accommodation edit form must not render the is_available switch button beside 'Property is Vacant'."""
        self.client.login(username='housing_owner', password='Password123!')
        resp = self.client.get(reverse('accommodation_edit', kwargs={'acc_id': self.accommodation.id}))
        self.assertEqual(resp.status_code, 200)
        # Switch button removed from form
        self.assertNotContains(resp, 'id="id_is_available"')
        self.assertNotContains(resp, 'Property is Vacant &amp; Open for Student Inquiries')
        # Vacancy controller card is present
        self.assertContains(resp, 'Vacancy Controller')
        self.assertContains(resp, 'VACANT & AVAILABLE')

    def test_accommodation_edit_has_required_fields_and_saves(self):
        """Accommodation edit form displays required housing fields and saves updates."""
        self.client.login(username='housing_owner', password='Password123!')
        resp = self.client.get(reverse('accommodation_edit', kwargs={'acc_id': self.accommodation.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'name="gender"')
        self.assertContains(resp, 'name="food_included"')
        self.assertContains(resp, 'name="security_deposit"')
        self.assertContains(resp, 'name="notice_period"')
        self.assertContains(resp, 'name="gate_closing_time"')
        self.assertContains(resp, 'name="facilities"')
        self.assertContains(resp, 'name="contact_email"')

        # Post update
        post_data = {
            'name': 'Google PG Updated',
            'type': 'PG',
            'college': self.college.id,
            'city': 'Bangalore',
            'address': 'New Address Landmark 123',
            'rent': '25000.00',
            'room_type': 'Double',
            'gender': 'Girls',
            'food_included': 'Optional',
            'security_deposit': '15000.00',
            'notice_period': '15 Days',
            'gate_closing_time': '10:00 PM',
            'facilities': 'AC, High Speed Wi-Fi, Food',
            'contact_phone': '9988776655',
            'contact_email': 'updated@example.com',
        }
        post_resp = self.client.post(reverse('accommodation_edit', kwargs={'acc_id': self.accommodation.id}), post_data)
        self.assertEqual(post_resp.status_code, 302)

        self.accommodation.refresh_from_db()
        self.assertEqual(self.accommodation.name, 'Google PG Updated')
        self.assertEqual(self.accommodation.gender, 'Girls')
        self.assertEqual(self.accommodation.food_included, 'Optional')
        self.assertEqual(self.accommodation.security_deposit, Decimal('15000.00'))
        self.assertEqual(self.accommodation.notice_period, '15 Days')
        self.assertEqual(self.accommodation.gate_closing_time, '10:00 PM')
        self.assertEqual(self.accommodation.contact_email, 'updated@example.com')


class ModernButtonDesignSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.uni_user = User.objects.create_user(
            username='modern_uni_admin',
            email='uni_modern@collegeclue.local',
            password='Password123!'
        )
        self.uni_profile, _ = UserProfile.objects.get_or_create(
            user=self.uni_user,
            defaults={'role': 'university', 'organization_name': 'Modern Technical University'}
        )
        self.uni_profile.role = 'university'
        self.uni_profile.save()
        self.university = University.objects.create(
            name="Modern Technical University",
            city="Bengaluru",
            state="Karnataka",
            established_year=1995,
            rating=Decimal("4.8")
        )
        self.college = College.objects.create(
            university=self.university,
            name="Modern Institute of Technology",
            city="Bengaluru",
            admin_email="uni_modern@collegeclue.local",
            fees=Decimal("220000.00"),
            rating=Decimal("4.8"),
            status='Approved'
        )

    def test_base_html_includes_modern_button_styles_and_v5(self):
        """base.html embeds modern button styles, squircle overrides, and bumps style.css to v5.0."""
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'collegeClueModernButtonStyles')
        self.assertContains(resp, 'style.css?v=5.0')
        self.assertContains(resp, '.btn.rounded-pill')
        self.assertContains(resp, 'border-radius: 9px !important')

    def test_style_css_contains_modern_squircle_button_rules(self):
        """static/css/style.css defines the global modern button architecture."""
        import os
        from django.conf import settings
        css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'style.css')
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        self.assertIn('CollegeClue Modern Button & Control System', css_content)
        self.assertIn('border-radius: 9px !important;', css_content)
        self.assertIn('.btn.rounded-pill', css_content)
        self.assertIn('.btn-primary', css_content)
        self.assertIn('.status-tab-btn', css_content)

    def test_university_applications_page_uses_modern_button_shapes(self):
        """University applications page renders modern button classes and segmented status tabs."""
        self.client.login(username='modern_uni_admin', password='Password123!')
        resp = self.client.get(reverse('university_applications'))
        self.assertEqual(resp.status_code, 200)
        # Status tabs use modern segmented control class
        self.assertContains(resp, 'status-tab-btn')
        # Manage Campuses button does not have rounded-pill
        self.assertContains(resp, 'Manage Campuses')
        self.assertNotContains(resp, 'rounded-pill px-3 py-2 fw-semibold">')

    def test_university_applications_page_course_selection_filter(self):
        """University applications page supports filtering by applied course."""
        self.client.login(username='modern_uni_admin', password='Password123!')
        resp = self.client.get(reverse('university_applications'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'name="course"')
        self.assertContains(resp, '-- All Applied Courses --')

    def test_university_applications_page_removes_filter_button(self):
        """University applications page removes redundant Filter button and uses Enter/auto-submit."""
        self.client.login(username='modern_uni_admin', password='Password123!')
        resp = self.client.get(reverse('university_applications'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, '<i class="bi bi-funnel me-1"></i>Filter')


class CampusClueLandingPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='student_campusclue',
            email='student_campusclue@example.com',
            password='Password123!',
            first_name='Ananya'
        )
        self.user.profile.role = 'student'
        self.user.profile.save()

    def test_unauthenticated_first_page_renders_campusclue_modern_saas_hero(self):
        """Unauthenticated guest visiting homepage sees the modern academic SaaS layout with CollegeClue branding."""
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')

        # CollegeClue branding and topbar
        self.assertIn('College', content)
        self.assertIn('Clue', content)
        self.assertIn('campusclue-topbar', content)
        self.assertIn('EXPLORE • COMPARE • APPLY', content)

        # Center Hero content matching screenshot media_1790975431617.jpg
        self.assertIn('Find the right university for your future.', content)
        self.assertIn('Discover top colleges, compare courses, check fees', content)
        # Search card removed per user request
        self.assertNotIn('campus-search-card', content)

        # 4-metric stats bar with real dynamic database data
        self.assertIn('Universities Listed', content)
        self.assertIn('Courses Available', content)
        self.assertIn('Verified Accommodation', content)
        self.assertIn('Campus Institutes', content)
        self.assertNotIn('700+ Universities Listed', content)
        self.assertNotIn('5,000+ Courses Available', content)

        # Popular Universities section & bottom promo cards
        self.assertIn('Popular Universities', content)
        self.assertIn('Find Accommodation', content)
        self.assertIn('Compare Universities', content)

    def test_authenticated_student_sees_student_portal_and_campusclue(self):
        """Logged-in student sees the clean homepage hero without the top academic banner box."""
        self.client.login(username='student_campusclue', password='Password123!')
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')

        # First box removed per user request
        self.assertNotIn('SHAPING FUTURES', content)
        self.assertNotIn('student-hero-banner', content)
        self.assertIn('Find the right university for your future.', content)
        self.assertIn('Applications', content)

        # Should render modern topbar
        self.assertIn('campusclue-topbar', content)

    def test_sidebar_removes_courses_and_has_neat_sign_out(self):
        """Sidebar removes Courses from MAIN section and renders neat Sign Out button."""
        self.client.login(username='student_campusclue', password='Password123!')
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')

        # Sidebar toggle button has ID
        self.assertIn('id="sidebarToggleBtn"', content)

        # Courses and Accommodation links removed from MAIN section; Near by PG/Flats retained
        sidebar_main = content.split('id="collegeClueSidebar"')[1].split('STUDENT TOOLS')[0]
        self.assertNotIn('Courses', sidebar_main)
        self.assertNotIn('Accommodation', sidebar_main)
        self.assertIn('Near by PG/Flats', sidebar_main)

        # Neat Sign Out button in bottom user card
        self.assertIn('Sign Out', content)























