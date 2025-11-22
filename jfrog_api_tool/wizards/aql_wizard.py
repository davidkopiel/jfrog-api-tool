# jfrog_api_tool/wizards/aql_wizard.py

import json
import questionary
from rich.console import Console
from typing import Dict, Any, List

console = Console()

# --- TEMPLATES LIBRARY ---
TEMPLATES = {
    "🏆 Top 10 Largest Files": {
        "domain": "items",
        "description": "Finds the largest files to help clean up storage.",
        "aql": 'items.find({"type":"file"}).include("name","repo","path","size").sort({"$desc":["size"]}).limit(10)'
    },
    "🐳 List Docker Images": {
        "domain": "items",
        "description": "Finds Docker images by looking for manifest.json files.",
        "aql": 'items.find({"name":"manifest.json"}).include("repo","path").sort({"$asc":["repo"]}).limit(20)'
    },
    "☕ Find JAR containing class (Deep Search)": {
        "domain": "items",
        "description": "Finds which JAR file contains a specific class file.",
        "requires_input": "Enter Class Name (e.g. Log4j.class):",
        "aql_template": 'items.find({"archive.entry.name": {"$match": "*{INPUT}*"}}).include("name","repo","path")'
    },
    "🏗️ Find Latest Builds": {
        "domain": "builds",
        "description": "Returns the 10 most recent builds in the system.",
        "aql": 'builds.find().include("name","number","started","created_by").sort({"$desc":["started"]}).limit(10)'
    },
    "🕸️ Find by SHA1": {
        "domain": "items",
        "description": "Locates an artifact by its checksum.",
        "requires_input": "Enter SHA1 Hash:",
        "aql_template": 'items.find({"actual_sha1": "{INPUT}"}).include("name","repo","path")'
    }
}

def _get_operator(label: str) -> str:
    """Helper to map readable choices to AQL operators."""
    if "Equals" in label: return "$eq"
    if "Match (Wildcard)" in label: return "$match"
    if "Not Equals" in label: return "$ne"
    if "Greater" in label: return "$gt"
    if "Less" in label: return "$lt"
    if "Before" in label: return "$before"
    if "Last" in label: return "$last"
    return "$eq"

# --- BUILDER 1: ITEMS (FILES) ---
def _build_advanced_item_query() -> str:
    """Builder for Artifacts/Files queries."""
    console.print("\n[bold cyan]🏗️  AQL Builder: Items (Files)[/bold cyan]")
    criteria = {}

    while True:
        if criteria: console.print(f"[green]Current Filters:[/green] {json.dumps(criteria)}")
        
        add_filter = questionary.select(
            "Add Filter:",
            choices=[
                "Repository (Required)", 
                "Name / Path", 
                "File Size", 
                "Creation Date", 
                "File INSIDE Archive (Deep Search)", # <-- NEW VALID FILTER
                "Download Stats", 
                "Property",
                questionary.Separator(), "✅ Done", "❌ Cancel"
            ]
        ).ask()

        if add_filter == "❌ Cancel": return None
        
        if add_filter == "✅ Done": 
            if "repo" not in criteria:
                console.print("[bold red]⚠️  Repository filter is required for Items![/bold red]")
                continue
            break

        # -- Item Filters Logic --
        if "Repository" in add_filter:
            console.print("[dim]Hint: Use specific name ('libs-release') or wildcard ('libs-*')[/dim]")
            val = questionary.text("Repo Name:").ask()
            if val: criteria["repo"] = {"$match": val} if "*" in val else {"$eq": val}

        elif "Name" in add_filter:
            console.print("[dim]Hint: The file name itself (e.g. 'myapp.jar')[/dim]")
            val = questionary.text("File Name Pattern:").ask()
            if val: criteria["name"] = {"$match": val}

        elif "File Size" in add_filter:
            op = questionary.select("Size:", choices=["Greater (>)", "Less (<)"]).ask()
            mb = questionary.text("Size (MB):").ask()
            if mb.isdigit():
                criteria["size"] = {_get_operator(op): int(mb)*1024*1024}

        elif "Creation Date" in add_filter:
            val = questionary.text("Date (e.g. '2w', '2023-01-01'):").ask()
            if val: criteria["created"] = {"$last" if len(val) < 4 else "$before": val}

        # --- NEW VALID IMPLEMENTATION ---
        elif "File INSIDE Archive" in add_filter:
            console.print("[dim]Find zip/jar files that contain a specific file inside them.[/dim]")
            val = questionary.text("Inner File Name (e.g. 'log4j.class'):").ask()
            if val: criteria["archive.entry.name"] = {"$match": val}
        # --------------------------------

        elif "Download Stats" in add_filter:
            if questionary.confirm("Never Downloaded?").ask():
                criteria["stat.downloads"] = {"$eq": None}

        elif "Property" in add_filter:
            k = questionary.text("Key (e.g. @status):").ask()
            v = questionary.text("Value:").ask()
            if k and v: criteria[k if k.startswith("@") else "@"+k] = {"$match": v}

    # Output Fields
    fields = questionary.checkbox("Output Fields:", choices=[
        questionary.Choice("name", checked=True),
        questionary.Choice("repo", checked=True),
        questionary.Choice("path", checked=True),
        questionary.Choice("size"),
        questionary.Choice("created"),
        questionary.Choice("stat.downloads")
    ]).ask()
    if not fields: fields = ["name", "repo"]
    
    fields_str = ','.join([f'"{f}"' for f in fields])
    limit = questionary.text("Limit:", default="50").ask()
    
    return f'items.find({json.dumps(criteria)}).include({fields_str}).limit({limit})'


# --- BUILDER 2: BUILDS (CI/CD) ---
def _build_advanced_build_query() -> str:
    """Builder for Build Info queries."""
    console.print("\n[bold cyan]🏗️  AQL Builder: Builds (CI/CD)[/bold cyan]")
    criteria = {}

    while True:
        if criteria: console.print(f"[green]Current Filters:[/green] {json.dumps(criteria)}")
        
        add_filter = questionary.select(
            "Add Filter:",
            choices=[
                "Build Name", "Build Number", "Started Date", 
                "Created By (User)", "Property",
                questionary.Separator(), "✅ Done", "❌ Cancel"
            ]
        ).ask()

        if add_filter == "❌ Cancel": return None
        if add_filter == "✅ Done": break

        # -- Build Filters Logic --
        if "Build Name" in add_filter:
            val = questionary.text("Build Name (supports *):").ask()
            if val: criteria["name"] = {"$match": val} if "*" in val else {"$eq": val}

        elif "Build Number" in add_filter:
            val = questionary.text("Build Number:").ask()
            if val: criteria["number"] = {"$eq": val}

        elif "Started Date" in add_filter:
            val = questionary.text("Started (e.g. '2w', '2023-01-01'):").ask()
            if val: criteria["started"] = {"$last" if len(val) < 4 else "$before": val}

        elif "Created By" in add_filter:
            val = questionary.text("Username:").ask()
            if val: criteria["created_by"] = {"$eq": val}

        elif "Property" in add_filter:
            k = questionary.text("Key (e.g. @release):").ask()
            v = questionary.text("Value:").ask()
            if k and v: criteria[k if k.startswith("@") else "@"+k] = {"$match": v}

    # Output Fields
    fields = questionary.checkbox("Output Fields:", choices=[
        questionary.Choice("name", checked=True),
        questionary.Choice("number", checked=True),
        questionary.Choice("started", checked=True),
        questionary.Choice("created_by"),
        questionary.Choice("url")
    ]).ask()
    if not fields: fields = ["name", "number"]

    fields_str = ','.join([f'"{f}"' for f in fields])
    limit = questionary.text("Limit:", default="50").ask()

    return f'builds.find({json.dumps(criteria)}).include({fields_str}).sort({{"$desc":["started"]}}).limit({limit})'


# --- MAIN ROUTER ---
def _run_template_wizard() -> str:
    choices = list(TEMPLATES.keys())
    selected_name = questionary.select("Choose a template:", choices=choices).ask()
    if not selected_name: return None
    
    template = TEMPLATES[selected_name]
    console.print(f"\n[italic]{template['description']}[/italic]")
    
    if "requires_input" in template:
        user_val = questionary.text(template["requires_input"]).ask()
        if not user_val: return None
        return template["aql_template"].replace("{INPUT}", user_val)
    
    return template["aql"]

def run_aql_wizard() -> Dict[str, Any]:
    """Main entry point."""
    console.print("\n[bold]Starting AQL Query Wizard...[/bold]")
    
    mode = questionary.select(
        "Select AQL Mode:",
        choices=[
            "🏗️  Interactive Builder (Recommended)",
            "📚 Run Common Template",
            "✍️  Type Manually", 
            "📂 Read from File"
        ]
    ).ask()
    
    if not mode: return None
    aql_query = ""

    if "Interactive" in mode:
        # 2. Choose Domain
        domain = questionary.select(
            "What are you looking for?",
            choices=[
                "📦 Artifacts / Files (items)",
                "🏗️  Builds / CI Info (builds)",
                # REMOVED: "📂 Archive Content (entries)" -> This domain is deprecated
            ]
        ).ask()
        
        if "items" in domain:
            aql_query = _build_advanced_item_query()
        elif "builds" in domain:
            aql_query = _build_advanced_build_query()

    elif "Template" in mode:
        aql_query = _run_template_wizard()

    elif "Manual" in mode:
        aql_query = questionary.text("Enter AQL Query:").ask()

    elif "File" in mode:
        path = questionary.path("Path:").ask()
        if path:
            try:
                with open(path, 'r') as f: aql_query = f.read()
            except: return None

    if not aql_query: return None
    return {"__json_body_from_file__": aql_query}