# Description: Pytest shared configuration for import path setup and common fixtures.
# This file is part of the SprintStudy project.

"""Pytest shared configuration for repository-local imports."""

from __future__ import annotations

import sys
from pathlib import Path


# Ensure tests can import `backend` package when running from repo root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

