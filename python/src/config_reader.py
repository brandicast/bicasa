import configparser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

config = configparser.ConfigParser()

config_path = BASE_DIR / "conf" / "config.ini"
try:
    config.read(str(config_path), encoding='utf-8')
    print(f"reading config from {config_path}")
except:
    print(f"Reading {config_path} error")
