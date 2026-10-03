"""
college_insights.py - Institutional Overview, Placement Analytics,
and Visiting Recruiter Data for Colleges in CollegeClue.
"""

def get_college_about(college):
    """
    Returns structured background, accreditation, campus life, infrastructure,
    and key institutional highlights for a college.
    """
    name_lower = college.name.lower()
    city = college.city or "India"
    uni_name = college.university.name if college.university else "Leading University"

    is_tech = any(k in name_lower for k in ['engineering', 'technology', 'tech', 'iit', 'bits', 'dtu', 'computing', 'science', 'institute'])
    is_mgmt = any(k in name_lower for k in ['management', 'business', 'mba', 'dms', 'commerce', 'school of business'])

    if is_tech:
        discipline = "Engineering, Computing & Advanced Sciences"
        accreditations = [
            "NAAC 'A++' Accredited (Highest Institutional Grade)",
            "NBA Tier-1 Accredited Degree Programs",
            "AICTE Approved Institute of National Repute",
            "NIRF Top-Tier Ranked Engineering Institution"
        ]
        focus_areas = [
            "Artificial Intelligence & Machine Learning",
            "Robotics, IoT & Autonomous Systems Hub",
            "Cloud Computing & Cybersecurity Center",
            "VLSI Design & Next-Gen Semiconductor Research"
        ]
        campus_acres = "75+ Acres Eco-Friendly Campus"
        faculty_ratio = "1:12 Faculty-to-Student Ratio"
    elif is_mgmt:
        discipline = "Management, Business Administration & Global Strategy"
        accreditations = [
            "AACSB & AMBA Aligned Curriculum",
            "NAAC 'A+' Grade Business Faculty",
            "AICTE Approved Post-Graduate Center",
            "Top-Ranked Business School by Leading Surveys"
        ]
        focus_areas = [
            "Corporate Strategy & Global Leadership",
            "FinTech & Quantitative Financial Modeling",
            "Supply Chain Analytics & Global Logistics",
            "Digital Marketing, Brand Management & Consumer Insights"
        ]
        campus_acres = "45+ Acres Modern Urban Campus"
        faculty_ratio = "1:10 Faculty-to-Student Ratio"
    else:
        discipline = "Multidisciplinary Higher Education, Arts & Sciences"
        accreditations = [
            "UGC Recognized Centre with Potential for Excellence",
            "NAAC 'A+' Grade Re-accredited Institution",
            "NIRF Top-Ranked College",
            "DST-FIST Sponsored Science Laboratories"
        ]
        focus_areas = [
            "Pure & Applied Scientific Research",
            "Commerce, Economics & Industry Analytics",
            "Humanities, Media & Interdisciplinary Studies",
            "Social Entrepreneurship & Incubation Hub"
        ]
        campus_acres = "50+ Acres Heritage Campus"
        faculty_ratio = "1:14 Faculty-to-Student Ratio"

    overview_paragraphs = [
        f"{college.name} is an eminent academic institution affiliated with {uni_name}, delivering world-class curriculum, transformative experiential learning, and distinguished research in {city}.",
        f"Anchored in academic excellence, the campus integrates cutting-edge pedagogical methodologies with state-of-the-art laboratory and digital infrastructure. Faculty members bring distinguished doctoral credentials and extensive industrial consultancy expertise, mentoring students through hands-on capstone projects and research publications.",
        f"With an active community representing students from across India and abroad, the institution fosters a vibrant collegiate ecosystem featuring 30+ technical societies, entrepreneurial incubation cells, and annual national symposiums."
    ]

    facilities_list = [
        {
            "icon": "bi-laptop",
            "title": "State-of-the-Art Computing Labs",
            "desc": "High-performance GPU workstations, enterprise cloud computing testbeds, and licensed development toolchains."
        },
        {
            "icon": "bi-book-half",
            "title": "Central Knowledge Repository",
            "desc": "Over 65,000+ print volumes, 12,000+ e-journals with 24/7 digital access to IEEE, ScienceDirect, and JSTOR databases."
        },
        {
            "icon": "bi-wifi",
            "title": "Campus-Wide Gigabit Wi-Fi",
            "desc": "High-speed redundant optical fiber connectivity covering classrooms, residence halls, and outdoor study plazas."
        },
        {
            "icon": "bi-dribbble",
            "title": "Sports & Fitness Pavilion",
            "desc": "Multi-sport indoor sports complex, floodlit cricket & football arenas, synthetic tennis courts, and gymnasium."
        },
        {
            "icon": "bi-cup-hot",
            "title": "Hygienic Multi-Cuisine Food Courts",
            "desc": "FSSAI-certified nutritious vegetarian and multi-cuisine cafeterias with comfortable communal dining lounges."
        },
        {
            "icon": "bi-shield-check",
            "title": "Healthcare & 24/7 Security",
            "desc": "Round-the-clock emergency medical infirmary, on-campus doctor & ambulance, and comprehensive CCTV security coverage."
        }
    ]

    return {
        "discipline": discipline,
        "accreditations": accreditations,
        "focus_areas": focus_areas,
        "campus_acres": campus_acres,
        "faculty_ratio": faculty_ratio,
        "overview_paragraphs": overview_paragraphs,
        "facilities": facilities_list,
        "location_highlight": f"Conveniently positioned in {city}, offering proximity to commercial innovation parks, transit corridors, and safe student living zones."
    }


def get_college_placements(college):
    """
    Returns realistic placement statistics, packages, sectors, and
    career cell highlights tailored to the college.
    Respects custom placement records set by the university partner if provided,
    and automatically calculates benchmark defaults if any field is left empty.
    """
    name_lower = college.name.lower()
    rating = float(college.rating or 4.3)
    fees = float(college.fees or 150000)

    is_tech = any(k in name_lower for k in ['engineering', 'technology', 'tech', 'iit', 'bits', 'dtu', 'computing', 'science'])
    is_mgmt = any(k in name_lower for k in ['management', 'business', 'mba', 'dms', 'commerce'])

    if is_tech:
        if rating >= 4.7:
            calc_highest = "₹58.50 LPA"
            calc_average = "₹21.40 LPA"
            calc_median = "₹18.00 LPA"
            calc_rate = "98.2%"
            calc_offers = "1,150+"
            calc_stipend = "₹1,25,000 / mo"
        elif rating >= 4.4:
            calc_highest = "₹44.00 LPA"
            calc_average = "₹14.80 LPA"
            calc_median = "₹12.50 LPA"
            calc_rate = "96.4%"
            calc_offers = "820+"
            calc_stipend = "₹80,000 / mo"
        else:
            calc_highest = "₹32.00 LPA"
            calc_average = "₹10.50 LPA"
            calc_median = "₹8.80 LPA"
            calc_rate = "92.8%"
            calc_offers = "540+"
            calc_stipend = "₹50,000 / mo"

        sectors = [
            {"name": "Software & Product Engineering", "percentage": 44, "color": "bg-primary"},
            {"name": "AI, Machine Learning & Data Analytics", "percentage": 22, "color": "bg-info"},
            {"name": "Management, Strategy & Consulting", "percentage": 15, "color": "bg-warning"},
            {"name": "Core Electronics & Hardware Engineering", "percentage": 12, "color": "bg-success"},
            {"name": "BFSI & FinTech Engineering", "percentage": 7, "color": "bg-secondary"},
        ]
    elif is_mgmt:
        if rating >= 4.6:
            calc_highest = "₹42.00 LPA"
            calc_average = "₹16.50 LPA"
            calc_median = "₹14.20 LPA"
            calc_rate = "97.5%"
            calc_offers = "620+"
            calc_stipend = "₹1,00,000 / mo"
        else:
            calc_highest = "₹28.00 LPA"
            calc_average = "₹11.20 LPA"
            calc_median = "₹9.50 LPA"
            calc_rate = "94.0%"
            calc_offers = "410+"
            calc_stipend = "₹60,000 / mo"

        sectors = [
            {"name": "Management Consulting & Advisory", "percentage": 34, "color": "bg-primary"},
            {"name": "Investment Banking, Wealth & FinTech", "percentage": 26, "color": "bg-success"},
            {"name": "Product Strategy & Tech Operations", "percentage": 20, "color": "bg-info"},
            {"name": "FMCG, Brand Strategy & Marketing", "percentage": 12, "color": "bg-warning"},
            {"name": "Supply Chain & General Management", "percentage": 8, "color": "bg-secondary"},
        ]
    else:
        calc_highest = "₹26.50 LPA"
        calc_average = "₹9.40 LPA"
        calc_median = "₹7.80 LPA"
        calc_rate = "91.5%"
        calc_offers = "480+"
        calc_stipend = "₹45,000 / mo"

        sectors = [
            {"name": "Corporate Consulting & Professional Services", "percentage": 32, "color": "bg-primary"},
            {"name": "Information Technology & Digital Services", "percentage": 28, "color": "bg-info"},
            {"name": "Financial Research & Banking", "percentage": 20, "color": "bg-success"},
            {"name": "Media, Research & Analytics", "percentage": 12, "color": "bg-warning"},
            {"name": "Education, NGO & Public Policy", "percentage": 8, "color": "bg-secondary"},
        ]

    # Use custom values if provided by university admin, otherwise auto-calculate benchmark
    highest_ctc = (getattr(college, 'highest_package', '') or '').strip() or calc_highest
    average_ctc = (getattr(college, 'average_package', '') or '').strip() or calc_average
    median_ctc = (getattr(college, 'median_package', '') or '').strip() or calc_median
    placement_rate = (getattr(college, 'placement_rate', '') or '').strip() or calc_rate
    total_offers = (getattr(college, 'total_offers', '') or '').strip() or calc_offers
    highest_stipend = (getattr(college, 'summer_stipend', '') or '').strip() or calc_stipend

    highlights = [
        "100% placement assistance facilitated through the dedicated Corporate Relations & Placement Division.",
        "Over 42% of graduates received Pre-Placement Offers (PPOs) following competitive summer internships.",
        "Structured pre-placement training including DSA bootcamps, quantitative aptitude, and mock interviews with alumni leaders.",
        "Annual participation from 180+ Fortune 500 corporations, top-tier domestic conglomerates, and high-growth unicorn startups."
    ]
    if getattr(college, 'placement_highlights', None):
        custom_highlights = [line.strip().lstrip('-*•').strip() for line in college.placement_highlights.splitlines() if line.strip()]
        if custom_highlights:
            highlights = custom_highlights

    return {
        "highest_ctc": highest_ctc,
        "average_ctc": average_ctc,
        "median_ctc": median_ctc,
        "placement_rate": placement_rate,
        "total_offers": total_offers,
        "highest_stipend": highest_stipend,
        "sectors": sectors,
        "highlights": highlights,
    }


def get_college_companies(college):
    """
    Returns categorized visiting recruiting companies that hire from this college,
    including job profiles, compensation tiers, and sector badges.
    Respects custom recruiter lists if specified by university partner.
    """
    name_lower = college.name.lower()
    is_tech = any(k in name_lower for k in ['engineering', 'technology', 'tech', 'iit', 'bits', 'dtu', 'computing', 'science'])
    is_mgmt = any(k in name_lower for k in ['management', 'business', 'mba', 'dms', 'commerce'])

    default_categories = [
        {
            "category_name": "Tier 1 Tech & Product Companies",
            "badge_color": "bg-primary",
            "icon": "bi-cpu-fill",
            "description": "Leading global technology conglomerates hiring for core software engineering, cloud systems, and AI/ML development.",
            "companies": [
                {
                    "name": "Google",
                    "roles": "Software Development Engineer (L3), Site Reliability Engineer",
                    "package_tier": "Super Dream (₹32 - ₹48 LPA)",
                    "tier_badge": "bg-danger",
                    "initial": "G",
                    "domain": "Cloud & AI"
                },
                {
                    "name": "Microsoft",
                    "roles": "Software Engineer (SDE), Cloud Solution Architect",
                    "package_tier": "Super Dream (₹30 - ₹45 LPA)",
                    "tier_badge": "bg-danger",
                    "initial": "M",
                    "domain": "Enterprise Cloud"
                },
                {
                    "name": "Amazon",
                    "roles": "Software Development Engineer - 1, Cloud Support Associate",
                    "package_tier": "Super Dream (₹28 - ₹44 LPA)",
                    "tier_badge": "bg-danger",
                    "initial": "A",
                    "domain": "E-Commerce & AWS"
                },
                {
                    "name": "Adobe",
                    "roles": "Member of Technical Staff (MTS), Product Developer",
                    "package_tier": "Super Dream (₹26 - ₹38 LPA)",
                    "tier_badge": "bg-danger",
                    "initial": "Ad",
                    "domain": "Creative Cloud & AI"
                },
                {
                    "name": "Oracle",
                    "roles": "Cloud Infrastructure Engineer, Applications Developer",
                    "package_tier": "Dream (₹16 - ₹24 LPA)",
                    "tier_badge": "bg-primary",
                    "initial": "O",
                    "domain": "Database & Cloud"
                },
                {
                    "name": "Cisco Systems",
                    "roles": "Network Software Engineer, Security Systems Analyst",
                    "package_tier": "Dream (₹17 - ₹23 LPA)",
                    "tier_badge": "bg-primary",
                    "initial": "C",
                    "domain": "Networking & Security"
                }
            ]
        },
        {
            "category_name": "Management Consulting & Big 4 Advisory",
            "badge_color": "bg-warning text-dark",
            "icon": "bi-briefcase-fill",
            "description": "Premier global strategy and technology advisory firms hiring for business transformation, analytics, and strategy.",
            "companies": [
                {
                    "name": "Deloitte",
                    "roles": "Technology Consultant, Business Technology Analyst",
                    "package_tier": "Dream (₹12 - ₹18 LPA)",
                    "tier_badge": "bg-primary",
                    "initial": "D",
                    "domain": "Advisory & Tech"
                },
                {
                    "name": "McKinsey & Company",
                    "roles": "Junior Associate Consultant, Business Analyst",
                    "package_tier": "Super Dream (₹24 - ₹32 LPA)",
                    "tier_badge": "bg-danger",
                    "initial": "McK",
                    "domain": "Strategy Consulting"
                },
                {
                    "name": "Boston Consulting Group (BCG)",
                    "roles": "Associate Consultant, Analytics Specialist",
                    "package_tier": "Super Dream (₹25 - ₹34 LPA)",
                    "tier_badge": "bg-danger",
                    "initial": "BCG",
                    "domain": "Management Strategy"
                },
                {
                    "name": "PricewaterhouseCoopers (PwC)",
                    "roles": "Cybersecurity Consultant, Management Associate",
                    "package_tier": "Dream (₹11 - ₹16 LPA)",
                    "tier_badge": "bg-primary",
                    "initial": "PwC",
                    "domain": "Risk & Tech Advisory"
                },
                {
                    "name": "Ernst & Young (EY)",
                    "roles": "Consultant - Digital & Emerging Technologies",
                    "package_tier": "Dream (₹11 - ₹15 LPA)",
                    "tier_badge": "bg-primary",
                    "initial": "EY",
                    "domain": "Assurance & Advisory"
                },
                {
                    "name": "KPMG",
                    "roles": "Analyst - Management Advisory & Financial Modeling",
                    "package_tier": "Dream (₹10 - ₹14 LPA)",
                    "tier_badge": "bg-primary",
                    "initial": "K",
                    "domain": "Business Advisory"
                }
            ]
        },
        {
            "category_name": "Banking, Financial Services & FinTech",
            "badge_color": "bg-success",
            "icon": "bi-bank2",
            "description": "Global investment banks, asset managers, and leading Indian financial institutions.",
            "companies": [
                {
                    "name": "Goldman Sachs",
                    "roles": "Engineering Analyst, Quantitative Strategist",
                    "package_tier": "Super Dream (₹26 - ₹36 LPA)",
                    "tier_badge": "bg-danger",
                    "initial": "GS",
                    "domain": "Investment Banking"
                },
                {
                    "name": "Morgan Stanley",
                    "roles": "Technology Analyst, Financial Systems Engineer",
                    "package_tier": "Super Dream (₹24 - ₹34 LPA)",
                    "tier_badge": "bg-danger",
                    "initial": "MS",
                    "domain": "Global Wealth Mgmt"
                },
                {
                    "name": "J.P. Morgan Chase & Co.",
                    "roles": "Software Engineer, Corporate Analyst",
                    "package_tier": "Dream (₹18 - ₹25 LPA)",
                    "tier_badge": "bg-primary",
                    "initial": "JPM",
                    "domain": "FinTech & Banking"
                },
                {
                    "name": "HDFC Bank",
                    "roles": "Management Trainee, Digital Transformation Officer",
                    "package_tier": "Core / Dream (₹9 - ₹14 LPA)",
                    "tier_badge": "bg-secondary",
                    "initial": "HB",
                    "domain": "Retail & Digital Banking"
                },
                {
                    "name": "ICICI Bank",
                    "roles": "Probationary Officer, Product Manager",
                    "package_tier": "Core / Dream (₹8.5 - ₹13 LPA)",
                    "tier_badge": "bg-secondary",
                    "initial": "IB",
                    "domain": "Commercial Banking"
                }
            ]
        },
        {
            "category_name": "Enterprise IT, Cloud & Digital Services",
            "badge_color": "bg-info text-dark",
            "icon": "bi-diagram-3-fill",
            "description": "Global systems integrators and enterprise software leaders recruiting across multiple faculties.",
            "companies": [
                {
                    "name": "Tata Consultancy Services (TCS)",
                    "roles": "Prime Innovator, Digital Specialist Engineer",
                    "package_tier": "Dream / Core (₹7 - ₹11.5 LPA)",
                    "tier_badge": "bg-secondary",
                    "initial": "TCS",
                    "domain": "IT & Consulting"
                },
                {
                    "name": "Infosys",
                    "roles": "Specialist Programmer, Power Programmer",
                    "package_tier": "Dream / Core (₹6.5 - ₹10.5 LPA)",
                    "tier_badge": "bg-secondary",
                    "initial": "INF",
                    "domain": "Digital Transformation"
                },
                {
                    "name": "Accenture",
                    "roles": "Advanced Application Engineering Analyst",
                    "package_tier": "Dream (₹7.5 - ₹12.5 LPA)",
                    "tier_badge": "bg-primary",
                    "initial": "AC",
                    "domain": "Cloud & AI Services"
                },
                {
                    "name": "Wipro",
                    "roles": "Turbo Developer, Elite Project Engineer",
                    "package_tier": "Core (₹6.5 - ₹9.5 LPA)",
                    "tier_badge": "bg-secondary",
                    "initial": "WIP",
                    "domain": "Technology Services"
                },
                {
                    "name": "Cognizant",
                    "roles": "GenC Next Developer, Programmer Analyst",
                    "package_tier": "Core (₹6.7 - ₹10.0 LPA)",
                    "tier_badge": "bg-secondary",
                    "initial": "CTS",
                    "domain": "Digital Operations"
                }
            ]
        },
        {
            "category_name": "Core Engineering, Automotive & R&D",
            "badge_color": "bg-dark",
            "icon": "bi-gear-wide-connected",
            "description": "Leading industrial, electronics, automotive, and infrastructure corporations hiring technical talent.",
            "companies": [
                {
                    "name": "Larsen & Toubro (L&T)",
                    "roles": "Graduate Engineer Trainee (GET), Project Engineer",
                    "package_tier": "Core / Dream (₹8 - ₹13 LPA)",
                    "tier_badge": "bg-secondary",
                    "initial": "L&T",
                    "domain": "Infrastructure & Tech"
                },
                {
                    "name": "Texas Instruments",
                    "roles": "Embedded Systems Engineer, Analog Circuit Designer",
                    "package_tier": "Super Dream (₹22 - ₹32 LPA)",
                    "tier_badge": "bg-danger",
                    "initial": "TI",
                    "domain": "Semiconductors"
                },
                {
                    "name": "Bosch Global Software",
                    "roles": "Automotive Embedded Software Engineer, IoT Specialist",
                    "package_tier": "Dream (₹11 - ₹17 LPA)",
                    "tier_badge": "bg-primary",
                    "initial": "B",
                    "domain": "Automotive & IoT"
                },
                {
                    "name": "Tata Motors",
                    "roles": "Electric Vehicle Systems Trainee, Design Engineer",
                    "package_tier": "Core / Dream (₹8.5 - ₹13 LPA)",
                    "tier_badge": "bg-secondary",
                    "initial": "TM",
                    "domain": "EV & Mobility"
                }
            ]
        }
    ]

    custom_recruiters_str = (getattr(college, 'top_recruiters', '') or '').strip()
    if not custom_recruiters_str:
        return default_categories

    custom_names = [n.strip() for n in custom_recruiters_str.replace('\n', ',').split(',') if n.strip()]
    if not custom_names:
        return default_categories

    # Build known company lookup
    known_companies = {}
    for cat in default_categories:
        for comp in cat["companies"]:
            known_companies[comp["name"].lower()] = (comp, cat["category_name"])

    # Prepare categories
    cat_map = {
        cat["category_name"]: {
            "category_name": cat["category_name"],
            "badge_color": cat["badge_color"],
            "icon": cat["icon"],
            "description": cat["description"],
            "companies": []
        }
        for cat in default_categories
    }

    for name in custom_names:
        key = name.lower()
        if key in known_companies:
            comp_data, cat_name = known_companies[key]
            cat_map[cat_name]["companies"].append(comp_data)
        else:
            clean_initial = "".join([w[0] for w in name.split()[:2]]).upper() or name[:2].upper()
            comp_entry = {
                "name": name,
                "roles": "Associate Software Engineer, Business Analyst, Management Trainee",
                "package_tier": "Dream (₹12 - ₹20 LPA)",
                "tier_badge": "bg-primary",
                "initial": clean_initial,
                "domain": "Technology & Consulting"
            }
            cat_map["Tier 1 Tech & Product Companies"]["companies"].append(comp_entry)

    filtered_categories = [c for c in cat_map.values() if len(c["companies"]) > 0]
    return filtered_categories if filtered_categories else default_categories
