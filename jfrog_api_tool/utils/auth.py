# jfrog_api_tool/utils/auth.py

import questionary
import configparser
import sys
import os
from pathlib import Path
from rich.console import Console
from cryptography.fernet import Fernet 

# Import config for debug flag
from jfrog_api_tool import config

console = Console()

# --- Settings ---
CONFIG_DIR = Path.home() / ".config" / "jfrog-api-tool"
CONFIG_FILE = CONFIG_DIR / "config.ini"
KEY_FILE = CONFIG_DIR / ".secret.key"  # 

# --- Encryption Helpers ---
def _get_cipher_suite():
    """
    Loads or creates the encryption key and returns a Fernet cipher suite.
    """
    # 1. Ensure directory exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 2. Check if key exists, otherwise generate it
    if not KEY_FILE.exists():
        if config.IS_DEBUG: print("DEBUG: Generating new encryption key...")
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
    else:
        if config.IS_DEBUG: print("DEBUG: Loading existing encryption key...")
        with open(KEY_FILE, "rb") as key_file:
            key = key_file.read()
            
    return Fernet(key)

def _encrypt_token(token: str) -> str:
    """Encrypts the token."""
    if not token: return ""
    cipher = _get_cipher_suite()
    return cipher.encrypt(token.encode()).decode()

def _decrypt_token(encrypted_token: str) -> str:
    """Decrypts the token."""
    if not encrypted_token: return ""
    cipher = _get_cipher_suite()
    try:
        return cipher.decrypt(encrypted_token.encode()).decode()
    except Exception as e:
        if config.IS_DEBUG: print(f"DEBUG: Decryption failed: {e}")
        return None

# --- Config Logic ---

def _init_config():
    """Ensures config dir and file exist."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not CONFIG_FILE.is_file():
            CONFIG_FILE.touch()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Could not create config directory.")
        sys.exit(1)

def _load_contexts() -> configparser.ConfigParser:
    """Loads contexts from config.ini."""
    _init_config()
    parser = configparser.ConfigParser()
    try:
        parser.read(CONFIG_FILE)
    except Exception:
        sys.exit(1)
    return parser

def _save_context(profile_name: str, base_url: str, username: str, token: str):
    """Saves context with ENCRYPTED token."""
    parser = _load_contexts()
    
    if profile_name not in parser:
        parser.add_section(profile_name)
    
    parser.set(profile_name, "base_url", base_url)
    parser.set(profile_name, "username", username)
    
    # --- ENCRYPTION HAPPENS HERE ---
    encrypted_token = _encrypt_token(token)
    parser.set(profile_name, "token", encrypted_token) 
    # -------------------------------
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            parser.write(f)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to write to config file.")
        return

    console.print(f"\n[green]✅ Context '[bold]{profile_name}[/bold]' saved successfully.[/green]")
    console.print(f"[dim]Token stored securely (encrypted locally).[/dim]")

def _prompt_for_new_context() -> dict:
    """Prompts user for new credentials."""
    try:
        base_url = questionary.text("Enter Base URL:").ask()
        if not base_url: return None

        username = questionary.text("Username:").ask()
        if not username: return None

        token = questionary.password("Password / API Token:").ask()
        if not token: return None

        save = questionary.confirm("Save these credentials?").ask()
        if save:
            profile_name = questionary.text("Profile Name (e.g. 'work'):").ask()
            if profile_name:
                _save_context(profile_name, base_url, username, token)
        
        if base_url.endswith("/"): base_url = base_url[:-1]
        return {"base_url": base_url, "username": username, "token": token}

    except KeyboardInterrupt:
        return None

def get_credentials() -> dict:
    """Main entry to get credentials."""
    console.print("\n🔐 [bold cyan]JFrog Platform Authentication[/bold cyan]")
    
    parser = _load_contexts()
    contexts = parser.sections()
    
    if not contexts:
        console.print("[yellow]No saved credentials found. Please add a new context.[/yellow]")
        return _prompt_for_new_context()
    
    choices = []
    for context_name in contexts:
        url = parser.get(context_name, 'base_url', fallback='N/A')
        user = parser.get(context_name, 'username', fallback='N/A')
        choices.append(questionary.Choice(title=f"[{context_name}] {user} @ {url}", value=context_name))
    
    choices.append(questionary.Separator())
    choices.append(questionary.Choice(title="[ Add New Credentials... ]", value="--new--"))
    choices.append(questionary.Choice(title="[ Exit ]", value="--exit--"))
    
    try:
        selected_context = questionary.select("Select credentials:", choices=choices).ask()

        if selected_context is None or selected_context == "--exit--": return None 
        if selected_context == "--new--": return _prompt_for_new_context()
        
        console.print(f"[green]Using saved context '[bold]{selected_context}[/bold]'...[/green]")
        
        # Retrieve encrypted token
        encrypted_token = parser.get(selected_context, 'token', fallback=None)
        
        # --- DECRYPTION HAPPENS HERE ---
        decrypted_token = _decrypt_token(encrypted_token)
        
        if not decrypted_token:
            console.print(f"[bold red]Error:[/bold red] Could not decrypt token for '{selected_context}'.")
            console.print("The key file might be missing or the token is corrupted.")
            console.print("Please re-add this profile.")
            return None
        # -------------------------------

        creds = {
            "base_url": parser.get(selected_context, 'base_url'),
            "username": parser.get(selected_context, 'username'),
            "token": decrypted_token
        }
        
        if creds["base_url"].endswith("/"): creds["base_url"] = creds["base_url"][:-1]
        return creds

    except KeyboardInterrupt:
        return None