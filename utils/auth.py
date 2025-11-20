# jfrog_api_tool/utils/auth.py

import questionary
import configparser
import sys
from pathlib import Path
from rich.console import Console

console = Console()

# --- הגדרות ---
CONFIG_DIR = Path.home() / ".config" / "jfrog-api-tool"
CONFIG_FILE = CONFIG_DIR / "config.ini"

# --- הדפסת דיבאג ראשונית ---
print(f"DEBUG: Script started.")
print(f"DEBUG: Config Directory path set to: {CONFIG_DIR}")
print(f"DEBUG: Config File path set to: {CONFIG_FILE}")

def _init_config():
    """
    Ensures the config directory and file exist.
    """
    print("DEBUG: --- Entering _init_config() ---")
    try:
        print(f"DEBUG: Checking/Creating directory: {CONFIG_DIR}")
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        print("DEBUG: Directory check/creation successful.")
        
        print(f"DEBUG: Checking if file exists: {CONFIG_FILE}")
        if not CONFIG_FILE.is_file():
            print("DEBUG: File does not exist. Attempting to create (touch) it...")
            CONFIG_FILE.touch()
            print("DEBUG: File created.")
        else:
            print("DEBUG: File already exists.")
            
    except Exception as e:
        print(f"DEBUG: !!! CRITICAL ERROR in _init_config !!!")
        print(f"DEBUG: Error details: {e}")
        console.print(f"[bold red]Error:[/bold red] Could not create config directory or file.")
        console.print(f"[italic]{e}[/italic]")
        sys.exit(1)
    print("DEBUG: --- Exiting _init_config() ---")


def _load_contexts() -> configparser.ConfigParser:
    """
    Loads all saved contexts from the config.ini file.
    """
    print("DEBUG: --- Entering _load_contexts() ---")
    _init_config()  # This will run the init function and its debug prints
    
    parser = configparser.ConfigParser()
    try:
        print(f"DEBUG: Reading config file: {CONFIG_FILE}")
        parser.read(CONFIG_FILE)
        print("DEBUG: Config file read successful.")
    except Exception as e:
        print(f"DEBUG: !!! CRITICAL ERROR in _load_contexts !!!")
        print(f"DEBUG: Error details: {e}")
        console.print(f"[bold red]Error:[/bold red] Could not read config file.")
        console.print(f"[italic]{e}[/italic]")
        sys.exit(1)
        
    print(f"DEBUG: Sections found in config file: {parser.sections()}")
    print("DEBUG: --- Exiting _load_contexts() ---")
    return parser

def _save_context(profile_name: str, base_url: str, username: str, token: str):
    """
    Saves a new context (including token) to the config.ini file.
    """
    print("DEBUG: --- Entering _save_context() ---")
    parser = _load_contexts()
    
    if profile_name not in parser:
        print(f"DEBUG: Adding new section to config: [{profile_name}]")
        parser.add_section(profile_name)
    
    print("DEBUG: Setting base_url, username, and token in config.")
    parser.set(profile_name, "base_url", base_url)
    parser.set(profile_name, "username", username)
    parser.set(profile_name, "token", token) 
    
    try:
        print(f"DEBUG: Writing changes to config file: {CONFIG_FILE}")
        with open(CONFIG_FILE, 'w') as f:
            parser.write(f)
        print("DEBUG: Write successful.")
    except Exception as e:
        print(f"DEBUG: !!! CRITICAL ERROR in _save_context !!!")
        print(f"DEBUG: Error details: {e}")
        console.print(f"[bold red]Error:[/bold red] Failed to write to config file.")
        console.print(f"[italic]{e}[/italic]")
        return

    console.print(f"\n[green]✅ Context '[bold]{profile_name}[/bold]' saved successfully.[/green]")
    console.print(f"[bold yellow]⚠️ Security Warning: Token was saved in plain text to {CONFIG_FILE}[/bold yellow]")
    print("DEBUG: --- Exiting _save_context() ---")
        

def _prompt_for_new_context() -> dict:
    """
    Runs the prompt to get new credentials from the user.
    """
    print("DEBUG: --- Entering _prompt_for_new_context() ---")
    try:
        print("DEBUG: Asking for Base URL...")
        base_url = questionary.text(
            "Enter the Base URL (e.g. https://mycompany.jfrog.io):",
            validate=lambda text: True if text.startswith("http") else "URL must start with 'http://' or 'https://'"
        ).ask()
        if base_url is None: 
            print("DEBUG: User cancelled at Base URL.")
            return None

        print("DEBUG: Asking for Username...")
        username = questionary.text(
            "Username:",
            validate=lambda text: True if len(text) > 0 else "Username cannot be empty"
        ).ask()
        if username is None: 
            print("DEBUG: User cancelled at Username.")
            return None

        print("DEBUG: Asking for Token/Password...")
        token = questionary.password(
            "Password or API Token (input is hidden):",
            validate=lambda text: True if len(text) > 0 else "Password/Token cannot be empty"
        ).ask()
        if token is None: 
            print("DEBUG: User cancelled at Password.")
            return None

        # --- Save Context ---
        print("DEBUG: Asking 'Do you want to save'...")
        save = questionary.confirm("Do you want to save these credentials?").ask()
        if save:
            print("DEBUG: User chose to save.")
            profile_name = questionary.text(
                "Enter a profile name to save these credentials (e.g., 'my-work', 'customer-x'):"
            ).ask()
            if profile_name:
                print(f"DEBUG: User provided profile name '{profile_name}'. Calling _save_context().")
                _save_context(profile_name, base_url, username, token)
            else:
                print("DEBUG: User did not provide profile name. Not saving.")
                console.print("[yellow]No profile name given. Credentials were not saved.[/yellow]")
        else:
            print("DEBUG: User chose not to save.")
        
        if base_url.endswith("/"):
            base_url = base_url[:-1]
            
        print("DEBUG: --- Exiting _prompt_for_new_context() ---")
        return {"base_url": base_url, "username": username, "token": token}

    except KeyboardInterrupt:
        print("DEBUG: KeyboardInterrupt caught in _prompt_for_new_context.")
        return None

def get_credentials() -> dict:
    """
    Main function to get credentials.
    Loads existing contexts or prompts for new ones.
    """
    print("DEBUG: --- Entering get_credentials() ---")
    console.print("\n🔐 [bold cyan]JFrog Platform Authentication[/bold cyan]")
    
    parser = _load_contexts()
    contexts = parser.sections()
    print(f"DEBUG: Contexts found: {contexts}")
    
    if not contexts:
        print("DEBUG: No contexts found. Calling _prompt_for_new_context().")
        console.print("[yellow]No saved credentials found. Please add a new context.[/yellow]")
        return _prompt_for_new_context()
    
    # --- Build Choices Menu ---
    print("DEBUG: Building context selection menu.")
    choices = []
    for context_name in contexts:
        url = parser.get(context_name, 'base_url', fallback='N/A')
        user = parser.get(context_name, 'username', fallback='N/A')
        choices.append(
            questionary.Choice(
                title=f"[{context_name}] {user} @ {url}",
                value=context_name
            )
        )
    
    choices.append(questionary.Separator())
    choices.append(questionary.Choice(title="[ Add New Credentials... ]", value="--new--"))
    choices.append(questionary.Choice(title="[ Exit ]", value="--exit--"))
    
    try:
        print("DEBUG: Asking user to select context.")
        selected_context = questionary.select(
            "Select credentials to use:",
            choices=choices
        ).ask()

        if selected_context is None or selected_context == "--exit--":
            print("DEBUG: User selected Exit or cancelled.")
            return None 
        
        if selected_context == "--new--":
            print("DEBUG: User selected Add New.")
            return _prompt_for_new_context()
        
        print(f"DEBUG: User selected context '{selected_context}'.")
        console.print(f"[green]Using saved context '[bold]{selected_context}[/bold]'...[/green]")
        
        creds = {
            "base_url": parser.get(selected_context, 'base_url'),
            "username": parser.get(selected_context, 'username'),
            "token": parser.get(selected_context, 'token', fallback=None)
        }
        
        if not creds["token"]:
            print(f"DEBUG: !!! ERROR: Token for '{selected_context}' not found in config file.")
            console.print(f"[bold red]Error:[/bold red] Token for '{selected_context}' not found in config file.")
            return None 
        
        if creds["base_url"].endswith("/"):
            creds["base_url"] = creds["base_url"][:-1]
            
        print("DEBUG: --- Exiting get_credentials() ---")
        return creds

    except KeyboardInterrupt:
        print("DEBUG: KeyboardInterrupt caught in get_credentials.")
        return None