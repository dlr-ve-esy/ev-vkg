import sys
from pathlib import Path

# Make the repository root importable (error_metrics, fair_scoring,
# run_config, canonical_values live there).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
