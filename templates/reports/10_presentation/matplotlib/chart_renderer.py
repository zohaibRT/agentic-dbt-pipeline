#!/usr/bin/env python3
"""Domain-neutral chart renderer abstraction for interactive and static exports.

Canonical implementation lives in scripts/lib_chart_renderer.py. This module is
copied into generated presentation folders and re-exports the same API.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Prefer the shared skill/scripts implementation when available.
_SCRIPTS = Path(__file__).resolve()
for parent in _SCRIPTS.parents:
    candidate = parent / "scripts" / "lib_chart_renderer.py"
    if candidate.exists():
        sys.path.insert(0, str(candidate.parent))
        break

try:
    from lib_chart_renderer import *  # noqa: F401,F403
    from lib_chart_renderer import (  # noqa: F401
        CHARTSPEC_FIELDS,
        DEFAULT_HOVER_FIELDS,
        DEFAULT_TOOLTIP_TEMPLATE,
        RENDER_MODE,
        VALID_CHART_TYPES,
        VALID_RENDER_MODES,
        build_chart_spec,
        build_tooltip_text,
        enrich_series_rows,
        ensure_offline_plotly_vendor,
        export_static_image,
        format_display_value,
        matplotlib_available,
        plotly_available,
        render_chart,
        render_interactive_chart,
    )
except ImportError:
    # Embedded fallback: load sibling copy written beside this file during fixture build.
    raise ImportError(
        "lib_chart_renderer is required. Copy scripts/lib_chart_renderer.py next to "
        "chart_renderer.py or ensure scripts/ is on PYTHONPATH."
    )
