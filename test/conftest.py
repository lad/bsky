'''pytest init for python include path'''
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
