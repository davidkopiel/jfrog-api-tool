# jfrog_api_tool/wizards/reindex_wizard.py
import questionary
from rich.console import Console
from typing import Dict, Any

console = Console()

def run_force_reindex_wizard() -> Dict[str, Any]:
    """
    Runs an interactive wizard to build the complex JSON body for Force Reindex.
    """
    console.print("\n[bold]Starting 'Force Reindex' wizard...[/bold]")
    reindex_type = questionary.select(
        "What do you want to reindex?",
        choices=["An Artifact", "A Build"]
    ).ask()
    if reindex_type is None: return None
    json_body = {}
    if reindex_type == "An Artifact":
        repo = questionary.text("Enter repository:").ask()
        path = questionary.text("Enter path:").ask()
        if repo is None or path is None: return None
        json_body = {"artifacts": [{"repository": repo, "path": path}]}
    elif reindex_type == "A Build":
        name = questionary.text("Enter build name:").ask()
        number = questionary.text("Enter build number:").ask()
        if name is None or number is None: return None
        json_body = {"builds": [{"name": name, "number": number}]}
    
    return {"__json_body_from_file__": json_body}