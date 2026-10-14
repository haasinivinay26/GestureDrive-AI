"""
Launcher proxy for GestureDriveAI directory structure.
Ensures seamless launching whether invoked from root or GestureDriveAI subdirectory.
"""

import os
import sys

# Ensure parent directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main import main

if __name__ == "__main__":
    main()
