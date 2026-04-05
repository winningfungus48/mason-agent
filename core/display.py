"""
core/display.py
---------------
DISPLAY_RAW wrapper utility.
All tools that show data to Mason call wrap_display().
The agent loop intercepts the tag and sends content directly to Telegram,
bypassing Claude's response entirely.

To use in any agent:
    from core.display import wrap_display
    return wrap_display(content)
"""


def wrap_display(content: str) -> str:
    """Wrap content so the agent loop sends it verbatim to Telegram."""
    return f"[DISPLAY_RAW]\n{content.strip()}\n[/DISPLAY_RAW]"
