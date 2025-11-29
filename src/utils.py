# src/utils.py
import json
import os
from datetime import datetime
import logging
from typing import Any, Dict

DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def load_yaml(path: str):
    import yaml
    with open(path, "r") as f:
        return yaml.safe_load(f)


def dump_json(obj: Any, path: str, indent: int = 2):
    with open(path, "w") as f:
        json.dump(obj, f, indent=indent, default=str)


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
    return path


def timestamped_filename(prefix: str, ext: str = ".json"):
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{ts}{ext}"


def setup_logger(name: str = "automated_qpcr", level: int = logging.INFO, logfile: str = None):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured
    logger.setLevel(level)
    fmt = logging.Formatter(DEFAULT_LOG_FORMAT)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    if logfile:
        fh = logging.FileHandler(logfile)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger
