# jfrog_api_tool/wizards/export_wizard.py
import questionary
from rich.console import Console
from typing import Dict, Any

console = Console()

def run_export_component_wizard() -> Dict[str, Any]:
    """
    Runs an interactive wizard to build the component export body.
    """
    console.print("\n[bold]Starting 'Export Component Details' wizard...[/bold]")
    
    try:
        # --- 1. Core Component Details (Required) ---
        console.print("[bold]Component Details (Required):[/bold]")
        package_type = questionary.text("Package Type (e.g., docker, maven, build):").ask()
        if not package_type: return None
        
        component_name = questionary.text("Component Name (e.g., image:tag):").ask()
        if not component_name: return None
        
        path = questionary.text("Path (e.g., my-repo/image/tag/manifest.json):").ask()
        if not path: return None

        json_body = {
            "package_type": package_type,
            "component_name": component_name,
            "path": path
        }

        # --- 2. Export Mode ---
        export_mode = questionary.select(
            "What do you want to export?",
            choices=[
                "Scan Results (PDF, CSV, JSON)",
                "SPDX SBOM",
                "CycloneDX SBOM"
            ]
        ).ask()
        if not export_mode: return None

        # --- 3. Mode-Specific Questions ---
        
        # Mode 1: Scan Results
        if export_mode == "Scan Results (PDF, CSV, JSON)":
            console.print("[bold]Scan Result Options:[/bold]")
            
            json_body["output_format"] = questionary.select(
                "Select output format:",
                choices=["pdf", "csv", "json", "json_full"],
                default="pdf"
            ).ask()
            
            console.print("[italic]Configure optional flags (Press Enter to accept default):[/italic]")
            json_body["violations"] = questionary.confirm("Include violations?", default=True).ask()
            json_body["include_ignored_violations"] = questionary.confirm("Include ignored violations?", default=True).ask()
            json_body["license"] = questionary.confirm("Include license?", default=True).ask()
            json_body["exclude_unknown"] = questionary.confirm("Exclude unknown licenses?", default=False).ask()
            json_body["operational_risk"] = questionary.confirm("Include operational risk?", default=True).ask()
            json_body["vulnerabilities"] = questionary.confirm("Include vulnerabilities (security)?", default=True).ask() 
            json_body["secrets"] = questionary.confirm("Include secrets?", default=True).ask()
            json_body["services"] = questionary.confirm("Include services?", default=True).ask()
            json_body["applications"] = questionary.confirm("Include applications?", default=True).ask()
            json_body["iac"] = questionary.confirm("Include IaC?", default=False).ask()

        # Mode 2: SPDX
        elif export_mode == "SPDX SBOM":
            console.print("[bold]SPDX Options:[/bold]")
            json_body["spdx"] = True
            json_body["spdx_format"] = questionary.select(
                "Select SPDX format:",
                choices=["json", "tag:value", "xlsx"],
                default="json"
            ).ask()

        # Mode 3: CycloneDX
        elif export_mode == "CycloneDX SBOM":
            console.print("[bold]CycloneDX Options:[/bold]")
            json_body["cyclonedx"] = True
            json_body["cyclonedx_format"] = questionary.select(
                "Select CycloneDX format:",
                choices=["json", "xml"],
                default="json"
            ).ask()
            json_body["vex"] = questionary.confirm("Include VEX?", default=False).ask()
        
    except KeyboardInterrupt:
        return None
    
    # Return the body using the special key
    return {"__json_body_from_file__": json_body}