# jfrog_api_tool/wizards/watch_wizard.py

import questionary
from rich.console import Console
from typing import Dict, Any
from datetime import datetime, timedelta

console = Console()

def run_apply_watch_history_wizard() -> Dict[str, Any]:
    """
    Wizard to apply a Watch on existing content (History Scan).
    Allows quick selection of date ranges.
    """
    console.print("\n[bold]Starting 'Apply Watch on Existing Content' wizard...[/bold]")
    console.print("[dim]This will trigger a historical scan for the selected watches.[/dim]\n")
    
    # 1. Watch Names
    watches_str = questionary.text("Enter Watch Names (comma separated):").ask()
    if not watches_str: return None
    
    # Clean up the list
    watch_list = [w.strip() for w in watches_str.split(',') if w.strip()]

    # 2. Date Range Selection
    date_choice = questionary.select(
        "Select Scan Range:",
        choices=[
            "Last 7 Days",
            "Last 30 Days",
            "Last 90 Days",
            "Everything (Since 2010)",
            "Custom Range (Manual Input)"
        ]
    ).ask()

    if not date_choice: return None

    # Calculate Dates
    now = datetime.utcnow()
    # Xray format: YYYY-MM-DDTHH:MM:SSZ
    api_fmt = "%Y-%m-%dT%H:%M:%SZ"
    
    end_date_str = now.strftime(api_fmt)
    start_date_str = ""

    if date_choice == "Last 7 Days":
        start_date_str = (now - timedelta(days=7)).strftime(api_fmt)
    
    elif date_choice == "Last 30 Days":
        start_date_str = (now - timedelta(days=30)).strftime(api_fmt)
    
    elif date_choice == "Last 90 Days":
        start_date_str = (now - timedelta(days=90)).strftime(api_fmt)
    
    elif date_choice == "Everything (Since 2010)":
        start_date_str = "2010-01-01T00:00:00Z"
    
    elif date_choice == "Custom Range (Manual Input)":
        console.print("[italic]Format: YYYY-MM-DDTHH:MM:SSZ (e.g. 2023-01-01T00:00:00Z)[/italic]")
        start_date_str = questionary.text("Start Date:", default="2023-01-01T00:00:00Z").ask()
        if not start_date_str: return None
        
        end_date_str = questionary.text("End Date:", default=end_date_str).ask()
        if not end_date_str: return None

    # 3. Construct Body
    json_body = {
        "watch_names": watch_list,
        "date_range": {
            "start_date": start_date_str,
            "end_date": end_date_str
        }
    }
    
    # Debug print to show user what dates are being sent
    console.print(f"\n[dim]Selected Range: {start_date_str} -> {end_date_str}[/dim]")

    return {"__json_body_from_file__": json_body}