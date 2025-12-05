import sys
from pathlib import Path

# Ensure python project root is on sys.path so tests can import local modules.
# Correlates to "cd ../../"
ROOT = Path(__file__).resolve().parent.parent
# sys.path is the current module search path (incl. PYTHONPATH/CWD)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
