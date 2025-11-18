# jfrog_api_tool/wizards/gc_wizards.py
import questionary
from rich.console import Console
from typing import Dict, Any

console = Console()

def run_force_gc_start_wizard() -> Dict[str, Any]:
    """
    Runs an interactive wizard to build the Force GC JSON body.
    """
    console.print("\n[bold]Starting 'Force GC to Run' wizard...[/bold]")

    try:
        max_duration = int(questionary.text("Enter Max Duration (seconds):", default="3600").ask())
        json_body = {
            "max_duration_seconds": max_duration
        }
    except (ValueError, TypeError):
        console.print("[bold red]Error: You must enter a valid number.[/bold red]")
        return None
    except KeyboardInterrupt:
        return None

    # Return the body using the special key
    return {"__json_body_from_file__": json_body}

def run_set_gc_config_wizard() -> Dict[str, Any]:
    """
    Runs an interactive wizard to build the GC config JSON body.
    """
    console.print("\n[bold]Starting 'Set GC Configuration' wizard...[/bold]")
    console.print("[italic]Press Enter to accept the default value.[/italic]")

    try:
        json_body = {
            "scheduler_enabled": questionary.confirm("Scheduler Enabled?", default=True).ask(),
            "scheduler_period_minutes": int(questionary.text("Scheduler Period (minutes):", default="60").ask()),
            "max_duration_seconds": int(questionary.text("Max Duration (seconds):", default="3600").ask()),
            "max_retry_count": int(questionary.text("Max Retry Count:", default="3").ask()),
            "Idle_listener_enabled": questionary.confirm("Idle Listener Enabled?", default=True).ask(),
            "Idle_listener_gc_duration_seconds": int(questionary.text("Idle Listener GC Duration (seconds):", default="600").ask()),
            "Idle_listener_sampling_rate_seconds": int(questionary.text("Idle Listener Sampling Rate (seconds):", default="60").ask())
        }
    except (ValueError, TypeError):
        console.print("[bold red]Error: All values must be valid numbers.[/bold red]")
        return None
    except KeyboardInterrupt:
        return None

    # Return the body using the special key
    return {"__json_body_from_file__": json_body}