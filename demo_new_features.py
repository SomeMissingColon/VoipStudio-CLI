#!/usr/bin/env python3
"""
Demo script showcasing all new features:
- Close-won/Close-lost status management
- Clients and Cemetery views
- Quick field editing with history tracking
- Contact lifecycle management
"""

import sys
import os
import json
from pathlib import Path

# Import the main VStudio CLI
from vstudio_cli import VStudioCLI, STATUS_CLOSE_WON, STATUS_CLOSE_LOST

def demo_new_features():
    """Demo all new CRM features."""
    
    # Override database config to use test database
    test_config = {
        "use_mongodb": True,
        "mongodb_uri": "mongodb://localhost:27017/",
        "database_name": "vstudio_crm_test",
        "csv_backup_enabled": True,
        "auto_migrate": False
    }
    
    # Write temporary config for test mode
    original_config_path = Path("database_config.json")
    backup_config_path = Path("database_config.json.backup")
    temp_config_path = Path("database_config.json")
    
    # Backup original config if it exists
    if original_config_path.exists():
        import shutil
        shutil.copy2(original_config_path, backup_config_path)
    
    # Write test config
    with open(temp_config_path, 'w') as f:
        json.dump(test_config, f, indent=2)
    
    print("🎯 NEW CRM FEATURES DEMO")
    print("=" * 60)
    print("Showcasing: Field Editing, Status Management, Clients & Cemetery")
    print("=" * 60)
    
    try:
        app = VStudioCLI(debug=False)
        app.testing_mode = True
        app._initialize_database()
        
        if app.db_manager:
            print("\n✅ Connected to MongoDB test database")
            
            # Setup demo data
            contacts = app.db_manager.get_contacts(limit=5)
            if len(contacts) >= 4:
                # Create a sales pipeline scenario
                lead = contacts[0]
                prospect = contacts[1]
                client = contacts[2]
                lost_deal = contacts[3]
                
                lead_id = lead.get('external_row_id')
                prospect_id = prospect.get('external_row_id')
                client_id = client.get('external_row_id')
                lost_id = lost_deal.get('external_row_id')
                
                print(f"\n🎬 DEMO SCENARIO: Sales Pipeline Management")
                print(f"=" * 50)
                
                # Set up different contact stages
                print(f"📋 Setting up demo contacts:")
                app.db_manager.update_contact(lead_id, {'status': 'new', 'notes': 'Fresh lead from website'})
                app.db_manager.update_contact(prospect_id, {'status': 'callback', 'notes': 'Interested prospect - follow up needed'})
                app.db_manager.update_contact(client_id, {'status': STATUS_CLOSE_WON, 'notes': 'Deal closed - new client!'})
                app.db_manager.update_contact(lost_id, {'status': STATUS_CLOSE_LOST, 'notes': 'Lost to competitor'})
                
                print(f"   🆕 Lead: {lead.get('name')} - New contact")
                print(f"   📞 Prospect: {prospect.get('name')} - Callback scheduled") 
                print(f"   🎉 Client: {client.get('name')} - CLOSE WON")
                print(f"   💀 Lost Deal: {lost_deal.get('name')} - CLOSE LOST")
                
                # Demonstrate view switching
                print(f"\n🔄 VIEW SWITCHING DEMONSTRATION")
                print(f"=" * 40)
                
                # Show clients view
                clients = app.db_manager.get_contacts_by_status(STATUS_CLOSE_WON)
                print(f"👥 CLIENTS VIEW (Press 'c' in app):")
                print(f"   Found {len(clients)} client(s)")
                for client_contact in clients:
                    print(f"   🎉 {client_contact.get('name')} - {client_contact.get('company', 'Unknown Company')}")
                
                # Show cemetery view  
                cemetery = app.db_manager.get_contacts_by_status(STATUS_CLOSE_LOST)
                print(f"\n💀 CEMETERY VIEW (Press 'z' in app):")
                print(f"   Found {len(cemetery)} lost deal(s)")
                for lost_contact in cemetery:
                    print(f"   ❌ {lost_contact.get('name')} - {lost_contact.get('company', 'Unknown Company')}")
                
                # Demonstrate edit history
                print(f"\n📝 EDIT HISTORY DEMONSTRATION")
                print(f"=" * 40)
                
                # Create some edit history for the demo
                app._save_edit_history(client_id, 'status', 'callback', STATUS_CLOSE_WON)
                app._save_edit_history(client_id, 'notes', 'Initial contact made', 'Deal closed - new client!')
                app._save_edit_history(lost_id, 'status', 'meeting_booked', STATUS_CLOSE_LOST)
                
                # Show history tracking
                if hasattr(app.db_manager, 'mongodb') and app.db_manager.mongodb:
                    collection = app.db_manager.mongodb.db['edit_history']
                    
                    print(f"📊 Recent edit history across all contacts:")
                    recent_edits = list(collection.find({}).sort('timestamp', -1).limit(5))
                    for edit in recent_edits:
                        timestamp = edit['timestamp'].strftime('%H:%M:%S')
                        contact_id = edit['contact_id']
                        field = edit['field']
                        old_val = edit['old_value'][:20] + "..." if len(str(edit['old_value'])) > 20 else edit['old_value']
                        new_val = edit['new_value'][:20] + "..." if len(str(edit['new_value'])) > 20 else edit['new_value']
                        print(f"   {timestamp}: {contact_id} - {field}: '{old_val}' → '{new_val}'")
                
                # Show quick editing workflow
                print(f"\n⚡ QUICK EDITING WORKFLOW")
                print(f"=" * 40)
                print(f"During normal contact workflow:")
                print(f"   1. Press 'e' to enter edit mode")
                print(f"   2. See numbered list of all editable fields:")
                print(f"      1. Name              7. City")
                print(f"      2. Company           8. Status")  
                print(f"      3. Phone Number      9. Notes")
                print(f"      4. Email            10. Callback Date")
                print(f"      5. Title            11. Meeting Date/Time")
                print(f"      6. Address")
                print(f"   3. Press number to edit that field")
                print(f"   4. Press 's' for quick status changes:")
                print(f"      - Options include Close Won & Close Lost")
                print(f"   5. Press 'h' to view/revert edit history")
                print(f"   6. Press 'b' to go back")
                
                # Show status management
                print(f"\n📊 STATUS MANAGEMENT")
                print(f"=" * 40)
                print(f"Available statuses with visual indicators:")
                print(f"   🆕 new           - Fresh leads")
                print(f"   📞 callback      - Follow-up needed")
                print(f"   📅 meeting_booked - Meeting scheduled")
                print(f"   ❌ no_answer     - Could not reach")
                print(f"   🎉 close_won     - CLIENT (moves to Clients view)")
                print(f"   💀 close_lost    - Lost deal (moves to Cemetery)")
                print(f"   🚫 do_not_call   - Do not contact")
                print(f"   📵 bad_number    - Invalid phone")
                
                # Show keyboard shortcuts
                print(f"\n⌨️  NEW KEYBOARD SHORTCUTS")
                print(f"=" * 40)
                print(f"   e  = Edit current contact fields")
                print(f"   c  = Switch to Clients view (close-won)")
                print(f"   z  = Switch to Cemetery view (close-lost)")
                print(f"   ")
                print(f"In Edit Mode:")
                print(f"   1-11 = Edit specific field")
                print(f"   s    = Quick status change")
                print(f"   h    = View edit history")
                print(f"   b    = Back to contact")
                print(f"   ")
                print(f"In History Mode:")
                print(f"   1-N  = Revert to old value")
                print(f"   b    = Back to edit mode")
                
                # Show contact lifecycle
                print(f"\n🔄 COMPLETE CONTACT LIFECYCLE")
                print(f"=" * 40)
                print(f"1. 🆕 NEW LEAD")
                print(f"   → Import/add contact → Status: 'new'")
                print(f"   → Press 'e' to add notes, update details")
                print(f"")
                print(f"2. 📞 FOLLOW UP")
                print(f"   → Call contact → Set status to 'callback'")
                print(f"   → Schedule follow-up → Add callback date")
                print(f"")
                print(f"3. 📅 MEETING")
                print(f"   → Good response → Set status to 'meeting_booked'")
                print(f"   → Add meeting date/time")
                print(f"")
                print(f"4. 🎯 DECISION POINT")
                print(f"   → Deal closes → Status: 'close_won' (→ CLIENTS)")
                print(f"   → Deal lost → Status: 'close_lost' (→ CEMETERY)")
                print(f"")
                print(f"5. 👥 CLIENT MANAGEMENT")
                print(f"   → Press 'c' to view all clients")
                print(f"   → Continue servicing existing clients")
                print(f"")
                print(f"6. 📊 ANALYSIS")
                print(f"   → Press 'z' to review lost deals")
                print(f"   → Learn from cemetery for improvement")
                
                print(f"\n🎉 DEMO COMPLETE!")
                print(f"=" * 40)
                print(f"✅ All new features are ready to use")
                print(f"✅ {len(clients)} client(s) in CLIENTS view")
                print(f"✅ {len(cemetery)} lost deal(s) in CEMETERY view")
                print(f"✅ Edit history tracking active")
                print(f"✅ Quick field editing enabled")
                print(f"✅ Status management with visual feedback")
                
                print(f"\n💡 TO START USING:")
                print(f"   Run: python3 vstudio_test.py")
                print(f"   Try the new 'e', 'c', 'z' keys!")
                
            else:
                print("❌ Not enough test contacts for full demo")
                
        else:
            print("❌ MongoDB connection failed")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Restore original config
        if backup_config_path.exists():
            backup_config_path.rename(original_config_path)
        elif temp_config_path.exists():
            temp_config_path.unlink()
        
        print(f"\n👋 Demo completed - ready for real use!")

if __name__ == "__main__":
    demo_new_features()