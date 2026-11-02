#!/usr/bin/env python3

"""
⚜️ Sentra ⚜️
------------
* © 2026 Ali Tourani (https://github.com/alitourani)
* SA-Engine is licensed under the GPL 3.0 License
* (Check LICENSE file for details)
"""

from sa_engine.config.yaml import load_config


def main(args=None):
    """Main entry point for SA-Engine."""
    print("*** SA-Engine (Standalone) Started! ***\n")

    # Run the node
    try:
        # Load configuration
        print("- Loading configurations ...")
        cfg = load_config()
        print("- Configurations loaded successfully.\n")

    except (OSError, ValueError) as e:
        print(f"[ERROR] Error while running the code: {e}")


if __name__ == "__main__":
    main()
