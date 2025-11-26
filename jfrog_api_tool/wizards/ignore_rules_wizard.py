# jfrog_api_tool/wizards/ignore_rules_wizard.py

import questionary
from rich.console import Console
from typing import Dict, Any, List

console = Console()

def _add_source_filters(filters: Dict[str, Any]):
    """Step 1: Define WHAT to ignore (Vulnerabilities, CVEs, Licenses, etc.)"""
    
    options = [
        "Specific CVEs",
        "Specific Vulnerabilities (XRAY-ID)",
        "Specific Licenses",
        "Specific Policies",
        "Specific Watches",
        "Any Vulnerability",
        "Any License"
    ]
    
    selection = questionary.checkbox("What do you want to ignore?", choices=options).ask()
    if not selection: return

    if "Specific CVEs" in selection:
        val = questionary.text("Enter CVEs (comma separated):").ask()
        if val: filters["cves"] = [x.strip() for x in val.split(',')]

    if "Specific Vulnerabilities (XRAY-ID)" in selection:
        val = questionary.text("Enter Xray IDs (comma separated):").ask()
        if val: filters["vulnerabilities"] = [x.strip() for x in val.split(',')]

    if "Specific Licenses" in selection:
        val = questionary.text("Enter License Names (comma separated):").ask()
        if val: filters["licenses"] = [x.strip() for x in val.split(',')]

    if "Specific Policies" in selection:
        val = questionary.text("Enter Policy Names (comma separated):").ask()
        if val: filters["policies"] = [x.strip() for x in val.split(',')]

    if "Specific Watches" in selection:
        val = questionary.text("Enter Watch Names (comma separated):").ask()
        if val: filters["watches"] = [x.strip() for x in val.split(',')]

    if "Any Vulnerability" in selection:
        filters["vulnerabilities"] = ["any"]

    if "Any License" in selection:
        filters["licenses"] = ["any"]


def _add_scope_filters(filters: Dict[str, Any]):
    """Step 2: Define WHERE to ignore it (Components, Artifacts, Builds...)"""
    
    scope_type = questionary.select(
        "Apply this rule on:",
        choices=[
            "Global (Everything)",
            "Specific Components (Packages)",
            "Specific Artifacts (Files in Repo)",
            "Specific Builds",
            "Specific Release Bundles"
        ]
    ).ask()

    if scope_type == "Global (Everything)":
        return # No extra filters needed

    # --- Components Scope ---
    if scope_type == "Specific Components (Packages)":
        comps = []
        while True:
            console.print("[italic]Add Component (e.g. docker://alpine, npm://lodash)[/italic]")
            name = questionary.text("Component Name (Package ID):").ask()
            version = questionary.text("Version (Optional):").ask()
            
            comp_obj = {"name": name}
            if version: comp_obj["version"] = version
            comps.append(comp_obj)
            
            if not questionary.confirm("Add another component?").ask(): break
        filters["components"] = comps

    # --- Artifacts Scope ---
    elif scope_type == "Specific Artifacts (Files in Repo)":
        arts = []
        while True:
            console.print("[italic]Add Artifact (e.g. docker://image)[/italic]")
            name = questionary.text("Artifact Name:").ask()
            version = questionary.text("Version (Optional):").ask()
            path = questionary.text("Path Pattern (Optional, e.g. 'libs-release/*'):").ask()
            
            art_obj = {"name": name}
            if version: art_obj["version"] = version
            if path: art_obj["path"] = path
            arts.append(art_obj)
            
            if not questionary.confirm("Add another artifact?").ask(): break
        filters["artifacts"] = arts

    # --- Builds Scope ---
    elif scope_type == "Specific Builds":
        builds = []
        while True:
            name = questionary.text("Build Name:").ask()
            version = questionary.text("Build Number (Optional):").ask()
            project = questionary.text("Project Key (Optional):").ask()
            
            b_obj = {"name": name}
            if version: b_obj["version"] = version
            if project: b_obj["project"] = project
            builds.append(b_obj)
            
            if not questionary.confirm("Add another build?").ask(): break
        filters["builds"] = builds


def run_create_ignore_rule_wizard() -> Dict[str, Any]:
    """
    Wizard to create a new Xray Ignore Rule.
    """
    console.print("\n[bold]Starting Create Ignore Rule Wizard...[/bold]")
    
    # 1. Basic Info
    notes = questionary.text("Reason / Notes (Required):").ask()
    if not notes: return None
    
    expires_at = questionary.text("Expiration Date (YYYY-MM-DD, Optional):").ask()

    # 2. Build Filters
    ignore_filters = {}
    
    console.print("\n[bold cyan]1. Define WHAT to ignore (Source)[/bold cyan]")
    _add_source_filters(ignore_filters)
    
    console.print("\n[bold cyan]2. Define WHERE to ignore it (Scope)[/bold cyan]")
    _add_scope_filters(ignore_filters)

    # 3. Construct Body
    json_body = {
        "notes": notes,
        "ignore_filters": ignore_filters
    }
    
    if expires_at:
        # Xray expects ISO format usually, but simple date might work or need 'T00:00:00Z'
        if "T" not in expires_at: expires_at += "T00:00:00Z"
        json_body["expires_at"] = expires_at

    return {"__json_body_from_file__": json_body}