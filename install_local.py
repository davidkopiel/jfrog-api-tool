import os
import shutil
from pathlib import Path

# 1. הגדרות
HOME = Path.home()
PLUGIN_NAME = "jfat"
# חזרנו לשם המקורי - זה מה שה-CLI דורש
BINARY_NAME = "jfat" 

PLUGIN_DIR = HOME / ".jfrog" / "plugins" / PLUGIN_NAME
BIN_DIR = PLUGIN_DIR / "bin"
YAML_FILE = PLUGIN_DIR / "plugin.yaml"
DIST_FILE = Path("dist") / "jfat"  # הקובץ ש-pyinstaller יצר

# תוכן ה-YAML הנקי (חשוב מאוד!)
YAML_CONTENT = f"""version: "1.0.0"
name: {PLUGIN_NAME}
description: JFrog Support API Tool
maintainer: David
usage: jf {PLUGIN_NAME}
commands:
  - name: run
    alias: r
    description: Start Wizard
    executable: {BINARY_NAME}
    arguments: []
    flags: []
"""

def install():
    print(f"🚀 Installing {PLUGIN_NAME} plugin...")

    # 2. ניקוי התקנות קודמות
    if PLUGIN_DIR.exists():
        print(f"   - Removing old installation at {PLUGIN_DIR}")
        shutil.rmtree(PLUGIN_DIR)

    # 3. יצירת תיקיות
    print(f"   - Creating directory structure: {BIN_DIR}")
    BIN_DIR.mkdir(parents=True, exist_ok=True)

    # 4. העתקת הבינארי
    if not DIST_FILE.exists():
        print(f"❌ Error: Compiled file '{DIST_FILE}' not found. Did you run pyinstaller?")
        return
    
    dest_bin = BIN_DIR / BINARY_NAME
    print(f"   - Copying binary to {dest_bin}")
    shutil.copy(DIST_FILE, dest_bin)
    
    # 5. מתן הרשאות ריצה
    print("   - Setting executable permissions")
    os.chmod(dest_bin, 0o755)

    # 6. כתיבת קובץ ה-YAML
    print(f"   - Writing clean plugin.yaml")
    with open(YAML_FILE, "w", encoding="utf-8") as f:
        f.write(YAML_CONTENT)

    print("\n✅ Installation Complete!")
    print("👉 Run 'jf plugin list' to verify.")
    print(f"👉 Run 'jf {PLUGIN_NAME}' to start.")

if __name__ == "__main__":
    install()
