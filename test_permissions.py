import sys
from pathlib import Path

print("--- 🚀 STARTING PERMISSION TEST ---")

# נשתמש בשם תיקייה חדש לבדיקה
CONFIG_DIR = Path.home() / ".config" / "jfrog-api-tool-TEST"
CONFIG_FILE = CONFIG_DIR / "config.ini"

print(f"Attempting to create directory: {CONFIG_DIR}")

try:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    print("✅ SUCCESS: Directory created or already exists.")
except Exception as e:
    print(f"❌ FAILED to create directory.")
    print(f"Error details: {e}")
    sys.exit(1) # Stop here if dir creation fails

print(f"Attempting to create file: {CONFIG_FILE}")
try:
    CONFIG_FILE.touch()
    print("✅ SUCCESS: File 'config.ini' created or already exists.")
except Exception as e:
    print(f"❌ FAILED to create file.")
    print(f"Error details: {e}")
    sys.exit(1)

print("--- 🏁 TEST COMPLETE ---")
print("Please check for the directory '~/.config/jfrog-api-tool-TEST'")