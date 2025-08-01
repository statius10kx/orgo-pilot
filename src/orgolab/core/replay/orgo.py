from pathlib import Path

ORGO_TEMPLATE = '''\
from orgo import Computer
import os, json, time

pc = Computer(project_id=os.getenv("ORGO_PROJECT_ID"), api_key=os.getenv("ORGO_API_KEY"))
with open("{LOG}", "r") as f:
    steps = json.load(f)["actions"]

for step in steps:
    name = step["name"]
    args = step.get("args", {})
    getattr(pc, name)(**args)
'''

def generate_orgo_script(run_dir: Path, log_file: str) -> str:
    path = run_dir / "orgo_replay.py"
    path.write_text(ORGO_TEMPLATE.replace("{LOG}", log_file))
    return path.name
