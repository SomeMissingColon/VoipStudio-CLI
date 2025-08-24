#!/usr/bin/env python3
"""
Create enriched test data for developing past-due and scheduled calls features.
Generates realistic contacts with various callback/meeting scenarios.
"""

import csv
import random
from datetime import datetime, timedelta
from typing import List, Dict
import hashlib

# Sample data pools for realistic test data
COMPANY_NAMES = [
    "TechStart Solutions", "Digital Marketing Pro", "BuildRight Construction", 
    "Green Energy Solutions", "MetroFlow Logistics", "Precision Manufacturing",
    "CloudSync Technologies", "UrbanSpace Architecture", "NextGen Software",
    "BluePrint Engineering", "DataDriven Analytics", "SmartHome Systems",
    "EcoFriendly Products", "RapidGrow Marketing", "SecureNet Cybersecurity",
    "InnovateLab Research", "FreshStart Consulting", "PowerGrid Solutions",
    "MobileFirst Development", "SkyHigh Aviation", "ClearView Optics",
    "FastTrack Delivery", "PureTech Water", "BrightFuture Solar",
    "ConnectPlus Communications", "FlexiWork Staffing", "QualityFirst Testing"
]

FIRST_NAMES = [
    "Sarah", "Michael", "Jennifer", "David", "Lisa", "Robert", "Emily", "James",
    "Maria", "John", "Ashley", "Christopher", "Jessica", "Daniel", "Amanda",
    "Matthew", "Stephanie", "Anthony", "Nicole", "Mark", "Elizabeth", "Paul",
    "Rachel", "Steven", "Laura", "Andrew", "Michelle", "Joshua", "Kimberly", "Brian"
]

LAST_NAMES = [
    "Johnson", "Smith", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
]

JOB_TITLES = [
    "CEO", "CTO", "VP of Sales", "Marketing Director", "Operations Manager",
    "Project Manager", "Senior Developer", "Business Analyst", "Sales Manager",
    "Account Executive", "Product Manager", "HR Director", "Finance Manager",
    "Engineering Lead", "Quality Assurance Manager", "Customer Success Manager",
    "Regional Sales Director", "IT Manager", "Procurement Manager", "Brand Manager"
]

CANADIAN_CITIES = [
    "Toronto", "Montreal", "Vancouver", "Calgary", "Edmonton", "Ottawa", "Winnipeg",
    "Quebec City", "Hamilton", "Kitchener", "London", "Victoria", "Halifax",
    "Oshawa", "Windsor", "Saskatoon", "Regina", "Sherbrooke", "St. John's",
    "Kelowna", "Abbotsford", "Greater Sudbury", "Kingston", "Saguenay", "Trois-Rivières"
]

CANADIAN_ADDRESSES = [
    "{} Main Street", "{} King Street", "{} Queen Street", "{} University Avenue",
    "{} Bay Street", "{} Yonge Street", "{} Richmond Street", "{} Adelaide Street",
    "{} Bloor Street", "{} Dundas Street", "{} College Street", "{} Spadina Avenue",
    "{} St. Clair Avenue", "{} Eglinton Avenue", "{} Lawrence Avenue", "{} Sheppard Avenue"
]

# Area codes for different Canadian provinces
AREA_CODES = ["416", "647", "437", "905", "289", "365", "514", "438", "450", "579", "604", "778", "236", "403", "587", "825"]

BUSINESS_ACTIVITIES = [
    "Software Development", "Digital Marketing", "Construction Services", "Consulting Services",
    "Manufacturing", "E-commerce", "Real Estate", "Financial Services", "Healthcare Technology",
    "Educational Services", "Logistics and Transportation", "Renewable Energy", "Food Services",
    "Retail Sales", "Professional Services", "Engineering Services", "Design Services"
]

def generate_phone_number() -> str:
    """Generate a realistic Canadian phone number."""
    area_code = random.choice(AREA_CODES)
    exchange = random.randint(200, 999)
    number = random.randint(1000, 9999)
    return f"+1{area_code}{exchange:03d}{number:04d}"

def generate_email(first_name: str, last_name: str, company: str) -> str:
    """Generate a realistic email address."""
    patterns = [
        f"{first_name.lower()}.{last_name.lower()}@{company.lower().replace(' ', '').replace('&', 'and')}.com",
        f"{first_name.lower()}{last_name.lower()[0]}@{company.lower().replace(' ', '').replace('&', 'and')}.ca",
        f"{first_name.lower()[0]}{last_name.lower()}@{company.lower().replace(' ', '')}.org",
        f"{first_name.lower()}@{company.lower().replace(' ', '').replace('&', 'and')}.net"
    ]
    return random.choice(patterns)

def generate_address(city: str) -> str:
    """Generate a realistic Canadian address."""
    street_number = random.randint(100, 9999)
    street_template = random.choice(CANADIAN_ADDRESSES)
    postal_codes = {
        "Toronto": ["M5V", "M4W", "M6K", "M5T", "M4S"],
        "Montreal": ["H3A", "H2Y", "H4B", "H3G", "H2W"],
        "Vancouver": ["V6B", "V5K", "V6E", "V7Y", "V5T"],
        "Calgary": ["T2P", "T3A", "T2X", "T3K", "T2E"]
    }
    
    street_name = street_template.format(street_number)
    default_postal = "K1A 0A6"  # Default Canadian postal code
    postal_base = postal_codes.get(city, [default_postal[:3]])[0]
    postal_code = f"{postal_base} {random.randint(1, 9)}{chr(random.randint(65, 90))}{random.randint(1, 9)}"
    
    return f"{street_name}, {city} (Ontario), {postal_code}"

def create_test_contacts(num_contacts: int = 50) -> List[Dict]:
    """Create enriched test contacts with various scheduling scenarios."""
    contacts = []
    today = datetime.now().date()
    
    for i in range(num_contacts):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        company = random.choice(COMPANY_NAMES)
        city = random.choice(CANADIAN_CITIES)
        
        # Generate external_row_id
        content_hash = hashlib.md5(f"test_{i}_{company}_{first_name}_{last_name}".encode()).hexdigest()[:8]
        external_row_id = f"test_{i}_{content_hash}"
        
        # Base contact data
        contact = {
            'external_row_id': external_row_id,
            'phone_number': generate_phone_number(),
            'name': f"{first_name} {last_name}",
            'email': generate_email(first_name, last_name, company),
            'company': company,
            'title': random.choice(JOB_TITLES),
            'address': generate_address(city),
            'city': city,
            'source': 'test_data',
            'notes': '',
            'last_call_at': '',
            'callback_on': '',
            'meeting_at': '',
            'gcal_callback_event_id': '',
            'gcal_meeting_event_id': '',
            'last_sms_at': '',
            'sms_history': ''
        }
        
        # Create different scheduling scenarios
        scenario = random.randint(1, 10)
        
        if scenario <= 2:  # 20% - Past due callbacks (1-7 days ago)
            days_ago = random.randint(1, 7)
            past_date = today - timedelta(days=days_ago)
            contact['status'] = 'callback'
            contact['callback_on'] = past_date.isoformat()
            contact['notes'] = f"[{(today - timedelta(days=days_ago+1)).strftime('%Y-%m-%d %H:%M')}] Scheduled callback - follow up on proposal"
            
        elif scenario <= 4:  # 20% - Today's callbacks (various times)
            callback_hour = random.choice([9, 10, 11, 14, 15, 16, 17])
            callback_time = datetime.combine(today, datetime.min.time().replace(hour=callback_hour, minute=random.randint(0, 59)))
            contact['status'] = 'callback'
            contact['callback_on'] = callback_time.date().isoformat()
            contact['notes'] = f"[{(today - timedelta(days=1)).strftime('%Y-%m-%d %H:%M')}] Call back requested - interested in services"
            
        elif scenario == 5:  # 10% - Past due meetings (1-3 days ago)
            days_ago = random.randint(1, 3)
            past_datetime = datetime.combine(today - timedelta(days=days_ago), 
                                           datetime.min.time().replace(hour=random.choice([9, 10, 11, 14, 15]), minute=0))
            contact['status'] = 'meeting_booked'
            contact['meeting_at'] = past_datetime.isoformat()
            contact['notes'] = f"[{(today - timedelta(days=days_ago+1)).strftime('%Y-%m-%d %H:%M')}] Meeting scheduled - product demo"
            
        elif scenario <= 7:  # 20% - Today's meetings (various times)
            meeting_hour = random.choice([9, 10, 11, 13, 14, 15, 16])
            meeting_time = datetime.combine(today, datetime.min.time().replace(hour=meeting_hour, minute=random.choice([0, 30])))
            contact['status'] = 'meeting_booked'
            contact['meeting_at'] = meeting_time.isoformat()
            contact['notes'] = f"[{(today - timedelta(days=1)).strftime('%Y-%m-%d %H:%M')}] Meeting confirmed - discuss contract terms"
            
        elif scenario == 8:  # 10% - No answer (recent attempts)
            days_ago = random.randint(0, 3)
            call_date = today - timedelta(days=days_ago)
            contact['status'] = 'no_answer'
            contact['last_call_at'] = datetime.combine(call_date, 
                                                     datetime.min.time().replace(hour=random.randint(9, 17), minute=random.randint(0, 59))).isoformat()
            contact['notes'] = f"[{call_date.strftime('%Y-%m-%d %H:%M')}] No answer - left voicemail"
            
        else:  # 20% - New contacts (never called)
            contact['status'] = 'new'
            contact['notes'] = f"Lead source: {random.choice(['Website', 'Referral', 'Trade Show', 'Cold Outreach', 'LinkedIn'])}"
        
        contacts.append(contact)
    
    return contacts

def create_test_database():
    """Create test CSV and import to separate test database."""
    print("🎯 Creating enriched test data for past-due and scheduled calls...")
    
    # Generate test contacts
    contacts = create_test_contacts(50)
    
    # Write to CSV
    test_csv_path = "test_enriched_data.csv"
    headers = [
        'external_row_id', 'phone_number', 'name', 'email', 'company', 
        'title', 'city', 'address', 'source', 'status', 'notes', 'last_call_at',
        'callback_on', 'meeting_at', 'gcal_callback_event_id', 
        'gcal_meeting_event_id', 'last_sms_at', 'sms_history'
    ]
    
    with open(test_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(contacts)
    
    print(f"✅ Created {test_csv_path} with {len(contacts)} test contacts")
    
    # Analyze the test data
    today = datetime.now().date()
    stats = {
        'past_due_callbacks': 0,
        'today_callbacks': 0,
        'past_due_meetings': 0,
        'today_meetings': 0,
        'no_answer': 0,
        'new': 0
    }
    
    for contact in contacts:
        status = contact.get('status', '')
        
        if status == 'callback' and contact.get('callback_on'):
            callback_date = datetime.fromisoformat(contact['callback_on']).date()
            if callback_date < today:
                stats['past_due_callbacks'] += 1
            elif callback_date == today:
                stats['today_callbacks'] += 1
                
        elif status == 'meeting_booked' and contact.get('meeting_at'):
            meeting_date = datetime.fromisoformat(contact['meeting_at']).date()
            if meeting_date < today:
                stats['past_due_meetings'] += 1
            elif meeting_date == today:
                stats['today_meetings'] += 1
                
        elif status == 'no_answer':
            stats['no_answer'] += 1
        elif status == 'new':
            stats['new'] += 1
    
    print(f"\n📊 Test Data Distribution:")
    print(f"   📅 Today's callbacks: {stats['today_callbacks']}")
    print(f"   📅 Today's meetings: {stats['today_meetings']}")
    print(f"   ⏰ Past-due callbacks: {stats['past_due_callbacks']}")
    print(f"   ⏰ Past-due meetings: {stats['past_due_meetings']}")
    print(f"   📞 No answer (recent): {stats['no_answer']}")
    print(f"   🆕 New contacts: {stats['new']}")
    
    print(f"\n🎯 Perfect for testing:")
    print(f"   • Past-due feature ({stats['past_due_callbacks'] + stats['past_due_meetings']} overdue items)")
    print(f"   • Today's schedule feature ({stats['today_callbacks'] + stats['today_meetings']} today items)")
    print(f"   • Priority sorting and filtering")
    
    return test_csv_path, contacts

if __name__ == "__main__":
    create_test_database()