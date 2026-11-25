#!/usr/bin/env python3
"""Entry program for the make.fun bounty "news-image-20261125".

Writes the bundled front-page image to /output/entry.png.

The image (entry.png, kept next to this file) is a single-page newspaper
that sums up the world news of Wednesday, 25 November 2026: 37 stories
as reported that day, a world map of the day's story locations, a
west-to-east timeline with local times, a drawn scene of the Strait of
Hormuz at dawn, a markets ticker and a sport brief.

The program only copies that bundled file, so it needs no network and
every run writes exactly the same bytes.

Run with Python 3.13:  python3 main.py
"""

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "entry.png"
OUTPUT = Path("/output/entry.png")


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, OUTPUT)


if __name__ == "__main__":
    main()
