from pathlib import Path


def _to_sandbox_call(act: dict) -> str | None:
    name = act["name"]
    args = act.get("args", {})

    if name == "left_click":
        sel = args.get("selector")
        coords = args.get("coordinates") or {}
        if sel:
            return f'computer.left_click(selector="{sel}")'
        if "x" in coords and "y" in coords:
            return f'computer.left_click({coords["x"]}, {coords["y"]})'

    if name == "type":
        text = args.get("text")
        sel = args.get("selector")
        if text is not None:
            if sel:
                return f'computer.type("{text}", selector="{sel}")'
            return f'computer.type("{text}")'

    if name == "scroll":
        amt = args.get("amount")
        if amt is not None:
            return f"computer.scroll({amt})"

    if name in ("double_click", "right_click", "mouse_click"):
        sel = args.get("selector")
        coords = args.get("coordinates") or {}
        fn = name  # matches computer.double_click etc.
        if sel:
            return f'computer.{fn}(selector="{sel}")'
        if coords:
            return f'computer.{fn}({coords["x"]}, {coords["y"]})'

    if name in ("key", "key_press", "hotkey"):
        k = args.get("keys")
        if not k:
            return None          # silently skip empty key events
        return f'computer.key("{k}")'

    if name == "wait":
        return f'computer.wait({args.get("seconds", 1)})'

    return None

def generate_sandbox_snippet(run_dir: Path, actions) -> str:
    lines = [
        "# pip install orgo",
        "from orgo import Computer",
        "",
        "# Perform the recorded actions",
        'computer = Computer(project_id="<your_project_id>", api_key="<your_api_key>")',
        ""
    ]
    for act in actions:
        call = _to_sandbox_call(act)
        if call:
            lines.append(call)
    lines.append("")
    path = run_dir / "sandbox_snippet.py"
    path.write_text("\n".join(lines))
    return path.name
