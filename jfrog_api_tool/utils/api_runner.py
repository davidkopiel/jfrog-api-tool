# jfrog_api_tool/utils/api_runner.py

import json
import requests
import questionary
from requests.auth import HTTPBasicAuth
from rich.console import Console
from rich.pretty import pprint
from typing import Dict, Any

console = Console()

def _generate_curl_command(method, url, auth, headers, params, json_body):
    """
    Helper function to generate a cURL command string from request details.
    """
    # 1. Prepare the full URL with query parameters
    req = requests.Request(method, url, params=params)
    prepped = req.prepare()
    full_url = prepped.url

    # 2. Start building the command
    # We use backslashes (\) to make the command readable in the terminal
    command = ["curl"]
    
    # 3. Add Method
    command.append(f"-X {method}")
    
    # 4. Add Auth (Masked for security display, but user can replace it)
    # We use the actual token so it's runnable, but be careful sharing screens!
    command.append(f"-u '{auth.username}:{auth.password}'")
    
    # 5. Add Headers
    for k, v in headers.items():
        command.append(f"-H '{k}: {v}'")
    
    # 6. Add Body
    if json_body:
        # We dump to string and escape single quotes for shell safety
        body_str = json.dumps(json_body)
        command.append(f"-d '{body_str}'")
    
    # 7. Add URL (always last)
    command.append(f"'{full_url}'")

    return " \\\n  ".join(command)

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

    # --- 4. Prepare Headers & Metadata ---
    produces_type = api_config.get("produces", "application/json")
    
    headers = {
        "Accept": produces_type
    }
    if json_body:
        headers["Content-Type"] = "application/json"

    # --- 5. Execute the Call ---
    console.print(f"\n📡 [bold]Sending {method} request...[/bold]")
    console.print(f"[cyan]URL:[/cyan] {full_url}")
    
    if query_data:
        console.print(f"[cyan]Query Params:[/cyan]")
        pprint(query_data)
    if json_body:
        console.print(f"[cyan]Body:[/cyan]")
        pprint(json_body)
    
    try:
        response = requests.request(
            method=method,
            url=full_url,
            auth=auth,
            json=json_body,
            headers=headers,
            params=query_data,
            stream=True
        )
        
        # Check for HTTP errors
        try:
            response.raise_for_status()
            console.print(f"\n✅ [bold green]Response (HTTP {response.status_code}):[/bold green]")
        except requests.exceptions.HTTPError:
            console.print(f"\n❌ [bold red]Response (HTTP {response.status_code}):[/bold red]")
        
        # --- Handle File Download vs JSON ---
        content_type = response.headers.get("Content-Type", "")
        if "application/octet-stream" in content_type or "application/zip" in content_type:
            # File Logic
            default_filename = "report.zip"
            cd = response.headers.get("Content-Disposition")
            if cd:
                parts = cd.split("filename=")
                if len(parts) > 1:
                    default_filename = parts[1].strip("\"'")

            console.print(f"[bold blue]File detected! (Content-Type: {content_type})[/bold blue]")
            save_path = questionary.text("Enter path to save file:", default=default_filename).ask()

            if save_path:
                try:
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    console.print(f"[green]✅ File saved to: [bold]{save_path}[/bold][/green]")
                except Exception as e:
                    console.print(f"[bold red]Error saving file: {e}[/bold red]")
        else:
            # JSON/Text Logic
            if response.status_code != 204 and response.content:
                try:
                    data = response.json()
                    pprint(data)
                except requests.exceptions.JSONDecodeError:
                    console.print(response.text)

    except requests.exceptions.ConnectionError as e:
        console.print(f"\n❌ [bold red]Connection Error:[/bold red]")
        console.print(f"[italic]{e}[/italic]")
    except Exception as e:
        console.print(f"\n❌ [bold red]Unexpected Error:[/bold red]")
        console.print(f"[italic]{e}[/italic]")

    # --- 6. OPTIONAL: Generate CURL Command ---
    # We ask this at the very end, regardless of success or failure
    print() # Empty line
    show_curl = questionary.confirm("Would you like to generate the full cURL command (for sharing)?").ask()
    
    if show_curl:
        curl_cmd = _generate_curl_command(method, full_url, auth, headers, query_data, json_body)
        
        console.print("\n[bold yellow]📋 Copy-Pasteable cURL Command:[/bold yellow]")
        console.print("---------------------------------------------------")
        print(curl_cmd)
        console.print("---------------------------------------------------")
        console.print("[dim]Note: This command includes your API token. Be careful sharing it![/dim]")