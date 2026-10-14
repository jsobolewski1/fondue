#!/usr/bin/env python3
r"""Research prototype of Phase 2's reader: kb-universal plan. Not the implementation.

  reader.py <root> <path>          print the skeleton of one file
  reader.py <root> --check         per sample: files whose skeleton ends with a bracket open, and the
                                   raw/skeleton ratio over the files discover.py's directory modules hold

The pre-plan prototype (pre-plan/results/skel.py) with three repairs: brackets inside string literals
and comments do not count (a trailing `//` or `#` comment starts at the line's start or after a space,
so a regex literal like `/^W\//` is not one); a block comment's lines are comment lines whatever
they start with; a kept line over 220 characters is cut and closed with '…' and the brackets the cut left open; a kept
preprocessor line is closed the same way, and its continuation lines are not kept.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import discover  # noqa: E402
kb = discover.kb

CONTAINER = re.compile(r"\b(class|struct|enum|interface|union|trait|impl|object|namespace|module|record|protocol|extension)\b")
LICENSE = re.compile(r"copyright|licen[cs]e", re.I)
PREPROC = re.compile(r"^\s*#\s*(if|ifdef|ifndef|else|elif|endif|define|undef|include|pragma|error)\b")
LINE_COMMENT = re.compile(r"^\s*(#(?!!)|//|--|\*|<!--)")
DEPTH, MAX_LINE, MAX_COMMENT = 3, 220, 160
OPEN, CLOSE = "([", ")]"


def code_part(line, in_block):
    """The line without string literals and comments; and whether a block comment is open at its end."""
    out, i, n = [], 0, len(line)
    while i < n:
        if in_block:
            j = line.find("*/", i)
            if j < 0:
                return "".join(out), True
            i, in_block = j + 2, False
            continue
        c = line[i]
        if line.startswith("/*", i):
            in_block = True
            i += 2
        elif (line.startswith("//", i) or c == "#") and (i == 0 or line[i - 1] in " \t"):
            break
        elif c in "\"'`":
            j = i + 1
            while j < n and line[j] != c:
                j += 2 if line[j] == "\\" else 1
            if j >= n:                     # no closing quote on the line: not a string
                out.append(c)
                i += 1
            else:
                i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out), in_block


def balance(code):
    return sum(c in OPEN for c in code) - sum(c in CLOSE for c in code)


def closers(code):
    stack = []
    for c in code:
        if c in OPEN:
            stack.append(CLOSE[OPEN.index(c)])
        elif c in CLOSE and stack:
            stack.pop()
    return "".join(reversed(stack))


def closed(line, limit):
    """The line cut at `limit`, with the brackets its kept part leaves open closed."""
    head = line[:limit]
    return head + ("…" if len(line) > limit else "") + closers(code_part(head, False)[0])


def cut(line, limit):
    return line if len(line) <= limit else closed(line, limit)


def leading_comment_end(lines):
    i, n = 0, len(lines)
    while i < n and (not lines[i].strip() or lines[i].startswith("#!")):
        i += 1
    start = i
    s = lines[i].strip() if i < n else ""
    if s.startswith(("/*", "<!--")):
        end = "*/" if s.startswith("/*") else "-->"
        while i < n and end not in lines[i]:
            i += 1
        i += 1
    else:
        while i < n and LINE_COMMENT.match(lines[i]) and not PREPROC.match(lines[i]):
            i += 1
    return i if LICENSE.search("\n".join(lines[start:i])) else 0


def kind(code):
    h = code.strip()
    return "container" if CONTAINER.search(h.split("(")[0]) or "(" not in h else "body"


def skeleton(src):
    lines = src.splitlines()
    lines = lines[leading_comment_end(lines):]
    out, stack, cont, cont_shown, comment_kept, in_block = [], [], 0, False, None, False
    header, prev_indent = "", None

    def shown():
        return all(k == "container" for _, k in stack) and len(stack) <= DEPTH - 1

    for line in lines:
        s = line.strip()
        was_block = in_block
        code, in_block = code_part(line, in_block)
        if not s:
            comment_kept = None
            continue
        if cont > 0:
            if cont_shown:
                out.append(line.rstrip())
            header += " " + code.strip()
            cont += balance(code)
            continue
        if was_block or LINE_COMMENT.match(line) and not PREPROC.match(line) or (not code.strip() and s.startswith("/*")):
            if shown() and not comment_kept and re.search(r"\w", s):
                out.append(cut(line.rstrip(), MAX_COMMENT))
                comment_kept = True
            elif comment_kept is None:
                comment_kept = False
            continue
        comment_kept = None
        if PREPROC.match(line):
            if shown():
                out.append(closed(line.rstrip(), MAX_LINE))
            continue
        ind = len(line) - len(line.lstrip(" \t")) + line[: len(line) - len(line.lstrip(" \t"))].count("\t") * 3
        if prev_indent is not None and ind > prev_indent:
            stack.append((prev_indent, kind(header)))
        while stack and ind <= stack[-1][0]:
            stack.pop()
        cont_shown = shown()
        if cont_shown:
            out.append(cut(line.rstrip(), MAX_LINE))
        if not re.fullmatch(r"[{}()\[\];,]*", code.strip()):
            header = code
        prev_indent = ind
        cont = max(0, balance(code))
    return "\n".join(out)


def ends_open(text):
    bal, in_block = 0, False
    for line in text.splitlines():
        code, in_block = code_part(line, in_block)
        bal = max(0, bal + balance(code))
    return bal > 0


def main():
    root = Path(sys.argv[1]).resolve()
    kb.set_root(root)
    if "--check" not in sys.argv:
        print(skeleton((root / sys.argv[2]).read_text(errors="replace")))
        return
    build = kb.modules()
    roots = {m.path for m in build.values() if not m.parent}
    mods = discover.group(Path("."), discover.sources(build), roots, 250000, 5000, by_size=False)
    files = [f for _, _, fs, _ in mods for f in fs]
    raw = sk = 0
    bad = []
    for f in files:
        src = kb.read(f)
        out = skeleton(src)
        raw, sk = raw + len(src), sk + len(out)
        if ends_open(out):
            bad.append(str(f))
    print(f"{len(files)} files, raw {raw}, skeleton {sk}, {raw / max(sk, 1):.1f}x; ending with a bracket open: {len(bad)} {bad[:5]}")


if __name__ == "__main__":
    main()
