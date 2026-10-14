#!/usr/bin/env python3
"""Research prototype of a reader that knows no language: kb-universal pre-plan. Not a design.

  skel.py <root> <path>               print the skeleton of one tracked file
  skel.py <root> --java               raw and skeleton size of every .java file under src/main

Options: --depth N (default 3), --comments first|none|all (default first).

Lines are kept by indentation. A block opens when a line is followed by a more indented one. A block
whose header has no parenthesis before its end, or names a container keyword, is a container; any
other block is a body. A line is kept when every block around it is a container and it sits at most
--depth - 1 blocks deep. A kept line that leaves a bracket open keeps its continuation lines, so a
signature split over several lines stays whole. Comment and preprocessor lines never open or close
a block; of a run of comment lines only the first that carries a word is kept. A leading comment
block that mentions a copyright or licence is dropped. Lines are cut at 220 characters.
"""
import re
import subprocess
import sys
from pathlib import Path

CODE_EXT = {".c", ".h", ".cc", ".cpp", ".hpp", ".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".tsx", ".jsx",
            ".vue", ".svelte", ".py", ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".php", ".cs", ".swift",
            ".kt", ".kts", ".scala", ".groovy", ".lua", ".java", ".cmake", ".pl", ".m", ".mm"}
CODE_NAMES = {"Makefile", "makefile", "GNUmakefile", "Dockerfile", "Vagrantfile", "CMakeLists.txt", "Rakefile", "Justfile"}
CONTAINER = re.compile(r"\b(class|struct|enum|interface|union|trait|impl|object|namespace|module|record|protocol|extension)\b")
LICENSE = re.compile(r"copyright|licen[cs]e", re.I)
PREPROC = re.compile(r"^\s*#\s*(if|ifdef|ifndef|else|elif|endif|define|undef|include|pragma|error)\b")
COMMENT = re.compile(r"^\s*(#(?!!)|//|/\*|\*|--|<!--)")
MAX_LINE = 220


def is_code(p):
    return p.suffix in CODE_EXT or p.name in CODE_NAMES


def indent(line):
    n = 0
    for ch in line:
        if ch == " ":
            n += 1
        elif ch == "\t":
            n += 4
        else:
            break
    return n


def balance(line):
    return sum(1 for c in line if c in "([") - sum(1 for c in line if c in ")]")


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
        while i < n and COMMENT.match(lines[i]) and not PREPROC.match(lines[i]):
            i += 1
    return i if LICENSE.search("\n".join(lines[start:i])) else 0


def kind(header):
    h = header.strip()
    return "container" if CONTAINER.search(h.split("(")[0]) or "(" not in h else "body"


def skeleton(src, depth=3, comments="first"):
    lines = src.splitlines()
    lines = lines[leading_comment_end(lines):]
    out, stack, cont, cont_visible, comment_kept = [], [], 0, False, None
    header, prev_indent = "", None

    def shown():
        return all(k == "container" for _, k in stack) and len(stack) <= depth - 1

    for line in lines:
        s = line.strip()
        if not s:
            comment_kept = None
            continue
        if cont > 0:
            if cont_visible:
                out.append(line.rstrip()[:MAX_LINE])
            header += " " + s
            cont += balance(line)
            continue
        if COMMENT.match(line) and not PREPROC.match(line):
            worded = re.search(r"\w", s) is not None
            if shown() and (comments == "all" or (comments == "first" and not comment_kept and worded)):
                out.append(line.rstrip()[:160])
                comment_kept = True
            elif comment_kept is None:
                comment_kept = False
            continue
        comment_kept = None
        if PREPROC.match(line):
            if shown():
                out.append(line.rstrip()[:MAX_LINE])
            continue
        ind = indent(line)
        if prev_indent is not None and ind > prev_indent:
            stack.append((prev_indent, kind(header)))
        while stack and ind <= stack[-1][0]:
            stack.pop()
        cont_visible = shown()
        if cont_visible:
            out.append(line.rstrip()[:MAX_LINE])
        if s not in ("{", "{{") and not re.fullmatch(r"[})\]];?,?", s):
            header = s
        prev_indent = ind
        cont = max(0, balance(line))
    return "\n".join(out)


def opt(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    root = Path(sys.argv[1])
    depth, comments = int(opt("--depth", 3)), opt("--comments", "first")
    if "--java" in sys.argv:
        files = subprocess.run(["git", "ls-files", "*.java"], cwd=root, capture_output=True, text=True).stdout.split()
        files = [f for f in files if "/src/main/" in f]
        raw = sk = 0
        for f in files:
            src = (root / f).read_text(errors="replace")
            raw += len(src)
            sk += len(skeleton(src, depth, comments))
        print(f".java under src/main: {len(files)} files  raw {raw}  skeleton {sk}  {raw / sk:.1f}x")
        return
    print(skeleton((root / sys.argv[2]).read_text(errors="replace"), depth, comments))


if __name__ == "__main__":
    main()
