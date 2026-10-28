#!/usr/bin/env python3

"""
⚜️ Sentra ⚜️
------------
* © 2026 Ali Tourani (https://github.com/alitourani)
* SA-Engine is licensed under the GPL 3.0 License
* (Check LICENSE file for details)
"""

from sa_engine.config.yaml import load_config

if __name__ == "__main__":
    cfg = load_config()
    print(cfg)