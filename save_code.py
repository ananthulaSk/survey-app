import os
import datetime
import subprocess

def run_command(command):
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError:
        print(f"Error executing: {command}")
        exit(1)

def save_snapshot():
    # 1. Get the Title from you
    print("--- 🚀 SURVEY APP GIT SAVER ---")
    raw_title = input("Enter a short title for this change (e.g., 'fixed submit button'): ").strip()
    
    if not raw_title:
        print("Title cannot be empty.")
        return

    # 2. Generate Date and Time String
    # Format: YYYY-MM-DD_HH-MM
    now = datetime.datetime.now()
    time_str = now.strftime("%Y-%m-%d_%H-%M")
    
    # 3. Format the Branch Name (Replace spaces with underscores)
    safe_title = raw_title.replace(" ", "_").replace("'", "").lower()
    branch_name = f"{time_str}_{safe_title}"
    
    print(f"\nCreating and switching to branch: {branch_name}...")

    # 4. Execute Git Commands
    # Create new branch
    run_command(f"git checkout -b {branch_name}")
    
    # Add all changes
    run_command("git add .")
    
    # Commit
    run_command(f'git commit -m "{raw_title} - {time_str}"')
    
    # Push to GitHub
    print(f"Pushing {branch_name} to GitHub...")
    run_command(f"git push -u origin {branch_name}")
    
    print("\n✅ SUCCESS! Code saved and pushed safely.")
    print(f"🔗 Branch: {branch_name}")

if __name__ == "__main__":
    save_snapshot()
