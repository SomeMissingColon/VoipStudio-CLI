#!/usr/bin/env python3
"""
MongoDB Database Explorer for VStudio CLI CRM
Interactive tool to explore collections and documents
"""

from pymongo import MongoClient
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.json import JSON
import sys

console = Console()

def format_value(value):
    """Format values for display."""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    elif hasattr(value, '__len__') and len(str(value)) > 50:
        return str(value)[:47] + "..."
    else:
        return str(value)

def show_collection_overview(db):
    """Show overview of all collections."""
    table = Table(title="📊 MongoDB Collections Overview")
    table.add_column("Collection", style="cyan", no_wrap=True)
    table.add_column("Documents", style="magenta")
    table.add_column("Description", style="green")
    
    descriptions = {
        "contacts": "Contact information and metadata",
        "interactions": "Calls, texts, notes history", 
        "tasks": "Callbacks, meetings, reminders",
        "outcomes": "Call results and categorization",
        "calendar_map": "Calendar integration tracking",
        "priority_rules": "Scoring rules configuration",
        "user_preferences": "User settings and preferences",
        "audit_log": "Change history and audit trail"
    }
    
    collections = db.list_collection_names()
    for collection_name in sorted(collections):
        count = db[collection_name].count_documents({})
        desc = descriptions.get(collection_name, "")
        table.add_row(collection_name, str(count), desc)
    
    console.print(table)

def explore_collection(db, collection_name):
    """Explore a specific collection."""
    collection = db[collection_name]
    count = collection.count_documents({})
    
    console.print(f"\n🔍 Exploring Collection: [bold cyan]{collection_name}[/bold cyan]")
    console.print(f"Total Documents: [bold magenta]{count}[/bold magenta]")
    
    if count == 0:
        console.print("[yellow]Collection is empty[/yellow]")
        return
    
    # Show sample documents
    limit = min(count, 5)
    console.print(f"\n📄 Showing first {limit} documents:")
    
    documents = list(collection.find().limit(limit))
    
    for i, doc in enumerate(documents, 1):
        # Create table for each document
        table = Table(title=f"Document {i}")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        
        for key, value in doc.items():
            # Convert ObjectId to string for display
            if hasattr(value, '__str__') and 'ObjectId' in str(type(value)):
                value = str(value)
            
            formatted_value = format_value(value)
            table.add_row(key, formatted_value)
        
        console.print(table)
    
    if count > limit:
        console.print(f"\n[dim]... and {count - limit} more documents[/dim]")

def show_document_details(db, collection_name, doc_id=None):
    """Show detailed view of a specific document."""
    collection = db[collection_name]
    
    if doc_id is None:
        # Show first document
        doc = collection.find_one()
    else:
        from bson import ObjectId
        try:
            doc = collection.find_one({"_id": ObjectId(doc_id)})
        except:
            console.print(f"[red]Invalid document ID: {doc_id}[/red]")
            return
    
    if not doc:
        console.print("[red]Document not found[/red]")
        return
    
    # Convert to JSON-serializable format
    def convert_doc(obj):
        if hasattr(obj, '__str__') and 'ObjectId' in str(type(obj)):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: convert_doc(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_doc(item) for item in obj]
        else:
            return obj
    
    converted_doc = convert_doc(doc)
    json_str = json.dumps(converted_doc, indent=2)
    
    console.print(f"\n📋 Document Details from [bold cyan]{collection_name}[/bold cyan]:")
    console.print(Panel(JSON(json_str), expand=False))

def query_collection(db, collection_name):
    """Allow user to query a collection."""
    console.print(f"\n🔍 Query Collection: [bold cyan]{collection_name}[/bold cyan]")
    console.print("Examples:")
    console.print("  {'status': 'callback'}")
    console.print("  {'name': {'$regex': 'john', '$options': 'i'}}")
    console.print("  {} (empty for all documents)")
    
    query_str = Prompt.ask("Enter query (JSON format)", default="{}")
    
    try:
        query = json.loads(query_str) if query_str.strip() else {}
        collection = db[collection_name]
        
        # Execute query
        cursor = collection.find(query).limit(10)
        results = list(cursor)
        
        console.print(f"\n📊 Found {len(results)} documents (showing max 10):")
        
        if results:
            for i, doc in enumerate(results, 1):
                table = Table(title=f"Result {i}")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="white")
                
                for key, value in doc.items():
                    if hasattr(value, '__str__') and 'ObjectId' in str(type(value)):
                        value = str(value)
                    
                    formatted_value = format_value(value)
                    table.add_row(key, formatted_value)
                
                console.print(table)
        else:
            console.print("[yellow]No documents match the query[/yellow]")
    
    except json.JSONDecodeError:
        console.print("[red]Invalid JSON query format[/red]")
    except Exception as e:
        console.print(f"[red]Query error: {e}[/red]")

def main():
    """Main interactive explorer."""
    console.print("[bold green]🗄️  MongoDB Database Explorer[/bold green]")
    console.print("VStudio CLI CRM Database Browser\n")
    
    # Connect to MongoDB
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client['vstudio_crm']
    except Exception as e:
        console.print(f"[red]❌ Failed to connect to MongoDB: {e}[/red]")
        console.print("Make sure MongoDB is running: python setup_mongodb.py --check-only")
        return
    
    console.print("[green]✅ Connected to MongoDB[/green]")
    
    while True:
        console.print("\n" + "="*50)
        console.print("[bold]Choose an option:[/bold]")
        console.print("1. Show collections overview")
        console.print("2. Explore specific collection")
        console.print("3. View document details")
        console.print("4. Query collection")
        console.print("5. Show indexes for collection")
        console.print("0. Exit")
        
        try:
            choice = IntPrompt.ask("Your choice", choices=['0', '1', '2', '3', '4', '5'])
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        
        if choice == 0:
            console.print("[green]Goodbye![/green]")
            break
        
        elif choice == 1:
            show_collection_overview(db)
        
        elif choice == 2:
            collections = db.list_collection_names()
            console.print("\nAvailable collections:")
            for i, coll in enumerate(collections, 1):
                console.print(f"  {i}. {coll}")
            
            coll_choice = IntPrompt.ask("Select collection", choices=[str(i) for i in range(1, len(collections) + 1)])
            collection_name = collections[coll_choice - 1]
            explore_collection(db, collection_name)
        
        elif choice == 3:
            collections = db.list_collection_names()
            console.print("\nAvailable collections:")
            for i, coll in enumerate(collections, 1):
                console.print(f"  {i}. {coll}")
            
            coll_choice = IntPrompt.ask("Select collection", choices=[str(i) for i in range(1, len(collections) + 1)])
            collection_name = collections[coll_choice - 1]
            
            doc_id = Prompt.ask("Document ID (press Enter for first document)", default="")
            show_document_details(db, collection_name, doc_id if doc_id else None)
        
        elif choice == 4:
            collections = db.list_collection_names()
            console.print("\nAvailable collections:")
            for i, coll in enumerate(collections, 1):
                console.print(f"  {i}. {coll}")
            
            coll_choice = IntPrompt.ask("Select collection", choices=[str(i) for i in range(1, len(collections) + 1)])
            collection_name = collections[coll_choice - 1]
            query_collection(db, collection_name)
        
        elif choice == 5:
            collections = db.list_collection_names()
            console.print("\nAvailable collections:")
            for i, coll in enumerate(collections, 1):
                console.print(f"  {i}. {coll}")
            
            coll_choice = IntPrompt.ask("Select collection", choices=[str(i) for i in range(1, len(collections) + 1)])
            collection_name = collections[coll_choice - 1]
            
            collection = db[collection_name]
            indexes = list(collection.list_indexes())
            
            console.print(f"\n🔍 Indexes for [bold cyan]{collection_name}[/bold cyan]:")
            table = Table()
            table.add_column("Index Name", style="cyan")
            table.add_column("Keys", style="yellow")
            table.add_column("Options", style="green")
            
            for idx in indexes:
                name = idx.get('name', 'N/A')
                keys = str(idx.get('key', {}))
                options = {k: v for k, v in idx.items() if k not in ['name', 'key', 'v']}
                table.add_row(name, keys, str(options) if options else "None")
            
            console.print(table)
    
    client.close()

if __name__ == "__main__":
    main()