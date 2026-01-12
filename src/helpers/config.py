import tomllib
from pathlib import Path


def load_config():
    # Locate the pyproject.toml relative to this script
    path = Path(__file__).parent.parent.parent / "pyproject.toml"

    with open(path, "rb") as f:
        data = tomllib.load(f)

    # Access your specific tool section
    config = data.get("tool", {}).get("scraper", {})
    return config


# Usage
app_config = load_config()
print(f"MAX_PAGES: {app_config.get('MAX_PAGES')}")
