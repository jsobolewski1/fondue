#!/usr/bin/env python3
"""Research prototype of links between directory modules: kb-universal pre-plan. Not a design.

  links.py <root> [--min N]           for each directory module, the others that use it

A module's names are the identifiers its skeleton declares: the word after a declaring keyword, or
the first word followed by '(', '=' or ':' on a line at most one indent level deep. A name counts
when it is at least 6 characters long and declared by one directory module only. Module A uses B
when A's source holds at least --min (default 3) of B's names as words, or one of B's file names.
"""
import collections
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import layout  # noqa: E402
import skel  # noqa: E402
import kb  # noqa: E402

KEYWORD = re.compile(r"\b(?:struct|enum|union|typedef|class|interface|type|def|func|fn|function|const|let|var|trait|impl)\s+\*?([A-Za-z_]\w*)")
FIRST = re.compile(r"([A-Za-z_]\w*)\s*(?:\(|=|:)")
STOP = {"return", "static", "export", "default", "import", "public", "private", "protected", "unsigned", "string",
        "number", "boolean", "object", "undefined", "function", "extends", "implements", "readonly"}


def declared(text):
    names = set(KEYWORD.findall(text))
    for line in text.splitlines():
        if skel.indent(line) <= 4:
            m = FIRST.search(line)
            if m:
                names.add(m.group(1))
    return {n for n in names if len(n) >= 6 and n not in STOP}


def main():
    kb.set_root(Path(sys.argv[1]).resolve())
    least = int(skel.opt("--min", 3))
    _, mods = layout.directory_modules()
    mods = {str(d): fs for d, fs in mods}
    names = {m: declared("\n".join(skel.skeleton(kb.read(f)) for f in fs)) for m, fs in mods.items()}
    owners = collections.Counter(n for ns in names.values() for n in ns)
    names = {m: {n for n in ns if owners[n] == 1} for m, ns in names.items()}
    texts = {m: "\n".join(kb.read(f) for f in fs) for m, fs in mods.items()}
    for b, ns in sorted(names.items()):
        word = re.compile(r"\b(" + "|".join(re.escape(n) for n in sorted(ns, key=len, reverse=True)) + r")\b") if ns else None
        fname = re.compile(r"\b(" + "|".join(re.escape(f.name) for f in mods[b]) + r")\b")
        users = []
        for a, t in sorted(texts.items()):
            if a == b:
                continue
            hits = set(word.findall(t)) if word else set()
            files = set(fname.findall(t))
            if len(hits) >= least or files:
                users.append(f"{a} ({len(hits)} names" + (f", {len(files)} file names" if files else "") + ")")
        print(f"{b:44} {len(ns):4} names  used by: {'; '.join(users) or '-'}")


if __name__ == "__main__":
    main()
