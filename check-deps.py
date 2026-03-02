#!/usr/bin/env python3
"""
Quick dependency checker for Dual Core Coder.
Verifies all required modules are installed and accessible.
"""

import sys
from pathlib import Path

def check_python_version():
    """Verify Python version is 3.8+"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor} (FAIL - need 3.8+)")
        return False

def check_module(module_name, description=""):
    """Check if a module is available"""
    try:
        mod = __import__(module_name)
        version_str = ""
        if hasattr(mod, "__version__"):
            version_str = f" v{mod.__version__}"
        elif hasattr(mod, "VERSION"):
            version_str = f" v{mod.VERSION}"
        elif hasattr(mod, "TkVersion") and module_name == "tkinter":
            version_str = f" v{mod.TkVersion}"
        print(f"✓ {module_name}{version_str} ({description})")
        return True
    except ImportError as e:
        print(f"✗ {module_name} (FAIL - {description})")
        print(f"  Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Dual Core Coder — Dependency Check")
    print("=" * 60)
    print()

    results = []

    # Python version
    print("Python Version:")
    results.append(check_python_version())
    print()

    # Standard library modules (should always be present)
    print("Standard Library Modules:")
    results.append(check_module("tkinter", "GUI framework (built-in)"))
    results.append(check_module("threading", "Threading (built-in)"))
    results.append(check_module("json", "JSON parsing (built-in)"))
    results.append(check_module("time", "Timing (built-in)"))
    results.append(check_module("math", "Math utilities (built-in)"))
    results.append(check_module("os", "OS utilities (built-in)"))
    print()

    # External dependencies
    print("External Dependencies (PyPI):")
    results.append(check_module("requests", "HTTP client"))
    print()

    # Summary
    print("=" * 60)
    if all(results):
        print("✓ All dependencies OK — Ready to run!")
        return 0
    else:
        failed = sum(1 for r in results if not r)
        print(f"✗ {failed} dependency issue(s) found — See DEPENDENCIES.md for help")
        return 1

if __name__ == "__main__":
    sys.exit(main())
