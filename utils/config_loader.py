# utils/config_loader.py
import yaml
import os

def load_yaml(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)
