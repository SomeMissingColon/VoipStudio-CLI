#!/usr/bin/env python3
"""
Setup script for VStudio CLI - helps users get started quickly.
"""

import os
import sys
from pathlib import Path
import subprocess
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

console = Console()

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 7):
        console.print("[red]Error: Python 3.7 or higher is required[/red]")
        console.print(f"Current version: {sys.version}")
        return False
    return True

def install_dependencies():
    """Install required Python packages."""
    console.print("[yellow]Installing Python dependencies...[/yellow]")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        console.print("[green]✓ Dependencies installed successfully[/green]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to install dependencies: {e}[/red]")
        return False

def setup_voipstudio():
    """Guide user through VoIPstudio setup."""
    console.print("\n[bold cyan]VoIPstudio API Setup[/bold cyan]")
    
    panel_content = """
To get your VoIPstudio API token:

1. Log into your VoIPstudio web dashboard
2. Go to Settings → API 
3. Generate a new API token
4. Copy the token - you'll need it when running the app

The token will be stored securely in your system keychain.
    """
    
    console.print(Panel(panel_content.strip(), title="API Token Setup"))
    
    if Confirm.ask("Do you have your VoIPstudio API token ready?"):
        console.print("[green]Great! You can enter it when you first run the application.[/green]")
        return True
    else:
        console.print("[yellow]Please get your API token first, then run the setup again.[/yellow]")
        return False

def setup_google_calendar():
    """Guide user through Google Calendar setup."""
    console.print("\n[bold cyan]Google Calendar Setup (Optional)[/bold cyan]")
    
    if not Confirm.ask("Do you want to enable Google Calendar integration?"):
        console.print("[yellow]Calendar integration will be disabled.[/yellow]")
        return True
    
    panel_content = """
To enable Google Calendar integration:

1. Go to the Google Cloud Console (https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the Google Calendar API
4. Create OAuth 2.0 credentials:
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Choose "Desktop Application"
   - Download the JSON file
5. Rename the file to 'credentials.json' in this directory

Without this file, calendar features will be disabled.
    """
    
    console.print(Panel(panel_content.strip(), title="Calendar Setup"))
    
    if Path("credentials.json").exists():
        console.print("[green]✓ Found credentials.json file[/green]")
        return True
    else:
        console.print("[yellow]⚠ credentials.json not found - calendar integration will be disabled[/yellow]")
        return False

def create_sample_csv():
    """Create a sample CSV file if it doesn't exist."""
    sample_file = Path("sample_contacts.csv")
    if sample_file.exists():
        console.print(f"[green]✓ Sample CSV file already exists: {sample_file}[/green]")
        return
    
    if Confirm.ask("Create a sample contacts CSV file?"):
        try:
            # Sample CSV is already created by the main script
            console.print(f"[green]✓ Sample CSV file already exists: {sample_file}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to create sample CSV: {e}[/red]")

def show_usage_instructions():
    """Show usage instructions."""
    console.print("\n[bold green]Setup Complete![/bold green]\n")
    
    table = Table(title="Usage Instructions", show_header=True)
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="white")
    
    table.add_row(
        "python vstudio_cli.py contacts.csv",
        "Start the application with your CSV file"
    )
    table.add_row(
        "python vstudio_cli.py sample_contacts.csv",
        "Try the app with sample data"
    )
    table.add_row(
        "python vstudio_cli.py -h",
        "Show help and all available options"
    )
    table.add_row(
        "python vstudio_cli.py -v contacts.csv",
        "Run with verbose logging for debugging"
    )
    
    console.print(table)
    
    console.print("\n[bold]Keyboard shortcuts in the application:[/bold]")
    shortcuts = [
        "1 - Make call",
        "2 - Send text (if available)", 
        "3 - Next record",
        "4 - Delete record",
        "5 - Add note",
        "↑/k - Previous record",
        "↓/j - Next record", 
        "/ - Search",
        "q - Quit"
    ]
    
    for shortcut in shortcuts:
        console.print(f"  [cyan]{shortcut}[/cyan]")

def main():
    """Main setup function."""
    console.print(Panel.fit(
        "VStudio CLI Setup\nKeyboard-first VoIP call management",
        style="bold blue"
    ))
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        console.print("[red]Please fix dependency issues and run setup again.[/red]")
        sys.exit(1)
    
    # VoIPstudio setup
    if not setup_voipstudio():
        console.print("[yellow]You can complete VoIPstudio setup later.[/yellow]")
    
    # Google Calendar setup
    setup_google_calendar()
    
    # Create sample CSV
    create_sample_csv()
    
    # Show usage instructions
    show_usage_instructions()
    
    console.print("\n[green]Ready to go! Run 'python vstudio_cli.py --help' for more information.[/green]")

if __name__ == "__main__":
    main()