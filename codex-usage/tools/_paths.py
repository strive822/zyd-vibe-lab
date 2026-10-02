"""Project paths and source imports for tools launched from any directory."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
EVIDENCE = ROOT / "docs" / "evidence"
sys.path.insert(0, str(SOURCE))
