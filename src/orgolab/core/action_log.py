from pathlib import Path
from typing import Any, Dict, List


def write_log(actions: List[Dict[str, Any]], dest: Path) -> None:
    import datetime
    import json
    data = { "generated_at": datetime.datetime.utcnow().isoformat() + "Z", "actions": actions }
    dest.write_text(json.dumps(data, indent=2))
