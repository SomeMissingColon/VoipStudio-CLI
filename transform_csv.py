#!/usr/bin/env python3
"""
Transform recent_companies_enhanced.csv to match VStudio CLI requirements
"""

import csv
import hashlib
from pathlib import Path

def transform_csv(input_file, output_file):
    """Transform the CSV to match vstudio CLI requirements."""
    
    # Required fields for vstudio CLI
    vstudio_headers = [
        'external_row_id', 'phone_number', 'name', 'email', 'company', 
        'title', 'city', 'address', 'source', 'status', 'notes', 'last_call_at',
        'callback_on', 'meeting_at', 'gcal_callback_event_id', 
        'gcal_meeting_event_id', 'last_sms_at', 'sms_history'
    ]
    
    transformed_records = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            # Generate external_row_id
            content_hash = hashlib.md5(f"{row.get('NEQ', '')}{row.get('company_name', '')}{row.get('phone_number', '')}".encode()).hexdigest()[:8]
            external_row_id = f"companies_{i}_{content_hash}"
            
            # Clean phone number (remove any non-digits except +)
            phone_number = row.get('phone_number_cleaned', row.get('phone_number', '')).strip()
            if phone_number and not phone_number.startswith('+'):
                # Add Canadian country code if it's a 10-digit number
                if len(phone_number) == 10:
                    phone_number = f"+1{phone_number}"
            
            # Map fields
            transformed_record = {
                'external_row_id': external_row_id,
                'phone_number': phone_number,
                'name': row.get('company_name', '').strip(),  # Use company name as contact name
                'email': row.get('email', '').strip(),
                'company': row.get('company_name', '').strip(),  # Company name
                'title': row.get('desc_act_econ_assuj', '').strip(),  # Business activity as title
                'city': row.get('municipality', '').strip(),
                'address': row.get('physical_address', '').strip(),  # Physical address
                'source': 'license_data',  # Source identifier
                'status': 'new',  # Default status
                'notes': f"NEQ: {row.get('NEQ', '')}; License: {row.get('license_number', '')}; Status: {row.get('license_status', '')}; Inception: {row.get('inception_date', '')}",
                'last_call_at': '',
                'callback_on': '',
                'meeting_at': '',
                'gcal_callback_event_id': '',
                'gcal_meeting_event_id': '',
                'last_sms_at': '',
                'sms_history': ''
            }
            
            # Only include records with valid phone numbers
            if transformed_record['phone_number'] and len(transformed_record['phone_number'].replace('+', '').replace(' ', '').replace('-', '')) >= 10:
                transformed_records.append(transformed_record)
            else:
                print(f"Skipping record {i+1}: Invalid phone number '{transformed_record['phone_number']}'")
    
    # Write transformed data
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=vstudio_headers)
        writer.writeheader()
        writer.writerows(transformed_records)
    
    print(f"Transformed {len(transformed_records)} records from {input_file} to {output_file}")
    return len(transformed_records)

if __name__ == "__main__":
    input_file = "recent_companies_enhanced.csv"
    output_file = "recent_companies_vstudio.csv"
    
    if not Path(input_file).exists():
        print(f"Input file {input_file} not found")
        exit(1)
    
    count = transform_csv(input_file, output_file)
    print(f"Successfully transformed {count} records")