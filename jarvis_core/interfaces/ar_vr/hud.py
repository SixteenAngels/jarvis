from __future__ import annotations

"""AR HUD overlay hooks.

This module exposes a `render_overlay` function that, in production, should
draw detection bounding boxes and labels onto frames for AR display. Here we
keep a simple stub return to avoid graphical requirements.
"""

from typing import Any, Dict


def render_overlay(data: Dict[str, Any]) -> bool:
    # TODO: integrate with OpenGL/AR toolkit; accept frame buffer, draw overlay
    return True
