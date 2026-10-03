# College Clue

**College Clue** is a centralized college admission and accommodation discovery platform built with Django 5.x and Django REST Framework. Students can explore accredited universities, compare colleges side-by-side on fees and amenities, register for courses directly with dynamic form validation, and discover campus accommodations (PGs and hostels).

---

## Key Features

1. **University & College Directory**:
   - Comprehensive university catalog with city, state, NIRF ratings, and historical establishment data.
   - College listings with affiliated universities, tuition fee breakdowns, and campus amenities.
   - Multi-parameter filtering by search keyword, city, course title, and fee ranges.

2. **Side-by-Side College Comparison**:
   - Session-backed comparison cart supporting 2–4 colleges.
   - Side-by-side comparative table highlighting fees, ratings, offered courses, and amenities.

3. **Student Accommodation (PGs & Hostels)**:
   - Verified student housing catalog with rent, room configurations (Single/Double/Triple), and amenities.
   - Direct landlord contact details and proximity badges for affiliated colleges.

4. **Admission Registration & Automated Emailing**:
   - Dynamic course dropdown populated via JSON API and filtered by selected college.
   - Real-time client-side submission progress bar.
   - Automatic generation of unique UUID-based Registration IDs.
   - Confirmation email notification dispatched automatically using transactional email templates.
   - Celebration screen with canvas-confetti animation.

5. **Student Wishlist**:
   - Bookmarking capability for universities (requires login).

6. **Django REST Framework (DRF) API**:
   - Read-only endpoints: `/api/universities/`, `/api/colleges/`, `/api/accommodations/`.
   - Creation endpoint: `/api/register/` (creates admission registrations and dispatches confirmation emails).
   - Dynamic browsable API enabled during `DEBUG=True`.

7. **Production Observability & Extensibility**:
   - Custom `RequestLoggingMiddleware` logging every request method, path, and user.
   - Custom Django template tags (`inr` currency formatter and `active_link` navigation highlighter).
   - Idempotent seed script (`importdata.py`) for automated database loading.

---

## Project Structure

```text
collegeclue/
├── manage.py
├── importdata.py
├── college-clue-default-rtdb-export.json
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── core/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── middleware.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   ├── signals.py
│   ├── tests.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── migrations/
│   │   └── __init__.py
│   ├── templatetags/
│   │   ├── __init__.py
│   │   └── core_extras.py
│   └── templates/
│       ├── account/
│       │   ├── login.html
│       │   ├── logout.html
│       │   └── register.html
│       └── core/
│           ├── base.html
│           ├── home.html
│           ├── university_list.html
│           ├── university_detail.html
│           ├── college_list.html
│           ├── college_detail.html
│           ├── compare.html
│           ├── accommodation_list.html
│           ├── accommodation_detail.html
│           ├── wishlist.html
│           ├── registration_form.html
│           ├── registration_success.html
│           └── emails/
│               └── registration_confirmation.txt
└── collegeclue/
    ├── __init__.py
    ├── settings.py
    ├── urls.py
    ├── asgi.py
    ├── wsgi.py
    └── templates/
        └── base.html

Static files:
static/
├── css/
│   └── style.css
└── js/
    ├── confetti-init.js
    └── progress-bar.js

Media (created at runtime):
media/
└── logos/ , accommodations/
```

---

## Getting Started

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Environment Setup
```bash
# Clone the repository and enter the directory
cd collegeclue

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
venv\Scripts\Activate.ps1
# On macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
```

### 3. Database Migration
```bash
python manage.py makemigrations core
python manage.py migrate
```

### 4. Create Administrator Account
```bash
python manage.py createsuperuser
```

### 5. Seed Initial Data
```bash
python importdata.py
```

### 6. Run Development Server
```bash
python manage.py runserver
```
Visit the application in your browser:
- Web Portal: `http://127.0.0.1:8000/`
- Django Admin: `http://127.0.0.1:8000/admin/`
- REST API Root: `http://127.0.0.1:8000/api/`

---

## Running Automated Tests

Run the built-in test suite:
```bash
python manage.py test core
```

---

## REST API Examples

### List Universities
```bash
curl -X GET http://127.0.0.1:8000/api/universities/ -H "Accept: application/json"
```

### List Colleges
```bash
curl -X GET http://127.0.0.1:8000/api/colleges/ -H "Accept: application/json"
```

### Submit Student Admission Registration
```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Pooja Verma",
    "email": "pooja.verma@example.com",
    "phone": "9811223344",
    "college": 1,
    "course": 1
  }'
```

---

## Production Deployment Notes

1. **Database**: Swap to PostgreSQL by configuring `DB_ENGINE=django.db.backends.postgresql` and providing `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` in `.env`. Install `psycopg2-binary`.
2. **Environment Variables**:
   - Set `DEBUG=False` in production `.env`.
   - Update `SECRET_KEY` with a cryptographically secure random string.
   - Configure `ALLOWED_HOSTS` with your production domain (e.g. `collegeclue.com`).
3. **Email Backend**:
   - Set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`.
   - Configure SMTP server details (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`).
4. **Static & Media Collection**:
   ```bash
   python manage.py collectstatic --noinput
   ```
   Serve static files through Nginx or Whitenoise, and media files via Amazon S3 / Cloud Storage.
5. **WSGI / ASGI Server**: Run the application behind Gunicorn or Uvicorn managed by systemd or Docker:
   ```bash
   gunicorn collegeclue.wsgi:application --bind 0.0.0.0:8000 --workers 4
   ```
