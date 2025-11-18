# jfrog_api_tool/main.py

import sys
import os
import json
import importlib.resources
import questionary
from rich.console import Console
from rich.panel import Panel
from typing import Dict, Any

# Import the new config file
from jfrog_api_tool import config 

# Import utilities
from jfrog_api_tool.utils import auth, api_runner

# Import all our wizards
from jfrog_api_tool.wizards.policy_wizards import run_create_policy_wizard
from jfrog_api_tool.wizards.reindex_wizard import run_force_reindex_wizard
from jfrog_api_tool.wizards.gc_wizards import run_force_gc_start_wizard, run_set_gc_config_wizard
from jfrog_api_tool.wizards.config_wizards import run_configure_workers_wizard
from jfrog_api_tool.wizards.export_wizard import run_export_component_wizard

# Initialize Rich console
console = Console()


# --- Help Function ---
def _print_help():
    """Prints the help message."""
    console = Console()
    console.print(Panel.fit("[bold magenta]JFrog Support API CLI Tool[/bold magenta] (jfat)"))
    console.print("\n[bold]Usage:[/bold]")
    console.print("  jfat               - Runs the tool interactively.")
    console.print("  jfat --debug       - Runs the tool in debug mode (prints verbose logs).")
    console.print("  jfat --help        - Shows this help message.")
    
    console.print("\n[bold]Environment Variable:[/bold]")
    console.print("  JFAT_DEBUG=true    - Same as --debug (e.g., `JFAT_DEBUG=true jfat`)")

# --- Flag Handling ---
if "--help" in sys.argv:
    _print_help()
    sys.exit(0)

if "--debug" in sys.argv or os.environ.get("JFAT_DEBUG") == "true":
    config.IS_DEBUG = True
    print("!!! DEBUG MODE ENABLED !!!")


def load_api_config() -> dict:
    """
    Loads the API configuration file from within the package.
    """
    try:
        # Reads 'apis.json' from the 'jfrog_api_tool' package
        file_content = importlib.resources.read_text('jfrog_api_tool', 'apis.json')
        return json.loads(file_content)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] Failed to load internal 'apis.json' config.")
        console.print(f"[italic]{e}[/italic]")
        sys.exit(1)

# --- Main Parameter Gathering Function (The "Router") ---
def get_user_params(api_config: dict) -> dict:
    """
    Prompts the user for required path, query, and body parameters.
    """
    params = {}
    
    path_params = api_config.get("path_params", [])
    if path_params:
        console.print("\n[bold]Please provide URL path parameters:[/bold]")
        for param in path_params:
            val = questionary.text(f"Enter value for '{param}':").ask()
            if val is None: return None
            params[param] = val

    query_params = api_config.get("query_params", [])
    if query_params:
        console.print("[bold]Please provide query parameters (optional):[/bold]")
        for param in query_params:
            val = questionary.text(f"Enter value for '{param}' (press Enter to skip):").ask()
            if val is None: return None
            if val:
                params[param] = val

    body_input_mode = api_config.get("body_input_mode")
    wizard_name = api_config.get("wizard_name")

    if body_input_mode == "wizard":
        wizard_params = None
        
        # Route to the correct wizard based on its name
        if wizard_name == "force_reindex":
            wizard_params = run_force_reindex_wizard()
        elif wizard_name == "create_policy_v2":
            wizard_params = run_create_policy_wizard()
        elif wizard_name == "configure_workers_count":
            wizard_params = run_configure_workers_wizard()
        elif wizard_name == "export_component_details":
            wizard_params = run_export_component_wizard()
        elif wizard_name == "set_gc_config":
            wizard_params = run_set_gc_config_wizard()    
        elif wizard_name == "force_gc_start":
            wizard_params = run_force_gc_start_wizard()
        else:
            console.print(f"[red]Error: Unknown wizard_name '{wizard_name}'[/red]")
            return None

        if wizard_params is None: return None
        params.update(wizard_params)

    elif body_input_mode == "file":
        console.print("\n[bold]This API requires a JSON body from a file.[/bold]")
        file_path = questionary.path("Enter path to JSON body file:").ask()
        if file_path is None: return None
        try:
            with open(file_path, 'r') as f:
                params["__json_body_from_file__"] = json.load(f)
        except Exception as e:
            console.print(f"[bold red]Error reading file {file_path}: {e}[/bold red]")
            return None
            
    else:
        # Simple key-value "Type 1" APIs
        body_params = api_config.get("body_params", [])
        if body_params:
            console.print("\n[bold]Please provide request body parameters:[/bold]")
            for param in body_params:
                val = questionary.text(f"Enter value for '{param}':").ask()
                if val is None: return None
                params[param] = val
            
    return params

# --- Main Function ---
def main():
    """
    Main execution flow.
    """
    console.print(Panel.fit("[bold magenta]JFrog Support API CLI Tool[/bold magenta]"))
    
    credentials = auth.get_credentials()
    if credentials is None:
        console.print("[yellow]Exiting tool.[/yellow]")
        sys.exit(0)
    
    api_config_data = load_api_config()
    
    try:
        while True:
            # --- System Selection ---
            selected_system = questionary.select(
                "Select system:",
                choices=list(api_config_data.keys()) + [questionary.Separator(), "Exit"]
            ).ask()
            if selected_system is None or selected_system == "Exit": break

            system_apis = api_config_data[selected_system]
            
            # --- API / Category Selection ---
            selected_key = questionary.select(
                f"Select API or Category from {selected_system}:",
                choices=list(system_apis.keys()) + [questionary.Separator(), "Back"]
            ).ask()
            
            if selected_key is None or selected_key == "Back":
                continue # Go back to system selection
                
            selected_config = system_apis[selected_key]
            
            # --- NEW: Sub-menu logic ---
            # Check if the selected item is a sub-category (doesn't have "method")
            if "method" not in selected_config:
                sub_menu = selected_config
                console.print(f"[bold]Selected category: {selected_key}[/bold]")
                
                selected_api_name = questionary.select(
                    f"Select API from {selected_key}:",
                    choices=list(sub_menu.keys()) + [questionary.Separator(), "Back"]
                ).ask()
                
                if selected_api_name is None or selected_api_name == "Back":
                    continue # Go back to system selection
                
                selected_config = sub_menu[selected_api_name]
            # --- End of sub-menu logic ---

            # At this point, selected_config is a final API endpoint
            user_params = get_user_params(selected_config)
            if user_params is None:
                continue # User cancelled parameter input, go back to system menu

            api_runner.execute_api_call(
                auth_details=credentials,
                api_config=selected_config,
                params=user_params
            )
            
            console.print("\n" + "="*50 + "\n")
            run_another = questionary.confirm("Do you want to run another API call?").ask()
            if not run_another:
                break # Exit the main while loop

    except KeyboardInterrupt:
        pass

    console.print("\n[bold cyan]Goodbye![/bold cyan]")

if __name__ == "__main__":
    main()