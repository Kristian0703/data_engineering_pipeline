import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def write_changelog(version, new_rows, schema_changes=None):
    """Append update details to changelog file."""
    with open("changelog.txt", "a", encoding="utf-8") as f:
        f.write(
            f"[{datetime.now()}] Version: {version} | "
            f"New rows: {new_rows} | "
            f"Schema Changes: {schema_changes or 'None'}\n"
        )

def get_next_version():
    """Read changelog and return next version number."""
    try:
        with open("changelog.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return "v1.0"
            last_version = lines[-1].split("|")[0].split(":")[-1].strip()
            major, minor = map(int, last_version.strip("v").split("."))
            return f"v{major}.{minor+1}"
    except FileNotFoundError:
        return "v1.0"
