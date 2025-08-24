#!/usr/bin/env python3
"""Quick database statistics viewer"""

from pymongo import MongoClient

def main():
    print('🚀 Quick Database Stats:')
    print('=' * 30)

    client = MongoClient('mongodb://localhost:27017/')
    db = client['vstudio_crm']

    # Show priority rules
    print('⚙️  PRIORITY RULES:')
    rules = list(db.priority_rules.find())
    for rule in rules:
        print(f'  • {rule["name"]}: weight={rule["weight"]}, enabled={rule["enabled"]}')

    print(f'\n📊 DATABASE SUMMARY:')
    total_docs = sum(db[coll].count_documents({}) for coll in db.list_collection_names())
    print(f'  • Total documents across all collections: {total_docs}')

    # Count queries
    active_contacts = db.contacts.count_documents({'status': {'$ne': 'archived'}})
    pending_tasks = db.tasks.count_documents({'state': 'pending'})
    interactions = db.interactions.count_documents({})

    print(f'  • Active contacts: {active_contacts}')
    print(f'  • Pending tasks: {pending_tasks}')
    print(f'  • Total interactions: {interactions}')

    client.close()

if __name__ == "__main__":
    main()