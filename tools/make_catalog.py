#!/usr/bin/env python3
"""Compatibility entrypoint: one browser implementation, one authoritative manifest."""
from build_site import build
if __name__ == '__main__':
    print(f'Built {build()} icon entries in site/index.html (also works offline).')
