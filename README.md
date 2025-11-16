# JFrog Support API CLI Tool (jfat)

`jfat` is an interactive Command Line Interface (CLI) tool for JFrog Support Engineers to quickly run and test Artifactory and Xray REST APIs.

It securely manages credentials for multiple JFrog instances and provides interactive wizards for complex API calls.

## ✨ Features

* **Interactive Menus:** Uses `questionary` to provide easy-to-navigate menus for all API calls.
* **Credential Management:** Securely stores and manages connection profiles (URL, User, Token) for multiple JFrog instances. No more typing credentials!
* **Complex API Wizards:** Provides guided "wizards" for complex, multi-step API calls (like creating Xray Policies).
* **Debug Mode:** Run with `jfat --debug` or `JFAT_DEBUG=true jfat` to see verbose logs.

## 📦 Installation (for macOS/Linux)

This tool is designed to run locally from a cloned repository using a dedicated virtual environment.

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/jfrog-api-tool.git](https://github.com/YOUR_USERNAME/jfrog-api-tool.git)
    cd jfrog-api-tool
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python3 -m venv venv
    ```

3.  **Activate the Environment & Install Dependencies:**
    ```bash
    source venv/bin/activate
    pip install -r requirements.txt
    ```
    *(Note: Deactivate the environment with `deactivate` when finished)*

4.  **Make the Launcher Script Executable:**
    ```bash
    chmod +x jfat
    ```

5.  **Create a Global Symlink (Optional but Recommended):**
    This allows you to run `jfat` from anywhere on your system.
    *(This example uses `homebrew`'s bin path, adjust if yours is different.)*
    ```bash
    ln -s "$(pwd)/jfat" /opt/homebrew/bin/jfat
    ```

## 🚀 Usage

Once installed and symlinked, you can run the tool from any directory.

```bash
# Run the tool
jfat

# Run in debug mode
jfat --debug

# Get help
jfat --help

🛠️ How to Add New APIs (Contributing)
Adding new APIs is the main way to contribute. There are two ways to add an API, depending on its complexity.

All API definitions are stored in: jfrog_api_tool/apis.json

Type 1: Simple Endpoints (The Easy Way)
This is for simple APIs (like GET requests or POST requests with simple key-value bodies) that do not require a complex, nested JSON body.

Example: Adding "Get Storage Info" to Artifactory.

Open jfrog_api_tool/apis.json.

Find the "Artifactory" section.

Add the new API block:



"Artifactory": {
  "Get Repositories": { ... },
  "Get Build Info": { ... },
  "System Ping": { ... },

  "Get Storage Info": {
    "method": "GET",
    "url": "/artifactory/api/storageinfo",
    "path_params": [],
    "body_params": []
  }
},
Save the file. You're done. The tool will automatically add "Get Storage Info" to the menu.

Type 2: Complex Endpoints (The Wizard Way)
This is for complex APIs that require nested JSON, arrays, or interactive logic (like Create Policy).

This is a two-step process:

Step 1: Add the API to apis.json
Add the API, but instead of body_params, use "body_input_mode": "wizard" and give your new wizard a unique wizard_name.



"Xray": {
    "Create Policy": { ... },
    "Force Reindex": { ... },

    "My New Complex API": {
      "method": "POST",
      "url": "/xray/api/v1/my-new-api",
      "path_params": [],
      "body_input_mode": "wizard",
      "wizard_name": "my_new_wizard"
    }
}
Step 2: Create the Wizard in main.py
Open jfrog_api_tool/main.py.

Create a new helper function for your wizard (e.g., _run_my_new_wizard()). This function should use questionary to ask the user for input and return a dictionary for the JSON body.

Python

# Add this function somewhere near the other wizards
def _run_my_new_wizard() -> Dict[str, Any]:
    console.print("\n[bold]Starting 'My New Wizard'...[/bold]")

    # Ask questions...
    param1 = questionary.text("Enter param1:").ask()
    param2_name = questionary.text("Enter param2 name:").ask()

    # Build the complex body
    json_body = {
        "some_key": param1,
        "nested_object": {
            "name": param2_name
        }
    }

    # Return the body using the special key
    return {"__json_body_from_file__": json_body}
Find the get_user_params() function in main.py.

Add an elif statement to hook your new wizard to the wizard_name you defined in apis.json.

Python

# Inside get_user_params()
...
if body_input_mode == "wizard":
    wizard_params = None

    if wizard_name == "force_reindex":
        wizard_params = _run_force_reindex_wizard()
    elif wizard_name == "create_policy_v2":
        wizard_params = _run_create_policy_wizard()

    # --- ADD THIS BLOCK ---
    elif wizard_name == "my_new_wizard":
        wizard_params = _run_my_new_wizard()
    # ---------------------

    else:
        console.print(f"[red]Error: Unknown wizard_name '{wizard_name}'[/red]")
        return None
...