import os
import sys

def get_storage_location(app_name: str = "aiko2", create: bool = True) -> str:
    """
    Get storage location for configs, logs, and other files.
    Depending on the platform, the location may vary.
    
    
    Linux/Unix: ~/.local/share/<app_name>
    macOS: ~/Library/Application Support/<app_name>
    Windows: %APPDATA%\<app_name>
    
    Parameters
    ----------
    app_name : str, optional
        The name of the application. The default is "aiko2".
    create : bool, optional
        Whether to create the directory if it does not exist. The default is True.
    """
    
    if sys.platform == "win32":
        base_dir = os.getenv("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
    elif sys.platform == "darwin":
        base_dir = os.path.expanduser("~/Library/Application Support")
    else:  # Assume Linux or other Unix-like OS
        base_dir = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))

    app_data_dir = os.path.join(base_dir, app_name)

    # Ensure the directory exists
    if create:
        os.makedirs(app_data_dir, exist_ok=True)

    return app_data_dir