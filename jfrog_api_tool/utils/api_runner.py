# jfrog_api_tool/utils/api_runner.py

import json
import requests
import questionary
from requests.auth import HTTPBasicAuth
from rich.console import Console
from rich.pretty import pprint
from typing import Dict, Any

console = Console()

def _generate_curl_command(method, url, auth, headers, params, body_content, auth_mode="interactive"):
    """
    Helper function to generate a cURL command string.
    auth_mode options: 'interactive', 'masked', 'unsafe'
    """
    req = requests.Request(method, url, params=params)
    prepped = req.prepare()
    full_url = prepped.url

    command = ["curl"]
    command.append(f"-X {method}")
    
    # --- AUTHENTICATION LOGIC ---
    if auth_mode == "interactive":
        # Just the username. cURL will prompt for password.
        command.append(f"-u '{auth.username}'")
    elif auth_mode == "masked":
        # Placeholder for documentation/tickets
        command.append(f"-u '{auth.username}:<YOUR_TOKEN>'")
    else:
        # Unsafe - includes real credential
        command.append(f"-u '{auth.username}:{auth.password}'")
    # ----------------------------
    
    for k, v in headers.items():
        command.append(f"-H '{k}: {v}'")
    
    # Handle Body (JSON vs Text)
    if body_content:
        if isinstance(body_content, dict) or isinstance(body_content, list):
            body_str = json.dumps(body_content)
            command.append(f"-d '{body_str}'")
        else:
            # Raw String (AQL) - Clean newlines for copy-paste safety
            clean_body = str(body_content).replace('\n', ' ')
            command.append(f"-d '{clean_body}'")
    
    command.append(f"'{full_url}'")
    return " \\\n  ".join(command)

def execute_api_call(auth_details: Dict[str, str], 
                       api_config: Dict[str, Any], 
                       params: Dict[str, Any]):
    
    method = api_config["method"]
    url_template = api_config["url"]
    
    # 1. Build URL
    full_url = f"{auth_details['base_url']}{url_template}"
    path_params = api_config.get("path_params", [])
    for param_key in path_params:
        if param_key in params:
            full_url = full_url.replace(f"{{{param_key}}}", str(params[param_key]))

    # 1.5 Query Params
    query_data = {}
    query_param_keys = api_config.get("query_params", [])
    for key in query_param_keys:
        if key in params and params[key]:
            query_data[key] = params[key]

    # 2. Build Body (JSON or Text)
    body_content = None
    if "__json_body_from_file__" in params:
        body_content = params["__json_body_from_file__"]
    elif method in ["POST", "PUT", "PATCH"]:
        body_params_keys = api_config.get("body_params", [])
        body_data = {}
        for key in body_params_keys:
            if key in params:
                body_data[key] = params[key]
        if body_data:
            body_content = body_data

    # 3. Auth
    auth = HTTPBasicAuth(auth_details['username'], auth_details['token'])

    # 4. Headers & Content Type
    produces_type = api_config.get("produces", "application/json")
    req_content_type = api_config.get("content_type", "application/json")
    
    headers = {
        "Accept": produces_type
    }
    if body_content:
        headers["Content-Type"] = req_content_type

    # 5. Execute
    console.print(f"\n📡 [bold]Sending {method} request...[/bold]")
    console.print(f"[cyan]URL:[/cyan] {full_url}")
    
    if body_content:
        console.print(f"[cyan]Body ({req_content_type}):[/cyan]")
        if isinstance(body_content, (dict, list)):
            pprint(body_content)
        else:
            console.print(f"[dim]{body_content}[/dim]")
    
    try:
        # Prepare request arguments
        kwargs = {
            "method": method,
            "url": full_url,
            "auth": auth,
            "headers": headers,
            "params": query_data,
            "stream": True
        }

        # Choose 'json' or 'data' based on content type
        if body_content:
            if req_content_type == "application/json":
                kwargs["json"] = body_content
            else:
                kwargs["data"] = body_content 

        response = requests.request(**kwargs)
        
        # Handle response
        try:
            response.raise_for_status()
            console.print(f"\n✅ [bold green]Response (HTTP {response.status_code}):[/bold green]")
        except requests.exceptions.HTTPError:
            console.print(f"\n❌ [bold red]Response (HTTP {response.status_code}):[/bold red]")
        
        # Handle File vs JSON output
        content_type = response.headers.get("Content-Type", "")
        if "application/octet-stream" in content_type or "application/zip" in content_type:
            default_filename = "report.zip"
            cd = response.headers.get("Content-Disposition")
            if cd and "filename=" in cd:
                default_filename = cd.split("filename=")[1].strip("\"'")

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
            if response.status_code != 204 and response.content:
                try:
                    data = response.json()
                    pprint(data)
                except requests.exceptions.JSONDecodeError:
                    console.print(response.text)

    except Exception as e:
        console.print(f"\n❌ [bold red]Error:[/bold red] {e}")

    # 6. Generate CURL (Updated Menu)
    print()
    
    curl_choice = questionary.select(
        "Generate cURL command?",
        choices=[
            "No",
            "Yes (Interactive - prompts for password)", # <-- New Default
            "Yes (Safe - with <TOKEN> placeholder)",
            "Yes (Unsafe - with REAL credentials)"
        ]
    ).ask()
    
    if curl_choice and "Yes" in curl_choice:
        # Determine mode
        mode = "interactive"
        if "Safe" in curl_choice: mode = "masked"
        elif "Unsafe" in curl_choice: mode = "unsafe"
        
        curl_cmd = _generate_curl_command(method, full_url, auth, headers, query_data, body_content, auth_mode=mode)
        
        console.print("\n[bold yellow]📋 Copy-Pasteable cURL Command:[/bold yellow]")
        console.print("---------------------------------------------------")
        print(curl_cmd)
        console.print("---------------------------------------------------")
        
        if mode == "interactive":
            console.print("[green]ℹ️  Run this command, and cURL will ask for your password.[/green]")
        elif mode == "unsafe":
            console.print("[bold red]⚠️  WARNING: This command contains your actual token. Do NOT share it![/bold red]")