from __future__ import annotations
import json, sys, time
from typing import Any, Dict

_index_prefix = "bot-logs"

def configure_json_logging(index_prefix: str):
    global _index_prefix
    _index_prefix = index_prefix

def log(event: str, **fields: Dict[str, Any]):
    rec = {
        "ts": time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()),
        "event": event,
        "index": _index_prefix,
    }
    rec.update(fields)
    sys.stdout.write(json.dumps(rec) + "\n")
    sys.stdout.flush()

def get_json_logger():
    return log
