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