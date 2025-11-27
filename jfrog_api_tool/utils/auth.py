# jfrog_api_tool/utils/auth.py

import os
from rich.console import Console

console = Console()

def get_credentials() -> dict:
    """
    Retrieves credentials injected by the JFrog CLI via environment variables.
    """
    
    # 1. Try to get the context from environment variables
    # JFrog CLI adds these automatically when running a plugin
    base_url = os.getenv("JFROG_CLI_OFFER_URL")
    username = os.environ.get("JFROG_CLI_OFFER_USER")
    token = os.environ.get("JFROG_CLI_OFFER_ACCESS_TOKEN") or os.environ.get("JFROG_CLI_OFFER_PASSWORD")

    # 2. Fail gracefully if not running via CLI
    if not base_url or not token:
        console.print("\n[bold red]❌ Error: JFrog CLI context not found.[/bold red]")
        console.print("[yellow]This tool is designed to run as a JFrog CLI Plugin.[/yellow]")
        console.print("Please run it using the command: [bold]jf jfat[/bold]")
        return None

    # 3. Normalize URL (remove trailing slash if exists)
    if base_url.endswith("/"):
        base_url = base_url[:-1]

    # 4. Return standard dictionary
    return {
        "base_url": base_url,
        "username": username,
        "token": token
    }