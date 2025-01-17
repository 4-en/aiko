import os

# Define environment file locations and the API keys they should store
CONFIG = {
    "aiko2/tests/.env": [
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        ],
}

GITIGNORE_FILE_PATH = os.path.join(os.path.dirname(__file__), ".gitignore")

def add_to_gitignore():
    """Ensures .env files are in .gitignore to prevent accidental commits."""
    if not os.path.exists(GITIGNORE_FILE_PATH):
        with open(GITIGNORE_FILE_PATH, "w") as f:
            f.write("\n".join(CONFIG.keys()) + "\n")
    else:
        with open(GITIGNORE_FILE_PATH, "r+") as f:
            lines = f.readlines()
            for env_file in CONFIG.keys():
                if f"{env_file}\n" not in lines:
                    f.write(f"\n{env_file}\n")
                    
def find_existing_key(key_name, env_files):
    for env_file in env_files:
        try:
            with open(env_file, "r") as f:
                for line in f:
                    if line.startswith(key_name):
                        return line.split("=")[1].strip()
        except Exception:
            continue
    return None

def create_env_files():
    """Prompts the user for API keys and creates .env files in multiple locations."""
    print("🔒 Setting up API keys securely...\n")

    different_key_names = set()
    for key_names in CONFIG.values():
        for key_name in key_names:
            different_key_names.add(key_name)

    keys = {key_name: find_existing_key(key_name, CONFIG.keys()) for key_name in different_key_names}

    # Prompt the user for API keys
    for key_name in different_key_names:
        
        key = keys[key_name]
        value = None
        if key:
            value = input(f"Enter new value for {key_name} (or press Enter to keep): ").strip()
            if not value:
                continue
        else:
            value = input(f"Enter value for {key_name}: ").strip()
            if not value:
                raise ValueError(f"Key {key_name} is missing.") 

        keys[key_name] = value

    # Create .env files
    for env_file, key_names in CONFIG.items():
        with open(env_file, "w") as f:
            for key_name in key_names:
                key = keys[key_name]
                if key is None:
                    raise ValueError(f"Key {key_name} is missing.")
                f.write(f"{key_name}={key}\n")

        print(f"✅ {env_file} has been created.")
       

    # Add .env files to .gitignore
    add_to_gitignore()
    print("\n✅ All .env files have been added to .gitignore to prevent accidental commits.")
    print("⚠️  Do NOT share these files!\n")

if __name__ == "__main__":
    create_env_files()

