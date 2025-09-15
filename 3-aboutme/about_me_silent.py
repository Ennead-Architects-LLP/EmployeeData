#!/usr/bin/env python3
import os
import sys

# Ensure silent mode for AboutMe
os.environ["ABOUTME_FORCE_SILENT"] = "1"

# Delegate to main app
from about_me import main

if __name__ == "__main__":
    sys.exit(main())


