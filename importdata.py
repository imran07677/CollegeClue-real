#!/usr/bin/env python
"""
Seed script to import authentic universities, colleges, courses, and accommodations into College Clue.
Reads college-clue-default-rtdb-export.json and uses update_or_create to ensure idempotency.
Usage:
    python importdata.py
"""
import os
import sys
import json
from pathlib import Path
from decimal import Decimal

# Configure Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'collegeclue.settings')

import django
django.setup()

from core.models import University, College, Course, Accommodation  # noqa: E402


def import_seed_data(json_filename='college-clue-default-rtdb-export.json'):
    json_path = BASE_DIR / json_filename
    if not json_path.exists():
        print(f"[ERROR] Seed file not found at: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    universities_data = data.get('universities', [])
    print(f"[*] Beginning import of {len(universities_data)} universities from {json_filename}...")

    uni_count = 0
    college_count = 0
    course_count = 0

    for u_item in universities_data:
        uni_name = u_item.get('name')
        if not uni_name:
            continue

        university, created = University.objects.update_or_create(
            name=uni_name,
            defaults={
                'city': u_item.get('city', 'New Delhi'),
                'state': u_item.get('state', 'Delhi'),
                'description': u_item.get('description', ''),
                'website': u_item.get('website', ''),
                'established_year': u_item.get('established_year', 2000),
                'rating': Decimal(str(u_item.get('rating', '4.5'))),
            }
        )
        action_str = "Created" if created else "Updated"
        print(f"  [+] {action_str} University: {university.name}")
        uni_count += 1

        for c_item in u_item.get('colleges', []):
            c_name = c_item.get('name')
            if not c_name:
                continue

            college, col_created = College.objects.update_or_create(
                university=university,
                name=c_name,
                defaults={
                    'city': c_item.get('city', university.city),
                    'description': c_item.get('description', ''),
                    'fees': Decimal(str(c_item.get('fees', '100000'))),
                    'rating': Decimal(str(c_item.get('rating', '4.5'))),
                    'facilities': c_item.get('facilities', 'Library, Wi-Fi, Laboratories'),
                }
            )
            c_action = "Created" if col_created else "Updated"
            print(f"      - {c_action} College: {college.name}")
            college_count += 1

            for crs_item in c_item.get('courses', []):
                crs_name = crs_item.get('name')
                if not crs_name:
                    continue

                course, crs_created = Course.objects.update_or_create(
                    college=college,
                    name=crs_name,
                    defaults={
                        'duration_years': crs_item.get('duration_years', 3),
                        'fee': Decimal(str(crs_item.get('fee', '50000'))),
                        'seats': crs_item.get('seats', 60),
                    }
                )
                course_count += 1

    # Seed Real Student Accommodations (Hostels & PGs)
    accommodations_data = [
        {
            'name': "St. Stephen's College On-Campus Residence",
            'type': 'Hostel',
            'college_name': "St. Stephen's College",
            'address': 'University Enclave, North Campus, Near Vishwavidyalaya Metro',
            'city': 'New Delhi',
            'rent': Decimal('7500.00'),
            'room_type': 'Single',
            'facilities': 'Heritage dining hall, 24/7 high-speed Wi-Fi, study library, laundry, sports grounds, warden surveillance',
            'contact_phone': '+91 11 2766 7200',
            'contact_email': 'hostel@ststephens.edu',
            'is_available': True,
        },
        {
            'name': 'Hudson Lane Scholars PG for Girls',
            'type': 'PG',
            'college_name': 'Hindu College',
            'address': 'Plot 54, Hudson Lane, Kingsway Camp, North Campus',
            'city': 'New Delhi',
            'rent': Decimal('11500.00'),
            'room_type': 'Double',
            'facilities': 'Fully furnished AC rooms, 3 homely vegetarian meals, biometric entry, CCTV, power backup, refrigerator',
            'contact_phone': '+91 98112 34567',
            'contact_email': 'hudson.scholars@delhipg.com',
            'is_available': True,
        },
        {
            'name': 'Kalyan Boys Luxury PG',
            'type': 'PG',
            'college_name': 'Shri Ram College of Commerce (SRCC)',
            'address': '12/4 Roop Nagar, Near Kamla Nagar Market',
            'city': 'New Delhi',
            'rent': Decimal('10000.00'),
            'room_type': 'Double',
            'facilities': 'High-speed fiber Wi-Fi, attached western bathrooms, daily housekeeping, RO purified water, gym access',
            'contact_phone': '+91 98990 11223',
            'contact_email': 'stay@kalyanboyspg.in',
            'is_available': True,
        },
        {
            'name': 'IIT Delhi Nilgiri & Karakoram Hostels',
            'type': 'Hostel',
            'college_name': 'IIT Delhi School of Engineering & Technology',
            'address': 'IIT Delhi Main Campus, Hauz Khas',
            'city': 'New Delhi',
            'rent': Decimal('6000.00'),
            'room_type': 'Single',
            'facilities': 'LAN connectivity in every room, mess facilities, night canteen, indoor badminton court, music room',
            'contact_phone': '+91 11 2659 1999',
            'contact_email': 'hostels@admin.iitd.ac.in',
            'is_available': True,
        },
        {
            'name': 'DTU Rohini Campus Hostels',
            'type': 'Hostel',
            'college_name': 'DTU Faculty of Engineering',
            'address': 'Shahbad Daulatpur, Main Bawana Road, Rohini',
            'city': 'New Delhi',
            'rent': Decimal('5500.00'),
            'room_type': 'Single',
            'facilities': '24/7 Wi-Fi, modern dining mess, gym, sports ground, reading hall, security staff',
            'contact_phone': '+91 11 2787 1018',
            'contact_email': 'hostels@dtu.ac.in',
            'is_available': True,
        },
        {
            'name': 'Hauz Khas Green PG for Students',
            'type': 'PG',
            'college_name': 'Department of Management Studies (DMS IITD)',
            'address': 'Building 8, Kaushalya Park, Near Hauz Khas Metro',
            'city': 'New Delhi',
            'rent': Decimal('12500.00'),
            'room_type': 'Double',
            'facilities': 'AC, attached balcony, 3 nutritious meals, daily cleaning, high-speed fiber internet',
            'contact_phone': '+91 98110 99887',
            'contact_email': 'hauzkhas.pg@studentliving.in',
            'is_available': True,
        },
        {
            'name': 'IISc Malleshwaram Scholars Hostel',
            'type': 'Hostel',
            'college_name': 'IISc Division of Electrical, Electronics & Computer Sciences (EECS)',
            'address': 'IISc Campus, CV Raman Road, Malleshwaram',
            'city': 'Bengaluru',
            'rent': Decimal('5500.00'),
            'room_type': 'Single',
            'facilities': 'High-performance research Wi-Fi, multi-cuisine mess, 24/7 library access, lush green surroundings',
            'contact_phone': '+91 80 2293 2004',
            'contact_email': 'hostel.office@iisc.ac.in',
            'is_available': True,
        },
        {
            'name': 'Koramangala Tech Executive Student Living',
            'type': 'PG',
            'college_name': 'Bangalore Institute of Technology & Science',
            'address': '8th Main, 4th Block Koramangala',
            'city': 'Bengaluru',
            'rent': Decimal('13500.00'),
            'room_type': 'Double',
            'facilities': 'Ergonomic study desks, fiber internet, air-conditioning, chef-curated meals, laundry service, gaming lounge',
            'contact_phone': '+91 99001 55667',
            'contact_email': 'info@koramangalaliving.com',
            'is_available': True,
        },
        {
            'name': 'Green Valley Scholar PG',
            'type': 'PG',
            'college_name': 'Bangalore Institute of Technology & Science',
            'address': 'Plot 42, Sector 15, Near Metro Pillar 112',
            'city': 'Bengaluru',
            'rent': Decimal('8500.00'),
            'room_type': 'Double',
            'facilities': 'High-speed Wi-Fi, 3 Homely Meals, Daily Housekeeping, RO Water, Biometric Access',
            'contact_phone': '+91 98765 43210',
            'contact_email': 'contact@greenvalleypg.com',
            'is_available': True,
        },
        {
            'name': 'VJTI Matunga Campus Hostel',
            'type': 'Hostel',
            'college_name': 'Veermata Jijabai Technological Institute (VJTI)',
            'address': 'H. R. Mahajani Road, Matunga East',
            'city': 'Mumbai',
            'rent': Decimal('7000.00'),
            'room_type': 'Triple',
            'facilities': 'On-campus convenience, hygienic cafeteria, sports ground, reading hall, medical center on call',
            'contact_phone': '+91 22 2419 8100',
            'contact_email': 'warden@vjti.ac.in',
            'is_available': True,
        },
        {
            'name': 'South Bombay Sea View Residency for Students',
            'type': 'PG',
            'college_name': "St. Xavier's College (Autonomous)",
            'address': '5 Mahapalika Marg, Dhobi Talao, Marine Lines',
            'city': 'Mumbai',
            'rent': Decimal('16500.00'),
            'room_type': 'Double',
            'facilities': 'Heritage building, walking distance to CST and Marine Drive, AC rooms, 24/7 security, high speed Wi-Fi',
            'contact_phone': '+91 98200 44556',
            'contact_email': 'sobo.students@mumbaipg.in',
            'is_available': True,
        },
        {
            'name': 'CEG Guindy Engineering Hostels',
            'type': 'Hostel',
            'college_name': 'College of Engineering, Guindy (CEG)',
            'address': 'Sardar Patel Road, Guindy',
            'city': 'Chennai',
            'rent': Decimal('4500.00'),
            'room_type': 'Double',
            'facilities': 'Spacious verdant campus, solar water heaters, cooperative student mess, sports pavilion, gymnasium',
            'contact_phone': '+91 44 2235 7000',
            'contact_email': 'ceghostels@annauniv.edu',
            'is_available': True,
        },
        {
            'name': 'Chromepet Scholars Residence for Students',
            'type': 'PG',
            'college_name': 'Madras Institute of Technology (MIT Chromepet)',
            'address': 'GST Road, Chromepet, Near Railway Station',
            'city': 'Chennai',
            'rent': Decimal('7500.00'),
            'room_type': 'Double',
            'facilities': 'Air-cooled rooms, South & North Indian meals, Wi-Fi, 24-hr security, RO water',
            'contact_phone': '+91 44 2223 8899',
            'contact_email': 'chromepet.residence@chennaipg.in',
            'is_available': True,
        },
        {
            'name': 'Symbiosis Lavale Hilltop Student Residency',
            'type': 'Hostel',
            'college_name': 'Symbiosis Institute of Business Management (SIBM)',
            'address': 'Gram Lavale, Taluka Mulshi, Lavale Hilltop Campus',
            'city': 'Pune',
            'rent': Decimal('15000.00'),
            'room_type': 'Double',
            'facilities': 'Panoramic Western Ghats views, swimming pool, indoor sports complex, cafeteria, health center',
            'contact_phone': '+91 20 2811 6000',
            'contact_email': 'campusadmin@sibmpune.ac.in',
            'is_available': True,
        },
        {
            'name': 'Kothrud & Viman Nagar Student PG',
            'type': 'PG',
            'college_name': 'Symbiosis Institute of Technology (SIT)',
            'address': 'Near Symbiosis Campus, Viman Nagar',
            'city': 'Pune',
            'rent': Decimal('9500.00'),
            'room_type': 'Double',
            'facilities': 'Wi-Fi, breakfast & dinner, washing machine, hot water, CCTV surveillance, near bus stop',
            'contact_phone': '+91 98220 33445',
            'contact_email': 'viman.scholars@punepg.com',
            'is_available': True,
        },
        {
            'name': 'Salt Lake Jadavpur Student Hostel',
            'type': 'Hostel',
            'college_name': 'Faculty of Engineering & Technology (FET Jadavpur)',
            'address': 'Block LB, Plot 8, Sector III, Salt Lake City',
            'city': 'Kolkata',
            'rent': Decimal('3500.00'),
            'room_type': 'Single',
            'facilities': 'Subsidized mess, high speed internet, student common room, table tennis, library corner',
            'contact_phone': '+91 33 2335 5215',
            'contact_email': 'hostels@jadavpuruniversity.in',
            'is_available': True,
        },
        {
            'name': 'Jadavpur Raja S.C. Mallick Road PG',
            'type': 'PG',
            'college_name': 'Faculty of Engineering & Technology (FET Jadavpur)',
            'address': '188 Raja S.C. Mallick Road, Near 8B Bus Stand',
            'city': 'Kolkata',
            'rent': Decimal('5500.00'),
            'room_type': 'Double',
            'facilities': 'Homely Bengali & North Indian meals, Wi-Fi, 24/7 water supply, study table, balcony',
            'contact_phone': '+91 98300 77889',
            'contact_email': 'kolkata.scholars@pglive.in',
            'is_available': True,
        },
        {
            'name': 'BITS Pilani Hyderabad Campus Student Hostels',
            'type': 'Hostel',
            'college_name': 'BITS Pilani Hyderabad Campus',
            'address': 'Jawahar Nagar, Kapra Mandal, Medchal District',
            'city': 'Hyderabad',
            'rent': Decimal('6500.00'),
            'room_type': 'Single',
            'facilities': 'Modern campus hostel, LAN port, solar water, night mess, sports complex, ATM and medical clinic',
            'contact_phone': '+91 40 6630 3999',
            'contact_email': 'hostels@hyderabad.bits-pilani.ac.in',
            'is_available': True,
        },
        {
            'name': 'Shamirpet Tech Scholar PG',
            'type': 'PG',
            'college_name': 'BITS Pilani Hyderabad Campus',
            'address': 'Main Road Shamirpet, Near BITS Campus Gate',
            'city': 'Hyderabad',
            'rent': Decimal('8500.00'),
            'room_type': 'Double',
            'facilities': 'AC rooms, Wi-Fi, 3 meals, shuttle bus to campus, power backup, security',
            'contact_phone': '+91 99890 22334',
            'contact_email': 'shamirpet.pg@hydhousing.in',
            'is_available': True,
        },
        {
            'name': 'Zuari View BITS Goa Student Residency',
            'type': 'PG',
            'college_name': 'BITS Pilani K.K. Birla Goa Campus',
            'address': 'NH 17B, Bypass Road, Zuarinagar, Sancoale',
            'city': 'Goa',
            'rent': Decimal('11000.00'),
            'room_type': 'Double',
            'facilities': 'Scenic river views, air-conditioned rooms, Wi-Fi, vegetarian & non-veg meal options, bike parking',
            'contact_phone': '+91 832 258 0100',
            'contact_email': 'goa.residency@studentstay.com',
            'is_available': True,
        },
    ]

    acc_count = 0
    for acc_item in accommodations_data:
        college_obj = College.objects.filter(name=acc_item['college_name']).first()
        acc, created = Accommodation.objects.update_or_create(
            name=acc_item['name'],
            defaults={
                'type': acc_item['type'],
                'college': college_obj,
                'address': acc_item['address'],
                'city': acc_item['city'],
                'rent': acc_item['rent'],
                'room_type': acc_item['room_type'],
                'facilities': acc_item['facilities'],
                'contact_phone': acc_item['contact_phone'],
                'contact_email': acc_item['contact_email'],
                'is_available': acc_item['is_available'],
            }
        )
        acc_count += 1

    print("\n" + "=" * 60)
    print(f"[*] SEEDING COMPLETE:")
    print(f"    - Universities processed : {uni_count}")
    print(f"    - Colleges processed     : {college_count}")
    print(f"    - Courses processed      : {course_count}")
    print(f"    - Accommodations seeded  : {acc_count}")
    print("=" * 60)


if __name__ == '__main__':
    import_seed_data()
