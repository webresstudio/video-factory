#!/usr/bin/env python3
"""Skill entrypoint forwarding to video-factory/kit/tools/audit_music_track.py."""
import os
import sys

TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "kit", "tools"))
sys.path.insert(0, TOOLS_DIR)
import audit_music_track  # noqa: E402

if __name__ == "__main__":
    sys.exit(audit_music_track.main())
