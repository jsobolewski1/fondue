#!/usr/bin/env python3
"""Research prototype of Phase 1's module rule: kb-universal plan. Not the implementation.

  discover.py <root> [--budget BYTES] [--floor BYTES]

Prints the build-file modules kb.py finds today (count only), then every directory module with
its kind (group or residual), source count, bytes, and for a residual the children folded into it.
Sizes are bytes on disk (st_size). Defaults: budget 250000, floor 5000.
"""
import fnmatch
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[4] / "protocol" / "kb"))
import kb  # noqa: E402

CODE_EXT = {".c", ".h", ".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx", ".m", ".mm", ".cs", ".go", ".rs", ".swift",
            ".kt", ".kts", ".scala", ".groovy", ".java", ".proto", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".mts",
            ".cts", ".tsx", ".vue", ".svelte", ".py", ".rb", ".php", ".pl", ".pm", ".lua", ".sh", ".bash", ".zsh",
            ".ksh", ".ps1", ".dart", ".ex", ".exs", ".erl", ".hs", ".clj", ".cmake", ".tf", ".zig", ".nim", ".jl", ".r"}
CODE_NAMES = {"Makefile", "makefile", "GNUmakefile", "Dockerfile", "Containerfile", "Vagrantfile", "Rakefile",
              "Justfile", "justfile", "CMakeLists.txt", "Jenkinsfile"}
TEST_DIRS = {"test", "tests", "__tests__", "testing", "e2e", "spec"}
VENDOR_DIRS = {"vendor", "third_party", "third-party", "node_modules", "dist", "build", "target", "out", "generated"}
TEST_FILE = re.compile(r"^test_.*\.py$|_test\.\w+$|\.test\.\w+$|\.spec\.\w+$|_spec\.rb$|Tests?\.java$")


def is_code(p):
    return p.suffix.lower() in CODE_EXT or p.name in CODE_NAMES or p.name.startswith("Dockerfile.")


def matches(pat, p):
    return str(p) == pat or Path(pat) in p.parents or fnmatch.fnmatchcase(str(p), pat)


def overrides():
    ex, inc = [], []
    if kb.PARTS.exists():
        for line in kb.PARTS.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if line.startswith("- "):
                ex.append(line[2:].strip())
            elif line.startswith("+ "):
                inc.append(line[2:].strip())
    return ex, inc


def sources(build):
    ex, inc = overrides()
    claimed = [m.main for m in build.values() if not m.parent]
    out = []
    for line in kb.git("ls-files", "-s", "-z").split("\0"):
        if not line:
            continue
        meta, path = line.split("\t", 1)
        if meta.startswith("160000"):
            continue
        p = Path(path)
        dirs = p.parts[:-1]
        if p.parts[0] == "fondue" or any(c in p.parents for c in claimed) or any(matches(x, p) for x in ex):
            continue
        if any(matches(x, p) for x in inc):
            out.append(p)
            continue
        if any(d.startswith(".") for d in dirs) or set(dirs) & (TEST_DIRS | VENDOR_DIRS) or TEST_FILE.search(p.name):
            continue
        if is_code(p):
            out.append(p)
    return out


def size(fs):
    return sum((kb.ROOT / f).stat().st_size for f in fs if (kb.ROOT / f).is_file())


def group(base, fs, roots, budget, floor, by_size):
    """Modules for files `fs` under `base`, which splits. `by_size`: the split was the budget's."""
    own, below = [], {}
    for f in fs:
        rel = f.parts[len(base.parts):] if base != Path(".") else f.parts
        (own if len(rel) == 1 else below.setdefault(base / rel[0], [])).append(f)
    mods, folded = [], []
    for d, cfs in sorted(below.items()):
        holds_root = any(r == d or d in r.parents for r in roots)
        if holds_root or size(cfs) > budget:
            mods += group(d, cfs, roots, budget, floor, by_size=not holds_root)
        elif by_size and size(cfs) < floor:
            folded.append((d, cfs))
        else:
            mods.append(("group", d, cfs, []))
    if own or folded:
        mods.insert(0, ("residual", base, own + [f for _, cfs in folded for f in cfs], [d for d, _ in folded]))
    return mods


def main():
    kb.set_root(Path(sys.argv[1]).resolve())
    budget = int(sys.argv[sys.argv.index("--budget") + 1]) if "--budget" in sys.argv else 250000
    floor = int(sys.argv[sys.argv.index("--floor") + 1]) if "--floor" in sys.argv else 5000
    build = kb.modules() if any(f.name in kb.BUILD_FILES for f in map(Path, kb.git("ls-files").splitlines())) else {}
    roots = {m.path for m in build.values() if not m.parent}
    mods = group(Path("."), sources(build), roots, budget, floor, by_size=False)
    print(f"{len(build)} build-file modules")
    for kind, d, fs, folded in mods:
        extra = f"  folds {', '.join(str(x) for x in folded)}" if folded else ""
        shared = "  (shares a build-file module's directory)" if d in roots else ""
        print(f"  {kind:8} {str(d):48} {len(fs):4} files {size(fs):>8} bytes{extra}{shared}")
    print(f"{len(mods)} directory modules")


if __name__ == "__main__":
    main()
