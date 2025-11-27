import os

print("--- 🕵️‍♂️ JFrog CLI Environment Spy ---")
# מדפיס כל משתנה סביבה שמתחיל ב-JFROG_CLI
for key, value in os.environ.items():
    if key.startswith("JFROG_CLI"):
        print(f"{key} = {value}")
print("------------------------------------")