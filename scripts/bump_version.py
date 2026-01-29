import re
import os
import sys

def bump_version():
    version_file = "version.txt"
    if not os.path.exists(version_file):
        with open(version_file, "w") as f:
            f.write("20.02")
            
    with open(version_file, "r") as f:
        version_str = f.read().strip()
    
    # Increment version (e.g., 20.03 -> 20.04)
    # Support both X.Y and vX.Y formats
    clean_version = version_str.replace('v', '')
    parts = clean_version.split('.')
    if len(parts) == 2:
        major, minor = parts
        new_minor = int(minor) + 1
        new_version = f"{major}.{new_minor:02d}"
    else:
        # Fallback if format is strange
        new_version = clean_version + ".1"
        
    print(f"Bumping version: {version_str} -> {new_version}")

    # Update main.py
    main_py_path = "voter_api/main.py"
    if os.path.exists(main_py_path):
        with open(main_py_path, "r") as f:
            main_content = f.read()
        
        main_content = re.sub(r'MAIN_VERSION = "v[^"]+"', f'MAIN_VERSION = "v{new_version} (Auto-Bumped)"', main_content)
        main_content = re.sub(r'EXPECTED_FRONTEND_VERSION = "v[^"]+"', f'EXPECTED_FRONTEND_VERSION = "v{new_version}"', main_content)
        
        with open(main_py_path, "w") as f:
            f.write(main_content)
        print(f"Updated {main_py_path} to v{new_version}")

    # Update registration_screen.dart
    reg_screen_path = "ec_front_end/lib/screens/registration_screen.dart"
    if os.path.exists(reg_screen_path):
        with open(reg_screen_path, "r") as f:
            reg_content = f.read()
            
        reg_content = re.sub(r'EXPECTED_BACKEND_VERSION = "v[^"]+"', f'EXPECTED_BACKEND_VERSION = "v{new_version}"', reg_content)
        reg_content = re.sub(r'_appVersionDisplay = "v[^"]+"', f'_appVersionDisplay = "v{new_version}"', reg_content)
        
        with open(reg_screen_path, "w") as f:
            f.write(reg_content)
        print(f"Updated {reg_screen_path} to v{new_version}")

    # Save new version to file
    with open(version_file, "w") as f:
        f.write(new_version)
    print(f"Updated {version_file} to {new_version}")

if __name__ == "__main__":
    bump_version()
