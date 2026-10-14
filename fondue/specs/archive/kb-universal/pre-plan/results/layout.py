#!/usr/bin/env python3
"""Research prototype of directory modules: kb-universal pre-plan. Not a design.

  layout.py <root> [--budget CHARS]   the modules kb.py finds today, then directory modules for the rest
  layout.py <root> --measure          raw and skeleton size, per extension, of the files directory modules hold

A code file (skel.is_code) belongs to a directory module unless it is under fondue/ or a hidden
directory, in a test or vendored directory, a test file, or under the src/ of a module kb.py finds
today. Directory modules are found top-down. The repository root, and the directory of every
module kb.py finds, split: the files group by their first directory below it, and the files directly
in it form a module of their own. A group whose raw source exceeds --budget (default 250000 chars)
splits the same way one level down. Every other group is one module.
"""
import collections
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[4] / "protocol" / "kb"))
import kb  # noqa: E402
import skel  # noqa: E402

TEST_DIR = {"test", "tests", "__tests__", "testing", "e2e"}
TEST_FILE = re.compile(r"(^test_.*\.py$|_test\.\w+$|\.test\.\w+$|\.spec\.\w+$|Tests?\.java$)")
VENDOR_DIR = {"vendor", "third_party", "node_modules", "dist", "build", "target", "out"}


def tracked():
    out = []
    for line in kb.git("ls-files", "-s").splitlines():
        meta, path = line.split("\t", 1)
        if not meta.startswith("160000"):           # a submodule is a directory, not a file
            out.append(Path(path))
    return out


def code_files(files, java_mods):
    claimed = [m.path / "src" for m in java_mods.values()]
    out = []
    for p in files:
        dirs = p.parts[:-1]
        if p.parts[0] == "fondue" or any(d.startswith(".") for d in dirs):
            continue
        if set(dirs) & (TEST_DIR | VENDOR_DIR) or TEST_FILE.search(p.name) or not skel.is_code(p):
            continue
        if any(c in p.parents for c in claimed):
            continue
        out.append(p)
    return out


def size(files):
    return sum(len(kb.read(f)) for f in files)


def group(base, files, roots, budget):
    """Modules for `files`, all under directory `base`, which always splits."""
    own, below = [], collections.defaultdict(list)
    for f in files:
        rel = f.relative_to(base) if base != Path(".") else f
        (own if len(rel.parts) == 1 else below[base / rel.parts[0]]).append(f)
    mods = [(base, own)] if own else []
    for d, fs in sorted(below.items()):
        if d in roots or size(fs) > budget:
            mods += group(d, fs, roots, budget)
        else:
            mods.append((d, fs))
    return mods


def directory_modules(budget=250000):
    files = tracked()
    java = kb.modules()
    code = code_files(files, java)
    roots = {m.path for m in java.values()}
    return java, group(Path("."), code, roots, budget)


def main():
    kb.set_root(Path(sys.argv[1]).resolve())
    budget = int(skel.opt("--budget", 250000))
    java, mods = directory_modules(budget)
    if "--measure" in sys.argv:
        by_ext = collections.defaultdict(lambda: [0, 0, 0])
        for _, fs in mods:
            for f in fs:
                src = kb.read(f)
                e = by_ext[f.suffix or f.name]
                e[0] += 1
                e[1] += len(src)
                e[2] += len(skel.skeleton(src, int(skel.opt("--depth", 3)), skel.opt("--comments", "first")))
        tr = ts = 0
        for k, (n, r, s) in sorted(by_ext.items(), key=lambda kv: -kv[1][1]):
            print(f"{k:16} {n:5} files  raw {r:>9}  skeleton {s:>8}  {r / max(s, 1):5.1f}x")
            tr, ts = tr + r, ts + s
        print(f"{'total':16}        raw {tr:>9}  skeleton {ts:>8}  {tr / max(ts, 1):5.1f}x")
        return
    print(f"{len(java)} modules kb.py finds today")
    for d, fs in mods:
        raw = size(fs)
        sk = sum(len(skel.skeleton(kb.read(f))) for f in fs)
        print(f"  {str(d):52} {len(fs):4} files  raw {raw:>8}  skeleton {sk:>7}")
    print(f"{len(mods)} directory modules")


if __name__ == "__main__":
    main()
