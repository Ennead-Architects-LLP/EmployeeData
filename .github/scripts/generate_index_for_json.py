#!/usr/bin/env python3
"""
Compatibility shim. This script is deprecated.
It now delegates to merge_all_data_for_website.py which generates a merged employees.json.
"""

import runpy

if __name__ == "__main__":
    runpy.run_module(".merge_all_data_for_website", run_name="__main__", alter_sys=True, package=__package__)

