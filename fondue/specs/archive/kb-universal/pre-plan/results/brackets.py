#!/usr/bin/env python3
"""Research prototype check: kb-universal pre-plan. Not a design.

  brackets.py <root>    every file of a directory module whose skel.py skeleton ends with a bracket open

A kept line that opens a bracket keeps its continuation lines until the bracket closes, so a skeleton
that ends with a bracket open has lost the rest of some declaration. Prints each such file with the
kept line that opened the bracket, then a count.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import layout  # noqa: E402
import skel  # noqa: E402
import kb  # noqa: E402


def main():
    kb.set_root(Path(sys.argv[1]).resolve())
    _, mods = layout.directory_modules()
    files = bad = 0
    for _, fs in mods:
        for f in fs:
            files += 1
            bal, opened = 0, None
            for line in skel.skeleton(kb.read(f)).splitlines():
                nb = max(0, bal + skel.balance(line))
                if bal == 0 and nb > 0:
                    opened = line
                bal = nb
            if bal:
                bad += 1
                print(f"  {f}: {opened[:120]}")
    print(f"{bad} of {files} files end with a bracket open")


if __name__ == "__main__":
    main()
