# jfrog_api_tool/utils/api_runner.py

import requests
import questionary # <-- Added for the download prompt
from requests.auth import HTTPBasicAuth
from rich.console import Console
from rich.pretty import pprint
from typing import Dict, Any

console = Console()

def execute_api_call(auth_details: Dict[str, str], 
                       api_config: Dict[str, Any], 
                       params: Dict[str, Any]):
    """
    Executes a single API call based on the provided config and parameters.
    """
    
    method = api_config["method"]
    url_template = api_config["url"]
    
    # --- 1. Build the Full URL ---
    full_url = f"{auth_details['base_url']}{url_template}"
    path_params = api_config.get("path_params", [])
    
    for param_key in path_params:
        if param_key in params:
            full_url = full_url.replace(f"{{{param_key}}}", str(params[param_key]))

    # --- 1.5. Build Query Params ---
    query_data = {}
    query_param_keys = api_config.get("query_params", [])
    for key in query_param_keys:
        if key in params and params[key]:
            query_data[key] = params[key]

    # --- 2. Build the JSON Body ---
    json_body = None
    
    if "__json_body_from_file__" in params:
        json_body = params["__json_body_from_file__"]
    elif method in ["POST", "PUT", "PATCH"]:
        body_params_keys = api_config.get("body_params", [])
        body_data = {}
        for key in body_params_keys:
            if key in params:
                body_data[key] = params[key]
        
        if body_data:
            json_body = body_data

    # --- 3. Prepare Authentication ---
    auth = HTTPBasicAuth(auth_details['username'], auth_details['token'])

    # --- 4. Execute the Call & Handle Response ---
    console.print(f"\n📡 [bold]Sending {method} request...[/bold]")
    console.print(f"[cyan]URL:[/cyan] {full_url}")
    if query_data:
        console.print(f"[cyan]Query Params:[/cyan]")
        pprint(query_data)
    if json_body:
        console.print(f"[cyan]Body:[/cyan]")
        pprint(json_body)
    
    # --- NEW: Handle `produces` key from apis.json ---
    produces_type = api_config.get("produces", "application/json")
    
    headers = {
        "Accept": produces_type
    }
    if json_body:
        headers["Content-Type"] = "application/json"

    try:
        response = requests.request(
            method=method,
            url=full_url,
            auth=auth,
            json=json_body,
            headers=headers,
            params=query_data,
            stream=True # Enable streaming for file downloads
        )
        
        response.raise_for_status() 
        
        console.print(f"\n✅ [bold green]Response (HTTP {response.status_code}):[/bold green]")
        
        # --- NEW: File Download Logic ---
        content_type = response.headers.get("Content-Type", "")
        if "application/octet-stream" in content_type or "application/zip" in content_type:
            
            # Try to get filename from headers
            default_filename = "report.zip"
            cd = response.headers.get("Content-Disposition")
            if cd:
                parts = cd.split("filename=")
                if len(parts) > 1:
                    default_filename = parts[1].strip("\"'")

            console.print(f"[bold blue]File detected! (Content-Type: {content_type})[/bold blue]")
            
            save_path = questionary.text(
                "Enter path to save file:",
                default=default_filename
            ).ask()

            if not save_path:
                console.print("[yellow]File download cancelled.[/yellow]")
                return

            try:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                console.print(f"[green]✅ File saved successfully to: [bold]{save_path}[/bold][/green]")
            except Exception as e:
                console.print(f"[bold red]Error saving file: {e}[/bold red]")

        # --- Original JSON Logic ---
        else:
            if response.status_code == 204 or not response.content:
                console.print("[italic]Request successful (No Content 204).[/italic]")
                return
            
            try:
                data = response.json()
                pprint(data)
            except requests.exceptions.JSONDecodeError:
                console.print(response.text) # Fallback to text

    # --- Error Handling (Unchanged) ---
    except requests.exceptions.HTTPError as e:
        console.print(f"\n❌ [bold red]HTTP Error ({e.response.status_code}):[/bold red]")
        try:
            error_data = e.response.json()
            pprint(error_data)
        except:
            console.print(e.response.text)
            
    except requests.exceptions.ConnectionError as e:
        console.print(f"\n❌ [bold red]Connection Error:[/bold red]")
        console.print(f"Could not connect to {auth_details['base_url']}")
        console.print(f"[italic]{e}[/italic]")

    except Exception as e:
        console.print(f"\n❌ [bold red]An unexpected error occurred:[/bold red]")
        console.print(f"[italic]{e}[/italic]")