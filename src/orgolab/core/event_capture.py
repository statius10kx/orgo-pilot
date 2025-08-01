"""Translate raw Orgo tool-result payloads into a strict action schema."""

from __future__ import annotations

from typing import Any

# Every supported Orgo UI command → the arg keys we want to persist
ACTION_MAP: dict[str, list[str]] = {
    # Mouse verbs
    "left_click":    ["selector", "coordinates"],
    "double_click":  ["selector", "coordinates"],
    "right_click":   ["selector", "coordinates"],
    "mouse_click":   ["selector", "coordinates"],   # alt spelling in some builds

    # Keyboard verbs  ───────────────────────────────────────────
    "type":          ["selector", "text"],
    "key":           ["keys", "key"],   # Orgo may send either field
    "key_press":     ["keys", "key"],
    "hotkey":        ["keys", "key"],
    "key_down":      ["keys", "key"],   # seen in some SDK builds

    # Misc-control verbs
    "scroll":        ["amount"],
    "wait":          ["seconds"],   # pause / sleep
    "screenshot":    [],            # explicit frame grab
    
    # High-level verbs (markers)
    "submit_form":   [],            # form submission marker
    "navigate":      [],            # navigation marker
}

# Accept both Orgo callback style ("action") and internal style ("name")
def _get_action_name(tool_result: dict[str, Any]) -> str | None:
    return tool_result.get("name") or tool_result.get("action")

def extract_actions(tool_result: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Convert a single Orgo tool_result object into zero-or-more actions
    that conform to ACTION_MAP.  Unknown commands are ignored.
    """
    actions: list[dict[str, Any]] = []
    name = _get_action_name(tool_result)
    if name in ACTION_MAP:
        payload = {k: tool_result.get(k) for k in ACTION_MAP[name] if tool_result.get(k) is not None}
        
        # Normalise alias ─ promote {"key": "enter"} → {"keys": "enter"}
        if name in ("key", "key_press", "hotkey", "key_down"):
            if payload.get("key") and not payload.get("keys"):
                payload["keys"] = payload.pop("key")
        
        # Normalise flat x/y into nested coordinates expected by replay
        if "x" in tool_result and "y" in tool_result and "coordinates" not in payload:
            payload["coordinates"] = {"x": tool_result["x"], "y": tool_result["y"]}
        
        # Drop useless key events that carry no key name
        if name in ("key", "key_press", "hotkey", "key_down") and not payload.get("keys"):
            return []
        
        # ❶ Promote trailing newline to an explicit Enter key-press
        if name == "type":
            txt = payload.get("text", "")
            if txt.endswith(("\n", "\r", "\r\n")):
                # strip the newline(s) so the typed text stays clean
                payload["text"] = txt.rstrip("\r\n")
        
        actions.append({"name": name, "args": payload, "ts": tool_result.get("timestamp")})
        
        # If we stripped a newline from type, add Enter key after it
        if name == "type":
            txt = tool_result.get("text", "")
            if txt.endswith(("\n", "\r", "\r\n")):
                actions.append({
                    "name": "key",
                    "args": {"keys": "Enter"},
                    "ts": tool_result.get("timestamp"),
                })
    
    # Fallback: treat any unrecognised verb with raw x/y as a generic click
    if not actions and {"x", "y"} <= tool_result.keys():
        actions.append({
            "name": "left_click",
            "args": {"coordinates": {"x": tool_result["x"], "y": tool_result["y"]}},
            "ts": tool_result.get("timestamp"),
        })
    
    return actions