# utils/api_runner.py

import requests
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

    # --- 1.5. Build Query Params --- (NEW LOGIC)
    query_data = {}
    query_param_keys = api_config.get("query_params", [])
    for key in query_param_keys:
        if key in params and params[key]: # Only add if it exists and is not empty
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
    
    headers = {
        "Accept": "application/json"
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
            params=query_data # NEW: Pass the query params to requests
        )
        
        response.raise_for_status() 
        
        console.print(f"\n✅ [bold green]Response (HTTP {response.status_code}):[/bold green]")
        
        if response.status_code == 204 or not response.content:
            console.print("[italic]Request successful (No Content 204).[/italic]")
            return
        
        try:
            data = response.json()
            pprint(data)
        except requests.exceptions.JSONDecodeError:
            console.print(response.text)

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