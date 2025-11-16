# jfrog_api_tool/main.py

import sys
import questionary
import os
import json
import importlib.resources
from rich.console import Console
from rich.panel import Panel
from typing import Dict, Any

# --- 1. Flag Handling Logic ---
# Must run before importing other modules

# Import the new config file
from jfrog_api_tool import config 

# New help function
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

# Check if user asked for help
if "--help" in sys.argv:
    _print_help()
    sys.exit(0)

# Check if debug mode should be enabled
if "--debug" in sys.argv or os.environ.get("JFAT_DEBUG") == "true":
    config.IS_DEBUG = True
    print("!!! DEBUG MODE ENABLED !!!")

# --- 2. Standard Imports ---
# (Now that flags are set, import the rest of the tool)
from jfrog_api_tool.utils import auth, api_runner

# Initialize Rich console
console = Console()

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


# --- Policy Wizard Helper: Build Actions ---
def _build_actions() -> Dict[str, Any]:
    """
    Interactive wizard to build the 'actions' object for a policy rule.
    Returns None if user cancels.
    """
    actions = {}
    console.print("\n[bold]Building Rule Actions:[/bold]")
    
    selected_actions = questionary.checkbox(
        "Select actions to configure:",
        choices=[
            "fail_build",
            "block_download",
            "notify_deployer",
            "notify_watch_recipients",
            "mails",
            "custom_severity"
        ]
    ).ask()

    if selected_actions is None: return None # User cancelled

    if "fail_build" in selected_actions:
        actions["fail_build"] = questionary.confirm("Fail build?", default=True).ask()

    if "block_download" in selected_actions:
        actions["block_download"] = {
            "active": questionary.confirm("Block download (active)?", default=True).ask(),
            "unscanned": questionary.confirm("Block download (unscanned)?", default=True).ask()
        }

    if "notify_deployer" in selected_actions:
        actions["notify_deployer"] = questionary.confirm("Notify deployer?", default=True).ask()
    
    if "notify_watch_recipients" in selected_actions:
        actions["notify_watch_recipients"] = questionary.confirm("Notify watch recipients?", default=True).ask()

    if "mails" in selected_actions:
        mails_str = questionary.text("Enter emails (comma-separated):").ask()
        if mails_str:
            actions["mails"] = [email.strip() for email in mails_str.split(',')]

    if "custom_severity" in selected_actions:
        actions["custom_severity"] = questionary.select(
            "Set custom severity:",
            choices=["low", "medium", "high", "critical"]
        ).ask()
        
    return actions

# --- Policy Wizard Helper: Build Criteria ---
def _build_criteria() -> Dict[str, Any]:
    """
    Interactive wizard to build the 'criteria' object for a policy rule.
    Returns None if user cancels.
    """
    criteria = {}
    console.print(f"\n[bold]Building Rule Criteria:[/bold]")
    
    criteria_choices = [
        "min_severity",
        "cvss_range",
        "vulnerability_ids",
        "fix_version_dependant",
        "applicable_cves_only",
        "malicious_package",
        "package_name",
        "package_type",
        "package_versions",
        "allowed_licenses",
        "banned_licenses",
        "allow_unknown",
        "multi_license_permissive",
        "op_risk_min_risk",
    ]
    
    selected_criteria = questionary.checkbox(
        "Select criteria to define (must select at least one):",
        choices=criteria_choices
    ).ask()

    if selected_criteria is None: return None 
    if not selected_criteria: 
        return {} 

    if "min_severity" in selected_criteria:
        criteria["min_severity"] = questionary.select(
            "Select minimum severity:",
            choices=["low", "medium", "high", "critical", "all severities"]
        ).ask()

    if "cvss_range" in selected_criteria:
        cvss_from = questionary.text("CVSS 'from' (0.0-10.0):").ask()
        cvss_to = questionary.text("CVSS 'to' (0.0-10.0):").ask()
        criteria["cvss_range"] = {"from": float(cvss_from), "to": float(cvss_to)}

    if "vulnerability_ids" in selected_criteria:
        cves_str = questionary.text("Enter CVEs/XRAY-IDs (comma-separated):").ask()
        if cves_str:
            criteria["vulnerability_ids"] = [cve.strip() for cve in cves_str.split(',')]
    
    if "fix_version_dependant" in selected_criteria:
        criteria["fix_version_dependant"] = questionary.confirm("Only if fix is available?", default=True).ask()
    
    if "applicable_cves_only" in selected_criteria:
        criteria["applicable_cves_only"] = questionary.confirm("Applicable CVEs only?", default=True).ask()

    if "malicious_package" in selected_criteria:
        criteria["malicious_package"] = questionary.confirm("Malicious package?", default=True).ask()

    if "package_name" in selected_criteria:
        criteria["package_name"] = questionary.text("Enter package name (e.g., 'log4j'):").ask()

    if "package_type" in selected_criteria:
        criteria["package_type"] = questionary.select(
            "Select package type:",
            choices=["maven", "docker", "npm", "pypi", "nuget", "generic", "golang"]
        ).ask()
        
    if "package_versions" in selected_criteria:
        vers_str = questionary.text("Enter package versions (e.g., '[1.1],(2.0,)'):").ask()
        if vers_str:
             criteria["package_versions"] = [v.strip() for v in vers_str.split(',')]

    if "allowed_licenses" in selected_criteria:
        lic_str = questionary.text("Enter allowed licenses (comma-separated):").ask()
        if lic_str:
            criteria["allowed_licenses"] = [lic.strip() for lic in lic_str.split(',')]
    
    if "banned_licenses" in selected_criteria:
        lic_str = questionary.text("Enter banned licenses (comma-separated):").ask()
        if lic_str:
            criteria["banned_licenses"] = [lic.strip() for lic in lic_str.split(',')]
    
    if "allow_unknown" in selected_criteria:
        criteria["allow_unknown"] = questionary.confirm("Allow unknown licenses?", default=True).ask()
        
    if "multi_license_permissive" in selected_criteria:
        criteria["multi_license_permissive"] = questionary.confirm("Multi-license permissive?", default=True).ask()

    if "op_risk_min_risk" in selected_criteria:
        criteria["op_risk_min_risk"] = questionary.select(
            "Select minimum operational risk:",
            choices=["low", "medium", "high"]
        ).ask()
        
    return criteria

# --- Policy Wizard Helper: Build a single Rule ---
def _build_policy_rule() -> Dict[str, Any]:
    """
    Runs an interactive wizard to build a single Policy Rule.
    """
    console.print("\n--- [bold green]Adding a New Rule[/bold green] ---")
    rule_name = questionary.text("Rule name:").ask()
    if rule_name is None: return None

    rule_priority = questionary.text("Rule priority (e.g., 1):", default="1").ask()
    if rule_priority is None: return None

    criteria = None
    while not criteria: 
        console.print("[yellow]A rule must have at least one criterion.[/yellow]")
        criteria = _build_criteria() 
        
        if criteria is None: 
             return None 
        
        if not criteria: 
            console.print("[bold red]Error: No criteria selected. Please define at least one.[/bold red]")

    actions = _build_actions()
    if actions is None: 
        return None
    
    return {
        "name": rule_name,
        "priority": int(rule_priority),
        "criteria": criteria,
        "actions": actions
    }

# --- WIZARD: Create Policy V2 ---
def _run_create_policy_wizard() -> Dict[str, Any]:
    """
    Runs the full interactive wizard for creating a V2 Policy.
    """
    console.print("\n[bold]Starting 'Create Policy (v2)' wizard...[/bold]")
    policy_body = {}
    rules = []
    
    policy_name = questionary.text("Policy name:").ask()
    if policy_name is None: return None
    
    policy_type = questionary.select(
        "Policy type:",
        choices=["security", "license", "operational_risk"]
    ).ask()
    if policy_type is None: return None
    
    policy_desc = questionary.text("Policy description (optional):").ask()
    
    policy_body["name"] = policy_name
    policy_body["type"] = policy_type
    if policy_desc:
        policy_body["description"] = policy_desc

    while True:
        new_rule = _build_policy_rule() 
        if new_rule:
            rules.append(new_rule)
        else:
            if not rules:
                console.print("[yellow]Policy creation cancelled.[/yellow]")
                return None
            else:
                break

        add_another = questionary.confirm("Add another rule?").ask()
        if not add_another:
            break
    
    if not rules:
        console.print("[bold red]Error: A policy must have at least one rule.[/bold red]")
        return None

    policy_body["rules"] = rules
    
    return {"__json_body_from_file__": policy_body}

# --- WIZARD: Force Reindex ---
def _run_force_reindex_wizard() -> Dict[str, Any]:
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

# --- Main Parameter Gathering Function ---
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
        console.print("\n[bold]Please provide query parameters (optional):[/bold]")
        for param in query_params:
            val = questionary.text(f"Enter value for '{param}' (press Enter to skip):").ask()
            if val is None: return None
            if val:
                params[param] = val

    body_input_mode = api_config.get("body_input_mode")
    wizard_name = api_config.get("wizard_name")

    if body_input_mode == "wizard":
        wizard_params = None
        
        if wizard_name == "force_reindex":
            wizard_params = _run_force_reindex_wizard()
        elif wizard_name == "create_policy_v2":
            wizard_params = _run_create_policy_wizard()
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
            selected_system = questionary.select(
                "Select system:",
                choices=list(api_config_data.keys())
            ).ask()
            if selected_system is None: break

            system_apis = api_config_data[selected_system]
            
            selected_api_name = questionary.select(
                f"Select API from {selected_system}:",
                choices=list(system_apis.keys())
            ).ask()
            if selected_api_name is None: break
                
            selected_api_config = system_apis[selected_api_name]
            
            user_params = get_user_params(selected_api_config)
            if user_params is None: break

            api_runner.execute_api_call(
                auth_details=credentials,
                api_config=selected_api_config,
                params=user_params
            )
            
            console.print("\n" + "="*50 + "\n")
            run_another = questionary.confirm("Do you want to run another API call?").ask()
            if not run_another:
                break

    except KeyboardInterrupt:
        pass

    console.print("\n[bold cyan]Goodbye![/bold cyan]")

if __name__ == "__main__":
    main()