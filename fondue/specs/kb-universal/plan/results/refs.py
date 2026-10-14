#!/usr/bin/env python3
"""Research prototype of Phase 2's possible references: kb-universal plan. Not the implementation.

  refs.py <root> [<module path>...] [--lines]   the possible references of those directory modules (default: all):
                                        how many names, and each selected line's file; with --lines, each line

A module's names are the names reader.py's output declares (names(), below) and its files' names, with
and without extension; a name counts when it is at least 6 characters long and no other directory
module has it. Candidate lines are every line of another module's source that holds one as a whole
word: another directory module's files, or a build-file module's files under its src/main, where only
its file names count (--all-names: every name, to show why). From one file the 3 that hold the most of its names are taken, a line holding one of its
file names counting 2 more; then the lines are taken round-robin over the referencing modules, the
module holding the most distinct names first (ties in path order), 40 in all.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import discover  # noqa: E402
import reader  # noqa: E402
kb = discover.kb

KEYWORD = re.compile(r"\b(?:struct|enum|union|typedef|class|interface|type|def|func|fn|function|const|let|var|trait|"
                     r"impl|module|object|record|protocol|extension|namespace|alias|macro)\s+\*?([A-Za-z_][\w$]*)")
DEFINE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)")
CALLED = re.compile(r"([A-Za-z_][\w$]*)\s*\(")
ASSIGNED = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][\w$.-]*)\s*(?::(?!:)|=(?!=))")
TYPEDEF_END = re.compile(r"^\s*}\s*([A-Za-z_]\w*)\s*;")
STOP = {"if", "for", "while", "switch", "return", "catch", "sizeof", "elif", "else", "until", "case", "when",
        "export", "default", "import", "from", "public", "private", "protected", "static", "extern", "inline"}
PER_FILE, TOTAL, MIN_LEN = 3, 40, 6


def names(skeleton):
    out = set()
    for line in skeleton.splitlines():
        code, _ = reader.code_part(line, False)
        out.update(KEYWORD.findall(code))
        for rx in (DEFINE, ASSIGNED, TYPEDEF_END):
            m = rx.search(code)
            if m:
                out.add(m.group(1))
        m = CALLED.search(code)
        if m:
            out.add(m.group(1))
    return {n for n in out if n not in STOP}


def module_names(fs):
    ns = set()
    for f in fs:
        ns |= names(reader.skeleton(kb.read(f)))
        ns |= {f.name, f.stem}
    return {n for n in ns if len(n) >= MIN_LEN}


def main():
    kb.set_root(Path(sys.argv[1]).resolve())
    build = kb.modules()
    roots = {m.path for m in build.values() if not m.parent}
    mods = {str(d): fs for _, d, fs, _ in discover.group(Path("."), discover.sources(build), roots, 250000, 5000, by_size=False)}
    all_names = {m: module_names(fs) for m, fs in mods.items()}
    owners = {}
    for m, ns in all_names.items():
        for n in ns:
            owners.setdefault(n, set()).add(m)
    texts = {m: [(f, kb.read(f).splitlines()) for f in fs] for m, fs in mods.items()}
    for b in build.values():                      # build-file modules reference too; they declare no names here
        texts[f"build:{b.id}"] = [(f, kb.read(f).splitlines()) for f in sorted(b.sources)]
    for target in [a for a in sys.argv[2:] if not a.startswith("--")] or sorted(mods):
        own = sorted(n for n in all_names[target] if owners[n] == {target})
        if not own:
            print(f"{target}: no names")
            continue
        files = {f.name for f in mods[target]}
        pat = re.compile(r"(?<![\w$])(" + "|".join(re.escape(n) for n in sorted(own, key=len, reverse=True)) + r")(?![\w$])")
        per_module = []
        for other in sorted(texts):
            if other == target:
                continue
            lines, held = [], set()
            for f, ls in texts[other]:
                scored = []
                for no, l in enumerate(ls, 1):
                    found = set(pat.findall(l))
                    if other.startswith("build:") and "--all-names" not in sys.argv:
                        found &= files                    # from a build-file module, file names only
                    held |= found
                    if found:
                        scored.append((-(len(found) + (2 if found & files else 0)), no))
                lines += [(f, no) for _, no in sorted(sorted(scored)[:PER_FILE], key=lambda s: s[1])]
            if lines:
                per_module.append((-len(held), other, lines))
        per_module = [(o, ls) for _, o, ls in sorted(per_module)]
        picked, i = [], 0
        while len(picked) < TOTAL and any(i < len(ls) for _, ls in per_module):
            for _, ls in per_module:
                if i < len(ls) and len(picked) < TOTAL:
                    picked.append(ls[i])
            i += 1
        print(f"{target}: {len(own)} names, {len(picked)} lines from {len(per_module)} modules")
        for f in sorted({str(g) for g, _ in picked}):
            print(f"    {f} ({sum(1 for g, _ in picked if str(g) == f)})")
        if "--lines" in sys.argv:
            for g, no in picked:
                print(f"      {g}:{no}: {kb.read(g).splitlines()[no - 1].strip()[:100]}")


if __name__ == "__main__":
    main()
