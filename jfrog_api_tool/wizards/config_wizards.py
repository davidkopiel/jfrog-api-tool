# jfrog_api_tool/wizards/config_wizards.py
import questionary
from rich.console import Console
from typing import Dict, Any

console = Console()

def run_configure_workers_wizard() -> Dict[str, Any]:
    """
    Runs an interactive wizard to build the workers count JSON body.
    Uses defaults from the sample usage.
    """
    console.print("\n[bold]Starting 'Configure Workers Count' wizard...[/bold]")
    console.print("[italic]Press Enter to accept the default value (e.g., [8]).[/italic]")

    try:
        json_body = {
            "index": {
                "new_content": int(questionary.text("Index [new_content]:", default="8").ask()),
                "existing_content": int(questionary.text("Index [existing_content]:", default="4").ask())
            },
            "persist": {
                "new_content": int(questionary.text("Persist [new_content]:", default="8").ask()),
                "existing_content": int(questionary.text("Persist [existing_content]:", default="4").ask())
            },
            "analysis": {
                "new_content": int(questionary.text("Analysis [new_content]:", default="8").ask()),
                "existing_content": int(questionary.text("Analysis [existing_content]:", default="4").ask())
            },
            "policy_enforcer": {
                "new_content": int(questionary.text("Policy Enforcer [new_content]:", default="8").ask()),
                "existing_content": int(questionary.text("Policy Enforcer [existing_content]:", default="8").ask())
            },
            "sbom": {
                "new_content": int(questionary.text("SBOM [new_content]:", default="0").ask()),
                "existing_content": int(questionary.text("SBOM [existing_content]:", default="0").ask())
            },
            "usercatalog": {
                "new_content": int(questionary.text("User Catalog [new_content]:", default="0").ask()),
                "existing_content": int(questionary.text("User Catalog [existing_content]:", default="0").ask())
            },
            "sbomimpactanalysis": {
                "new_content": int(questionary.text("SBOM Impact Analysis [new_content]:", default="0").ask()),
                "existing_content": int(questionary.text("SBOM Impact Analysis [existing_content]:", default="0").ask())
            },
            "migrationsbom": {
                "new_content": int(questionary.text("Migration SBOM [new_content]:", default="0").ask()),
                "existing_content": int(questionary.text("Migration SBOM [existing_content]:", default="0").ask())
            },
            "impact_analysis": {
                "new_content": int(questionary.text("Impact Analysis [new_content]:", default="8").ask())
            },
            "notification": {
                "new_content": int(questionary.text("Notification [new_content]:", default="8").ask())
            },
            "panoramic": {
                "new_content": int(questionary.text("Panoramic [new_content]:", default="0").ask())
            }
        }
    except (ValueError, TypeError):
        console.print("[bold red]Error: All values must be valid numbers.[/bold red]")
        return None
    except KeyboardInterrupt:
        return None

    # Return the body using the special key
    return {"__json_body_from_file__": json_body}