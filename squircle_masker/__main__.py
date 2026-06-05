#!/usr/bin/env python3
"""
Entry point for running SquircleMasker as a module: python -m squircle_masker
Supports --cli flag for CLI mode, defaults to GUI.
"""
import sys


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        from .cli import run_cli
        run_cli()
    else:
        from .gui import run_gui
        run_gui()


if __name__ == "__main__":
    main()
