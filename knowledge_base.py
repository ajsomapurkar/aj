# knowledge_base.py
COLLEGE_DATA = {
    "college_info": {
        "name": "Bharatesh Education Trust's Global Business School",
        "vtu_affiliated": True,
        "vtu_code": "BN005",
        "address": "Navnath Nagar, Airport Road, Belagavi, Karnataka 591156",
        "phone": "+91-831-2435171",
        "email": "info@bharatesh.edu.in",
        "website": "https://bharateshcollege.edu.in"
    },
    "admissions": {
        "undergraduate": {
            "courses": ["B.E.", "BBA", "BCA"],
            "eligibility": "PUC/12th with minimum 45% marks",
            "documents": ["SSLC Marks Card", "PUC/12th Marks Card", "Transfer Certificate",
                          "Migration Certificate", "Caste Certificate (if applicable)", "Aadhar Copy"],
            "process": "1. Fill application form 2. Submit documents 3. Pay fees 4. Get admission letter",
            "fees": {
                "btech": "₹85,000 per year (approx)",
                "bba": "₹45,000 per year (approx)",
                "bca": "₹40,000 per year (approx)"
            }
        }
    },
    "examinations": {
        "vtu_schedule": {
            "odd_sem": "November to January",
            "even_sem": "April to June"
        },
        "internal_assessment": {
            "tests": "3 tests per semester",
            "attendance": "Minimum 75% required for exam eligibility"
        },
        "results": {
            "check": "https://results.vtu.ac.in",
            "revaluation": "Within 15 days of result declaration"
        }
    },
    "departments": {
        "cse": {"hod": "Dr. XYZ", "contact": "cse@bharatesh.edu.in"},
        "ece": {"hod": "Dr. ABC", "contact": "ece@bharatesh.edu.in"},
        "mechanical": {"hod": "Dr. PQR", "contact": "mech@bharatesh.edu.in"},
        "civil": {"hod": "Dr. LMN", "contact": "civil@bharatesh.edu.in"},
        "mba": {"hod": "Dr. DEF", "contact": "mba@bharatesh.edu.in"}
    },
    "facilities": {
        "library": {"timing": "8:30 AM to 6:00 PM", "books": "25000+"},
        "hostel": {"available": True, "contact": "hostel@bharatesh.edu.in"},
        "transport": {"available": True, "routes": "All major areas of Belagavi"}
    },
    "important_dates": {
        "academic_year": "June to May",
        "semester_start": {"odd": "August", "even": "January"},
        "holidays": "As per VTU calendar"
    }
}
