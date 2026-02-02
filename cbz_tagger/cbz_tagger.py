"""Reflex app entry point.

This module provides the expected entry point for Reflex CLI.
It imports and exposes the app from the reflex_gui module.
"""

from cbz_tagger.reflex_gui.reflex_app import app

__all__ = ["app"]
