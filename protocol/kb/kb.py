#!/usr/bin/env python3
"""The knowledge base's tooling (protocol/kb.md). Run from the project root, or pass --root.

  kb.py modules                       list the source modules and their size
  kb.py estimate [<id>... | --since <sha>]  what writing those cards (default: all) costs, before spending it
  kb.py write <id>... | --all         write cards: pack each module, one tool-less model call each, then the index
  kb.py write --since <sha>           write the cards of modules changed since <sha>, and of modules with no card
  kb.py touched <sha>                 modules changed since <sha>, and the project skills that cover them
  kb.py status [<id>...] [--since <sha>]  every card against the code: changes since verified-at, dead symbols;
                                      with --since, a card the work since <sha> left stale is a problem too
  kb.py index                         regenerate index.md from the cards
  kb.py usage [--since <time>]        tokens and cost of the model calls this tool made, since a local
                                      time as `date +%Y-%m-%dT%H:%M:%S` prints it
  kb.py pack <id>...                  write the packed input only, to .packs/ (debugging)

Everything except `write` is mechanical and spends no tokens.
"""

import argparse
import concurrent.futures
import datetime
import fnmatch
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
CARD_WRITER = HERE / "card-writer.md"

BUILD_FILES = ("pom.xml", "build.gradle", "build.gradle.kts")
CODE_EXT = {".c", ".h", ".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx", ".m", ".mm", ".cs", ".go", ".rs", ".swift",
            ".kt", ".kts", ".scala", ".groovy", ".java", ".proto", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".mts", ".cts",
            ".tsx", ".vue", ".svelte", ".py", ".rb", ".php", ".pl", ".pm", ".lua", ".sh", ".bash", ".zsh", ".ksh", ".ps1",
            ".dart", ".ex", ".exs", ".erl", ".hs", ".clj", ".cmake", ".tf", ".zig", ".nim", ".jl", ".r"}
CODE_NAMES = {"Makefile", "makefile", "GNUmakefile", "Dockerfile", "Containerfile", "Vagrantfile", "Rakefile",
              "Justfile", "justfile", "CMakeLists.txt", "Jenkinsfile"}
TEST_DIRS = {"test", "tests", "__tests__", "testing", "e2e", "spec"}
VENDOR_DIRS = {"vendor", "third_party", "third-party", "node_modules", "dist", "build", "target", "out", "generated"}
TEST_FILES = ("test_*.py", "*_test.*", "*.test.*", "*.spec.*", "*_spec.rb", "*Test.java", "*Tests.java")
BUDGET = 250_000          # bytes of source: a directory over it splits into its subdirectories
FLOOR = 5_000             # bytes of source: a subdirectory under it, after a size split, stays with its parent
DECLARED_EXT = {".java", ".proto"}
WIRING_GLOBS = ("META-INF/services/*", "application*.yml", "application*.yaml", "application*.properties")
WIRING_MAX_LINES = 60
SKILL_LINES_PER_SKILL = 15
WIRED_FROM_MAX = 40
WIRING_NAMES = ("package.json", "deno.json", "jsr.json", "tsconfig.json", "Cargo.toml", "go.mod", "pyproject.toml",
                "setup.cfg", "requirements.txt", "Pipfile", "composer.json", "Gemfile", "pubspec.yaml")
WIRING_MAX_FILES = 8
HEADER_MAX = 220
SKELETON_DEPTH = 3        # the generic reader shows a line inside at most this many levels, counting the top
LINE_MAX = 220            # the generic reader cuts a kept line here, and closes its open brackets
COMMENT_MAX = 160
CONTAINER_KW = ("class", "struct", "enum", "interface", "union", "trait", "impl", "object", "namespace", "module",
                "record", "protocol", "extension")
REFS_PER_FILE = 3
REF_NAME_MIN = 6
CARD_MAX_LINES = 60
CHARS_PER_TOKEN = 2.5     # measured on Java skeletons; chars/4 undercounts code by about 1.6x
CHARS_PER_TOKEN_ANY = 2.5 # measured on packs read by the generic reader (skills/kb-init/design-notes.md)
VARIANTS = ("java", "any code")
WRITER_OVERHEAD = 1800    # system prompt and harness per call, in tokens
WRITER_OUTPUT = 1500      # tokens a card takes to write
PARALLEL = 6

ROOT = KB = CARDS = PACKS = RUNS = PARTS = None
FILES, RULES = [], []     # the tracked files and parts.txt's patterns, as modules() last read them
NAMES = {}                # a directory module's names for possible references, by id, since modules() last ran


def set_root(root):
    global ROOT, KB, CARDS, PACKS, RUNS, PARTS
    ROOT = Path(root).resolve()
    KB = ROOT / "fondue" / "kb"
    CARDS, PACKS, RUNS, PARTS = KB / "cards", KB / ".packs", KB / ".runs", KB / "parts.txt"


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def read(path):
    return (ROOT / path).read_text(errors="replace")


# ---------- modules ----------

class Module:
    """A card's unit. A build-file module is a directory with a build file and sources under src/main (kind "build").
    A directory module holds source no build file claims (kind "dir"): a whole directory (a group), or the files
    directly in one together with the small subdirectories folded into them (a residual). A part is a directory inside
    either that parts.txt gives a card of its own, of its module's kind.
    `main` is the directory whose changes count against a build-kind card, `build` the directory of the build file,
    `artifact` the name other build files depend on it by. A build-kind part shares its module's build and artifact;
    a directory module is its own build and artifact, and depends on nothing."""
    def __init__(self, path, mid, deps, sources, artifact, main=None, build=None, parent=None, kind="build"):
        self.path, self.id, self.deps, self.sources, self.artifact = path, mid, deps, sources, artifact
        self.main = main or path / "src" / "main"
        self.build = build or path
        self.parent = parent
        self.kind = kind
        self.residual = False
        self.parts, self.dependents, self.excluded, self.siblings_used, self.folded = [], [], [], [], []


def pom_info(pom):
    root = ET.parse(ROOT / pom).getroot()
    ns = root.tag[: root.tag.index("}") + 1] if root.tag.startswith("{") else ""
    aid = root.find(f"{ns}artifactId")
    deps = []
    for d in root.findall(f"{ns}dependencies/{ns}dependency"):
        a, s = d.find(f"{ns}artifactId"), d.find(f"{ns}scope")
        deps.append((a.text.strip(), s.text.strip() if s is not None else "compile"))
    return (aid.text.strip() if aid is not None else pom.parent.name), deps


def tracked():
    """Every tracked file, named as git stores it (-z: never quoted). A submodule is a directory, not a file."""
    paths = {}
    for entry in git("ls-files", "-s", "-z").split("\0"):
        if entry:
            meta, path = entry.split("\t", 1)
            if meta.split()[0] != "160000":
                paths[path] = None
    return [Path(p) for p in paths]


def file_size(f):
    try:
        return (ROOT / f).stat().st_size
    except OSError:
        return 0


def within(p, d):
    """p is the directory d or anything below it."""
    return p == d or d in p.parents


def read_parts():
    """fondue/kb/parts.txt, written by the User, one line each:
      `<card id> <directory>`  a directory inside a module gets a card of its own (split_parts);
      `- <pattern>`            what the pattern matches is not a source;
      `+ <pattern>`            what the pattern matches is a source, whatever its kind.
    A pattern is a path, a directory, or a glob over the whole path whose `*` also crosses `/`.
    Returns the patterns as (sign, pattern) and the parts as (line number, card id, directory)."""
    rules, parts = [], []
    if not PARTS.exists():
        return rules, parts
    for no, line in enumerate(PARTS.read_text().splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        words = line.split()
        if len(words) != 2:
            sys.exit(f"{PARTS.relative_to(ROOT)}:{no}: expected `<card id> <directory>`, `- <pattern>` or `+ <pattern>`")
        if words[0] in ("-", "+"):
            rules.append((words[0], words[1].rstrip("/")))
        else:
            parts.append((no, words[0], words[1]))
    return rules, parts


def matches(pattern, p):
    s = p.as_posix()
    return s == pattern or s.startswith(pattern + "/") or fnmatch.fnmatchcase(s, pattern)


def ruled(f, rules, sign):
    return any(matches(pat, f) for s, pat in rules if s == sign)


def code_file(f):
    return f.suffix.lower() in CODE_EXT or f.name in CODE_NAMES or f.name.startswith("Dockerfile.")


def is_source(f, mains, rules):
    """Whether a tracked file outside the build-file modules is a directory module's source: the first rule that
    applies decides."""
    if len(f.parts) > 1 and f.parts[0] == "fondue":
        return False
    if any(d in mains for d in f.parents):
        return False
    if ruled(f, rules, "-"):
        return False
    if ruled(f, rules, "+"):
        return True
    if any(d.startswith(".") or d in TEST_DIRS or d in VENDOR_DIRS for d in f.parts[:-1]):
        return False
    if any(fnmatch.fnmatchcase(f.name, t) for t in TEST_FILES):
        return False
    return code_file(f)


def directory_modules(files, found, rules):
    """The source no build-file module claims, as directory modules added to `found`.
    The repository root and every build-file module's directory are roots. Splitting a directory makes a residual of
    the files directly in it, and groups the rest by their first directory below it. A child group is split the same
    way when it is a root or holds one (a structural split) or when its source exceeds BUDGET (a size split); after a
    size split, a child under FLOOR is folded into the residual; any other child is one group module."""
    roots = {m.path for m in found.values()}
    mains = {m.main for m in found.values()}
    srcs = [f for f in files if is_source(f, mains, rules)]
    sizes = {f: file_size(f) for f in srcs}
    made = []

    def holds_root(d):
        return any(within(r, d) for r in roots)

    def split(d, by_size, group):
        own, folded, children = [], [], {}
        for f in group:
            rel = f.parts[len(d.parts):]
            if len(rel) == 1:
                if f.name not in BUILD_FILES:
                    own.append(f)
            else:
                children.setdefault(d / rel[0], []).append(f)
        for c, cf in sorted(children.items()):
            size = sum(sizes[f] for f in cf)
            if holds_root(c):
                split(c, False, cf)
            elif size > BUDGET:
                split(c, True, cf)
            elif by_size and size < FLOOR:
                own += cf
                folded.append(c)
            else:
                made.append((c, cf, [], False))
        if own:
            made.append((d, own, folded, True))

    split(Path("."), False, srcs)
    for path, sources, folded, residual in sorted(made, key=lambda t: t[0].parts):
        base = "root" if path == Path(".") else str(path).replace("/", "-")
        mid, n = base, 1
        while mid in found:
            mid, n = f"{base}-dir{n if n > 1 else ''}", n + 1
        m = Module(path, mid, [], sorted(sources), mid, main=path, build=path, kind="dir")
        m.residual, m.folded = residual, folded
        found[mid] = m


def modules():
    """Build-file modules first, as Maven and Gradle lay them out; then directory modules for the rest of the source;
    then the parts parts.txt names. Dependencies are known among build-file modules only."""
    global FILES, RULES
    files = tracked()
    fileset = set(files)
    rules, parts = read_parts()
    FILES, RULES = files, rules
    NAMES.clear()
    found = {}
    for d in sorted({f.parent for f in files if f.name in BUILD_FILES}):
        main = d / "src" / "main"
        srcs = [f for f in files if main in f.parents]
        if not srcs:
            continue
        pom = d / "pom.xml"
        mid, deps = pom_info(pom) if pom in fileset else (d.name, [])
        found[mid] = Module(d, mid, deps, srcs, mid)
    directory_modules(files, found, rules)
    split_parts(found, parts, files)
    build = [m for m in found.values() if m.kind == "build"]
    for m in build:
        for aid, scope in m.deps:
            if scope == "test":
                continue
            for target in build:
                if target.artifact == aid and target is not m:
                    target.dependents.append(m.id)
    narrow_split(found)
    return found


def narrow_split(found):
    """A build file depends on a whole module, but a module that depends on a split one uses only the parts it imports.
    The parts of one module depend on each other the same way."""
    build = [m for m in found.values() if m.kind == "build"]
    split = [m for m in build if m.parent or m.parts]
    if not split:
        return
    texts = {m.id: [read(f) for f in m.sources if f.suffix == ".java"] for m in build}
    for m in split:
        pkgs = packages(m)
        imports = importer(pkgs) if pkgs else None
        m.dependents = sorted(o.id for o in build
                              if o is not m and imports and any(imports.search(t) for t in texts[o.id]))
    for m in split:
        m.siblings_used = sorted(s.id for s in split if s.artifact == m.artifact and m.id in s.dependents)


def split_parts(found, parts, files):
    """A part takes the sources under its directory; the module that owns that directory keeps the rest, and loses
    its card if none are left."""
    where = PARTS.relative_to(ROOT)
    mains = build_mains(found)
    for no, pid, rel in parts:
        d = Path(rel)
        owned = [(f, o) for f in files if d in f.parents for o in [owner(f, found, mains)] if o]
        parent = owned[0][1] if owned else None
        if parent is None or pid in found:
            sys.exit(f"{where}:{no}: " + (f"`{pid}` is taken" if parent else f"{rel} is in no module"))
        if any(o is not parent for _, o in owned) or not within(d, owns(parent, owned[0][0], mains)):
            sys.exit(f"{where}:{no}: {rel} is not inside one module")
        srcs = [f for f in parent.sources if d in f.parents]
        if not srcs:
            sys.exit(f"{where}:{no}: {rel} holds none of {parent.id}'s sources")
        parent.sources = [f for f in parent.sources if d not in f.parents]
        parent.parts.append(pid)
        parent.excluded.append(d)
        parent.folded = [f for f in parent.folded if f != d]
        if parent.kind == "build":
            found[pid] = Module(d, pid, parent.deps, srcs, parent.artifact, main=d, build=parent.build, parent=parent.id)
        else:
            found[pid] = Module(d, pid, [], srcs, pid, main=d, build=d, parent=parent.id, kind="dir")
    for mid in [mid for mid, m in found.items() if not m.sources]:
        del found[mid]


def build_mains(mods):
    """The src/main of every build-file module that is not a part: no directory module owns anything under one."""
    return [m.main for m in mods.values() if m.kind == "build" and not m.parent]


def owns(m, p, mains):
    """The directory through which module m owns the tracked path p, or None. Every path, source or not, in a module's
    scope counts as a change to it."""
    if any(within(p, d) for d in m.excluded):
        return None
    if m.kind == "build":
        return m.main if m.main in p.parents else None
    if any(mn in p.parents for mn in mains):
        return None
    if not m.residual:
        return m.path if m.path in p.parents else None
    if p.parent == m.path and p.name not in BUILD_FILES:
        return m.path
    return next((f for f in m.folded if f in p.parents), None)


def owner(p, mods, mains):
    """The module that owns p; where more than one does, the one owning it through the deepest directory (a part)."""
    best, depth = None, -1
    for m in mods.values():
        root = owns(m, p, mains)
        if root is not None and len(root.parts) > depth:
            best, depth = m, len(root.parts)
    return best


def pathspecs(m, mods):
    """git pathspecs naming exactly what m owns."""
    excluded = [f":(exclude){d}" for d in m.excluded]
    if m.kind == "build":
        return [str(m.main), *excluded]
    mains = build_mains(mods)
    if not m.residual:
        return [str(m.path), *(f":(exclude){mn}" for mn in mains if m.path in mn.parents), *excluded]
    here = ":(glob)*" if m.path == Path(".") else f":(glob){m.path}/*"
    return [here, *map(str, m.folded), *(f":(exclude){m.path / b}" for b in BUILD_FILES),
            *(f":(exclude){mn}" for mn in mains if any(f in mn.parents for f in m.folded)), *excluded]


# ---------- declarations without bodies ----------

JAVA_PACKAGE = re.compile(r"^package\s+([\w.]+)\s*;", re.M)
TYPE_KW = re.compile(r"\b(class|interface|enum|record|@interface)\b")
ANNOTATION = re.compile(r"@[\w.]+(\([^()]*\))?\s*")
OVERRIDE = re.compile(r"@Override\s*")
TYPE_DECL = re.compile(r"\b(?:class|interface|enum|record|message|service)\s+([A-Z]\w*)")


def first_sentence(doc):
    text = " ".join(l.strip().lstrip("*").strip() for l in doc.splitlines())
    text = re.sub(r"\{@\w+\s+([^}]*)\}", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = "" if text.startswith("@") else text.split(" @", 1)[0]
    end = re.search(r"\.(\s|$)", text)
    return (text[: end.start() + 1] if end else text).strip()[:160]


def java_skeleton(src):
    """Type and member declarations of a Java source, with method bodies, initializers and comments dropped.
    A Javadoc's first sentence is kept above the declaration it documents."""
    out, stack, header, doc = [], [], [], None
    paren, i, n = 0, 0, len(src)

    def in_body():
        return bool(stack) and stack[-1] == "body"

    def emit(text):
        pad = "  " * sum(1 for k in stack if k == "type")
        if doc:
            out.append(f"{pad}// {doc}")
        out.append(pad + text)

    def norm():
        h = OVERRIDE.sub("", " ".join("".join(header).split()))
        return h if len(h) <= HEADER_MAX else h[:HEADER_MAX] + "…"

    while i < n:
        c = src[i]
        if src.startswith("/**", i):
            j = src.find("*/", i + 3)
            j = n if j < 0 else j
            if not in_body():
                doc = first_sentence(src[i + 3 : j]) or doc
            i = j + 2
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif src.startswith('"""', i):
            j = src.find('"""', i + 3)
            i = n if j < 0 else j + 3
            if not in_body():
                header.append('"""…"""')
        elif c in "\"'":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            if not in_body():
                header.append(src[i : j + 1][:60])
            i = j + 1
        elif in_body():
            if c == "{":
                stack.append("body")
            elif c == "}":
                stack.pop()
                if not in_body():
                    header, doc = [], None
            i += 1
        elif c == "{" and paren == 0:
            h = norm()
            if TYPE_KW.search(ANNOTATION.sub("", h).split("(")[0]):
                emit(h + " {")
                stack.append("type")
            else:
                if "(" in h and "=" not in h.split("(")[0]:
                    emit(h + ";")                              # method or constructor
                elif "=" in h:
                    emit(h.split("=")[0].strip() + " = …;")    # field with a block initializer
                stack.append("body")                          # an initializer block emits nothing
            header, doc = [], None
            i += 1
        elif c == "}" and paren == 0:
            if stack:
                stack.pop()
                emit("}")
            header, doc = [], None
            i += 1
        elif c == ";" and paren == 0:
            h = norm()
            if h and not h.startswith("import "):
                emit(h.split("=")[0].strip() + ";" if "=" in ANNOTATION.sub("", h) else h + ";")
            header, doc = [], None
            i += 1
        else:
            if c == "(":
                paren += 1
            elif c == ")":
                paren = max(0, paren - 1)
            header.append(c)
            i += 1
    return "\n".join(out)


def proto_skeleton(src):
    return "\n".join(l.rstrip() for l in src.splitlines() if l.strip() and not l.strip().startswith("//"))


# ---------- declarations in any language ----------

LICENCE = re.compile(r"copyright|licen[cs]e", re.I)
PREPROCESSOR = re.compile(r"#\s*(?:if|ifdef|ifndef|else|elif|endif|define|undef|include|pragma|error)\b")
COMMENT_START = ("//", "--", "*", "<!--", "/*")
CONTAINER = re.compile(r"\b(?:" + "|".join(CONTAINER_KW) + r")\b")


def code_part(line, in_comment):
    """The line without string literals and comments, and whether a /* */ comment is still open at its end.
    A string runs from a quote to the same quote on the line, with backslash escapes; a quote never closed on the
    line is a plain character. A // or # comment starts the line or follows a space or tab."""
    out, i, n = [], 0, len(line)
    while i < n:
        if in_comment:
            j = line.find("*/", i)
            if j < 0:
                return "".join(out), True
            i, in_comment = j + 2, False
            continue
        c = line[i]
        if line.startswith("/*", i):
            in_comment, i = True, i + 2
        elif c in "\"'`":
            j = i + 1
            while j < n and line[j] != c:
                j += 2 if line[j] == "\\" else 1
            if j < n:
                i = j + 1
            else:
                out.append(c)
                i += 1
        elif (line.startswith("//", i) or c == "#") and (i == 0 or line[i - 1] in " \t"):
            break
        else:
            out.append(c)
            i += 1
    return "".join(out), in_comment


def balance(code):
    return code.count("(") + code.count("[") - code.count(")") - code.count("]")


def indentation(line):
    n = 0
    for c in line:
        if c == " ":
            n += 1
        elif c == "\t":
            n += 4
        else:
            break
    return n


def drop_licence(lines):
    """Lines without the leading comment blocks that hold a copyright or licence, after blank lines and a #! line."""
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and lines[i].startswith("#!"):
        i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
    if i >= len(lines):
        return lines
    first, j = lines[i].strip(), i
    if first.startswith(("/*", "<!--")):
        end = "*/" if first.startswith("/*") else "-->"
        while j < len(lines) and end not in (lines[j].strip()[2:] if j == i else lines[j]):
            j += 1
        j += 1
    else:
        while j < len(lines) and is_line_comment(lines[j].strip()):
            j += 1
    if j > i and LICENCE.search("\n".join(lines[i:j])):
        return lines[:i] + drop_licence(lines[j:])
    return lines


def is_line_comment(stripped):
    return (stripped.startswith("#") and not stripped.startswith("#!") and not PREPROCESSOR.match(stripped)) \
        or stripped.startswith(("//", "--"))


def cut(line, in_comment):
    """A kept line over the limit, cut there and closed: `…` and the brackets its kept part leaves open."""
    if len(line) <= LINE_MAX:
        return line
    kept = line[:LINE_MAX]
    code, _ = code_part(kept.lstrip().lstrip("#") if PREPROCESSOR.match(kept.lstrip()) else kept, in_comment)
    opened = []
    for c in code:
        if c in "([":
            opened.append(c)
        elif c in ")]" and opened:
            opened.pop()
    return kept + "…" + "".join(")" if c == "(" else "]" for c in reversed(opened))


def comment_text(raw, in_comment, pad):
    """A kept comment line, as a // or # comment whatever its own markers, so it never opens a comment or a bracket."""
    stripped = raw.strip()
    if not in_comment and stripped.startswith(("#", "//")):
        return (pad + stripped)[: len(pad) + COMMENT_MAX]
    text = stripped
    for mark in ("<!--", "/**", "/*", "--", "*"):
        if text.startswith(mark):
            text = text[len(mark):]
            break
    for mark in ("-->", "*/"):
        if text.endswith(mark):
            text = text[: -len(mark)]
    return pad + "// " + text.strip()[:COMMENT_MAX]


def generic_skeleton(src):
    """Declarations of a source in any language, by indentation: a line is kept while every block it sits in is a
    container (a header with no `(`, or a type keyword before it) and it sits at most SKELETON_DEPTH levels deep.
    A body's lines are dropped. A kept line's continuation, while its ( and [ stay open, is kept whole."""
    out, stack = [], []                 # stack: (header indentation, is container) of each open block
    in_comment, skip_macro = False, False
    last = header = None                # the last logical code line, and the last that can head a block: [indent, code]
    open_brackets, keep_continuation = 0, False
    run = None                          # the comment run so far: (indentation, its first line with a word character)

    def shown(blocks):
        return len(blocks) < SKELETON_DEPTH and all(container for _, container in blocks)

    def opened(header):
        return header[0], not ("(" in header[1] and not CONTAINER.search(header[1].split("(")[0]))

    def flush():
        """A comment sits in the blocks its indentation puts it in, and in the one the last code line opens when it is
        indented under it."""
        nonlocal run
        if run and run[2] is not None:
            indent, _, text = run
            blocks = [b for b in stack if b[0] < indent]
            if last is not None and header is not None and indent > last[0]:
                blocks.append(opened(header))
            if shown(blocks):
                out.append(text)
        run = None

    for raw in drop_licence(src.splitlines()):
        raw = raw.rstrip()
        if skip_macro:
            skip_macro = raw.endswith("\\")
            continue
        started_in_comment = in_comment
        code, in_comment = code_part(raw, in_comment)
        stripped = raw.strip()
        if open_brackets > 0:
            open_brackets += balance(code)
            last[1] += " " + code
            if keep_continuation:
                out.append(cut(raw, started_in_comment))
            continue
        if not stripped:
            flush()
            continue
        if started_in_comment or is_line_comment(stripped) or stripped.startswith(COMMENT_START):
            if run is None:
                run = (indentation(raw), raw[: len(raw) - len(raw.lstrip())], None)
            if run[2] is None and re.search(r"\w", stripped):
                run = (*run[:2], comment_text(raw, started_in_comment, run[1]))
            continue
        flush()
        if PREPROCESSOR.match(stripped):
            if shown(stack):
                out.append(cut(raw, False))
            skip_macro = raw.endswith("\\")
            continue
        indent = indentation(raw)
        if last is not None and indent > last[0]:
            if header is not None:
                stack.append(opened(header))
        else:
            while stack and indent <= stack[-1][0]:
                stack.pop()
        keep_continuation = shown(stack)
        if keep_continuation:
            out.append(cut(raw, started_in_comment))
        last = [indent, code]
        if re.search(r"\w", code):
            header = last
        open_brackets = balance(code)
    flush()
    return "\n".join(out)


def generic_source(f):
    """A build-file module's file under src/main that the generic reader reads: a source by the code list or the name
    list, or by an include line, and not excluded."""
    return not ruled(f, RULES, "-") and (ruled(f, RULES, "+") or code_file(f))


def skeleton(f):
    if f.suffix == ".java":
        return java_skeleton(read(f))
    if f.suffix == ".proto":
        return proto_skeleton(read(f))
    return generic_skeleton(read(f))


def read_files(m):
    """The files declarations(m) reads, in path order: .java and .proto by their readers, the rest by the generic one."""
    return [f for f in sorted(m.sources) if f.suffix in DECLARED_EXT or m.kind == "dir" or generic_source(f)]


def variant(m):
    """The writer's prompt for m: "java" when its declarations read only .java and .proto, "any code" otherwise."""
    return "any code" if any(f.suffix not in DECLARED_EXT for f in read_files(m)) else "java"


def prompt(v):
    """card-writer.md for one variant: the lines marked for the other dropped, its own lines unmarked."""
    out = []
    for line in CARD_WRITER.read_text().splitlines(keepends=True):
        mark = next((f"[{w}] " for w in VARIANTS if line.startswith(f"[{w}] ")), None)
        if mark is None:
            out.append(line)
        elif mark == f"[{v}] ":
            out.append(line[len(mark):])
    return "".join(out)


def chars_per_token(m):
    return CHARS_PER_TOKEN if variant(m) == "java" else CHARS_PER_TOKEN_ANY


def declarations(m):
    parts = []
    for f in read_files(m):
        body = skeleton(f)
        if body.strip():
            parts.append(f"### {f.relative_to(m.path)}\n{body}")
    return "\n\n".join(parts)


def declared_types(m):
    names = set()
    for f in m.sources:
        if f.suffix in DECLARED_EXT:
            names.update(TYPE_DECL.findall(read(f)))
    return names


# ---------- packing ----------

def skills():
    base = ROOT / ".claude" / "skills"
    return {p.parent.name: p.read_text(errors="replace") for p in sorted(base.glob("*/SKILL.md"))}


def skill_description(text):
    m = re.search(r'^description:\s*"?(.*?)"?\s*$', text, re.M)
    return m.group(1) if m else ""


def skill_mentions(m, all_skills, types):
    # A part's directory name is a package segment ("ir", "dm"), far too common a word to match on.
    if m.kind == "dir":
        names = {m.id} | ({str(m.path)} if m.path != Path(".") else set())
    elif m.parent:
        names = {m.id, f"{m.build.name}/{m.path.name}"}
    else:
        names = {m.id, m.path.name}
    terms = names | {t for t in types if len(t) >= 6}
    pattern = re.compile(r"\b(" + "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)) + r")\b")
    hits = {}
    for name, text in all_skills.items():
        lines = [l.strip() for l in text.splitlines() if pattern.search(l)]
        if lines:
            hits[name] = lines
    return hits


def module_header(m, mods):
    artifacts = {o.artifact for o in mods.values() if o.kind == "build"}
    internal = sorted(a for a, s in m.deps if a in artifacts and s != "test")
    external = sorted(a for a, s in m.deps if a not in artifacts and s != "test")
    split = []
    if m.parent:
        siblings = [p for p in mods[m.parent].parts if p != m.id] if m.parent in mods else []
        split = [f"part of module {m.parent} ({m.build}), which has a card of its own for each of: "
                 f"{', '.join([m.id] + siblings)}. The external dependencies below are the whole module's.",
                 f"uses within {m.parent}: {', '.join(m.siblings_used) or '-'}"]
    elif m.parts:
        split = [f"the declarations below are what is left of this module after its parts, each with a card of its own: "
                 f"{', '.join(m.parts)}",
                 f"uses within {m.id}: {', '.join(m.siblings_used) or '-'}"]
    return "\n".join([
        f"# Module {m.id}",
        f"path: {m.path}",
        *([f"holds: the files directly in {m.path}" + "".join(f", and {f}/" for f in m.folded)] if m.residual else []),
        *split,
        f"depends on (project): {', '.join(internal) or '-'}",
        f"depends on (external): {', '.join(external) or '-'}",
        f"depended on by: {', '.join(sorted(m.dependents)) or '-'}",
    ])


def wiring_file(f, root):
    lines = [l for l in f.read_text(errors="replace").splitlines() if l.strip() and not l.strip().startswith("#")]
    more = f"\n… ({len(lines) - WIRING_MAX_LINES} more lines)" if len(lines) > WIRING_MAX_LINES else ""
    return f"### {f.relative_to(root)}\n" + "\n".join(lines[:WIRING_MAX_LINES]) + more


def wiring_files(m, mods):
    """A build-file module's service registrations and Spring configuration; a directory module's build and manifest
    files. Absolute paths."""
    if m.kind == "build":
        res = ROOT / m.path / "src" / "main" / "resources"
        return [f for g in WIRING_GLOBS for f in sorted(res.glob(g)) if f.is_file()]
    mains = build_mains(mods)
    owned = sorted(f for f in FILES if f.name in WIRING_NAMES and owns(m, f, mains) is not None)
    return [ROOT / f for f in owned[:WIRING_MAX_FILES]]


def wiring(m, mods):
    return "\n\n".join(wiring_file(f, ROOT / m.path) for f in wiring_files(m, mods))


def packages(m):
    return {p for f in m.sources if f.suffix == ".java" for p in JAVA_PACKAGE.findall(read(f))}


def importer(pkgs):
    """Matches an import of a type in one of `pkgs`: `pkg.Type`, `pkg.*` or a static import, never a subpackage's."""
    return re.compile(r"^import\s+(?:static\s+)?(?:" + "|".join(re.escape(p) for p in sorted(pkgs)) + r")\.(?:[A-Z]|\*)", re.M)


def matching_lines(others, keep_file, pattern_of):
    """For each (module, files) in `others`, the lines `pattern_of(module)` matches in those of its files whose text
    `keep_file` accepts: {module id: [(file, line no, line)]}, in order."""
    found = {}
    for o, files in others:
        pattern = pattern_of(o)
        hits = []
        for f in files:
            text = read(f)
            if keep_file and not keep_file(text):
                continue
            hits += [(f, no, line) for no, line in enumerate(text.splitlines(), 1) if pattern.search(line)]
        found[o.id] = hits
    return found


def wired_from(m, mods, types):
    """Lines in other modules that construct this module's types: where it gets plugged in.
    Only files that import one of this module's packages count, so a same-named type elsewhere does not."""
    pkgs = packages(m)
    if not types or not pkgs:
        return ""
    constructs = re.compile(r"\bnew\s+(" + "|".join(sorted(types, key=len, reverse=True)) + r")\b")
    imports = importer(pkgs)
    others = [(o, [f for f in o.sources if f.suffix == ".java"]) for o in mods.values() if o is not m and o.kind == "build"]
    hits = [h for lines in matching_lines(others, imports.search, lambda o: constructs).values() for h in lines]
    return "\n".join(f"- {f}:{no}: {line.strip()[:160]}" for f, no, line in hits[:WIRED_FROM_MAX])


DECLARING = re.compile(r"\b(?:struct|enum|union|typedef|class|interface|type|def|func|fn|function|const|let|var|trait|"
                       r"impl|module|object|record|protocol|extension|namespace|alias|macro)\s+\**\s*([A-Za-z_]\w*)")
DEFINE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)")
CALLED = re.compile(r"([A-Za-z_]\w*)\s*\(")
ASSIGNED = re.compile(r"^\s*(?:export\s+)?([A-Za-z_]\w*)\s*(?::(?!:)|=(?!=))")
TYPEDEF_END = re.compile(r"^\s*\}\s*([A-Za-z_]\w*)\s*;")
NOT_NAMES = {"if", "for", "while", "switch", "return", "catch", "sizeof", "elif", "else", "until", "case", "when",
             "export", "default", "import", "from", "public", "private", "protected", "static", "extern", "inline"}


def skeleton_names(text):
    """The names a generic skeleton declares."""
    names, in_comment = set(), False
    for line in text.splitlines():
        d = DEFINE.match(line)
        if d:
            names.add(d.group(1))
        code, in_comment = code_part(line, in_comment)
        names.update(DECLARING.findall(code))
        for pattern in (CALLED, ASSIGNED, TYPEDEF_END):
            hit = pattern.search(code)
            if hit:
                names.add(hit.group(1))
    return names - NOT_NAMES


def file_names(m):
    return {n for f in m.sources for n in (f.name, f.stem)}


def own_names(m, mods):
    """The names of a directory module that no other directory module also has: those its generic skeletons declare,
    and its files' names with and without extension, each at least REF_NAME_MIN long. Returns (all, file names)."""
    def names(o):
        if o.id not in NAMES:
            declared = set().union(*(skeleton_names(generic_skeleton(read(f))) for f in o.sources
                                     if f.suffix not in DECLARED_EXT))
            NAMES[o.id] = {n for n in declared | file_names(o) if len(n) >= REF_NAME_MIN}
        return NAMES[o.id]

    others = set().union(*(names(o) for o in mods.values() if o.kind == "dir" and o is not m))
    mine = names(m) - others
    return mine, mine & file_names(m)


def word(names):
    return re.compile(r"(?<![\w$])(" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + r")(?![\w$])")


def possible_references(m, mods):
    """Lines of other modules that hold a name only this directory module has: where it may be used or plugged in.
    From each file the REFS_PER_FILE lines holding the most of its names, a file name counting 2 more; then the
    modules by how many of its names their lines hold, one line from each in turn."""
    names, files = own_names(m, mods)
    if not names:
        return ""
    every, by_file = word(names), word(files) if files else None
    others = [(o, o.sources) for o in sorted(mods.values(), key=lambda o: o.path.parts)
              if o is not m and (o.kind == "dir" or by_file)]
    found = matching_lines(others, None, lambda o: every if o.kind == "dir" else by_file)
    ranked = []
    for o, _ in others:
        pattern = every if o.kind == "dir" else by_file
        taken = []
        for f in dict.fromkeys(f for f, _, _ in found[o.id]):
            lines = [(no, line, set(pattern.findall(line))) for g, no, line in found[o.id] if g == f]
            best = sorted(lines, key=lambda t: (-(len(t[2]) + 2 * bool(t[2] & files)), t[0]))[:REFS_PER_FILE]
            taken += [(f, no, line, held) for no, line, held in sorted(best, key=lambda t: t[0])]
        if taken:
            ranked.append((-len(set().union(*(held for *_, held in taken))), len(ranked), taken))
    queues = [taken for *_, taken in sorted(ranked)]
    picked = []
    while len(picked) < WIRED_FROM_MAX and any(queues):
        for q in queues:
            if q and len(picked) < WIRED_FROM_MAX:
                picked.append(q.pop(0))
    return "\n".join(f"- {f}:{no}: {line.strip()[:160]}" for f, no, line, _ in picked)


def pack(m, mods, all_skills):
    types = declared_types(m)
    sections = []
    card = CARDS / f"{m.id}.md"
    if card.exists():
        sections.append("## Current card\n" + strip_stamp(card.read_text()))
    sections.append(module_header(m, mods))
    readme = ROOT / m.path / "README.md"
    if readme.exists():
        sections.append("## README\n" + readme.read_text(errors="replace"))
    sections.append("## Declarations (method bodies dropped)\n" + declarations(m))
    if m.kind == "build":
        links = ("## Constructed in other modules (where it is plugged in)", wired_from(m, mods, types))
    else:
        links = ("## Possible references in other modules (lines that hold a name only this module declares; "
                 "not evidence of a dependency)", possible_references(m, mods))
    for title, body in (links, ("## Wiring", wiring(m, mods))):
        if body:
            sections.append(f"{title}\n{body}")
    if all_skills:
        sections.append("## Project skills\n" + "\n".join(f"- {n}: {skill_description(t)}" for n, t in all_skills.items()))
    mentions = skill_mentions(m, all_skills, types)
    if mentions:
        lines = ["## Lines of project skills that mention this module"]
        for name, ls in sorted(mentions.items(), key=lambda kv: -len(kv[1])):
            lines.append(f"### {name} ({len(ls)} lines)")
            lines += [f"- {l[:240]}" for l in ls[:SKILL_LINES_PER_SKILL]]
            if len(ls) > SKILL_LINES_PER_SKILL:
                lines.append(f"  … {len(ls) - SKILL_LINES_PER_SKILL} more")
        sections.append("\n".join(lines))
    return "\n\n".join(sections) + "\n"


# ---------- cards ----------

def head_sha():
    return git("rev-parse", "--short", "HEAD").strip()


def strip_stamp(text):
    return re.sub(r"^verified-at:.*\n", "", text, flags=re.M)


def read_card(path):
    text = path.read_text()
    meta, body = {}, text
    if text.startswith("---\n") and "\n---" in text[4:]:
        end = text.index("\n---", 4)
        for line in text[4:end].splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
        body = text[end + 4 :]
    return meta, body


def cards():
    return {p.stem: read_card(p) for p in sorted(CARDS.glob("*.md"))} if CARDS.exists() else {}


def card_skills(meta):
    return [s.strip() for s in meta.get("skills", "").strip("[]").split(",") if s.strip()]


def install_card(mid, text):
    text = re.sub(r"^```\w*\n|\n```\s*$", "", text.strip()) + "\n"
    text = strip_stamp(text)
    if not text.startswith("---\n"):
        raise ValueError("the writer's output does not start with frontmatter")
    end = text.index("\n---", 4)
    text = text[:end] + f"\nverified-at: {head_sha()}" + text[end:]
    CARDS.mkdir(parents=True, exist_ok=True)
    (CARDS / f"{mid}.md").write_text(text)
    return text.count("\n")


# ---------- the model call ----------

def ensure_ignores():
    KB.mkdir(parents=True, exist_ok=True)
    gi = KB / ".gitignore"
    if not gi.exists():
        gi.write_text(".packs/\n.runs/\n")


def call_writer(mid, text, model, v):
    """One headless, tool-less call, with the prompt of variant v. No project settings: the writer needs nothing but
    its input."""
    proc = subprocess.run(
        ["claude", "-p", "--model", model, "--tools", "", "--system-prompt", prompt(v),
         "--output-format", "json", "--no-session-persistence", "--strict-mcp-config", "--setting-sources", ""],
        input=text, capture_output=True, text=True, cwd=RUNS)
    if proc.returncode != 0:
        raise RuntimeError(f"claude exited {proc.returncode}: {proc.stderr.strip()[:300]}")
    d = json.loads(proc.stdout)
    if d.get("is_error"):
        raise RuntimeError(str(d.get("result"))[:300])
    u = d.get("usage", {})
    record = {
        "time": datetime.datetime.now().isoformat(timespec="seconds"),
        "module": mid, "model": model,
        "in": u.get("input_tokens", 0), "write": u.get("cache_creation_input_tokens", 0),
        "read": u.get("cache_read_input_tokens", 0), "out": u.get("output_tokens", 0),
        "cost_usd": d.get("total_cost_usd"),
    }
    with open(RUNS / "usage.jsonl", "a") as log:
        log.write(json.dumps(record) + "\n")
    return d["result"]


def write_cards(ids, mods, model):
    ensure_ignores()
    RUNS.mkdir(parents=True, exist_ok=True)
    all_skills = skills()
    failed = []

    def one(mid):
        lines = install_card(mid, call_writer(mid, pack(mods[mid], mods, all_skills), model, variant(mods[mid])))
        return mid, lines

    with concurrent.futures.ThreadPoolExecutor(PARALLEL) as pool:
        futures = {pool.submit(one, mid): mid for mid in ids}
        for fut in concurrent.futures.as_completed(futures):
            mid = futures[fut]
            try:
                _, lines = fut.result()
                print(f"{mid:40} {lines:>3} lines" + ("  OVER THE LIMIT" if lines > CARD_MAX_LINES + 8 else ""))
            except Exception as e:  # one failed card must not lose the others
                failed.append(mid)
                print(f"{mid:40} FAILED: {e}", file=sys.stderr)
    return failed


def changed_modules(sha, mods):
    """A build file counts against the build-file modules it builds; any other path against its owner."""
    mains = build_mains(mods)
    changed = set()
    for p in git("diff", "--name-only", "-z", sha, "HEAD").split("\0"):
        if not p:
            continue
        p = Path(p)
        if p.name in BUILD_FILES:
            built = {m.id for m in mods.values() if m.kind == "build" and m.build == p.parent}
            if built:
                changed |= built
                continue
        m = owner(p, mods, mains)
        if m:
            changed.add(m.id)
    return changed


# ---------- commands ----------

def cmd_modules(mods, _):
    for mid, m in sorted(mods.items(), key=lambda kv: str(kv[1].path)):
        size = sum(file_size(f) for f in m.sources)
        print(f"{mid:40} {str(m.path):60} {len(m.sources):>4} files {size // 1000:>6}k")
    print(f"{len(mods)} modules")


def since_ids(sha, mods):
    """Modules the work since <sha> changed, and modules with no card."""
    return sorted(changed_modules(sha, mods) | (set(mods) - set(cards())))


def cmd_estimate(mods, a):
    ids = since_ids(a.since, mods) if a.since else (a.ids or sorted(mods))
    all_skills = skills()
    total = 0
    for mid in ids:
        tokens = int(len(pack(mods[mid], mods, all_skills)) / chars_per_token(mods[mid])) + WRITER_OVERHEAD
        total += tokens
    out = WRITER_OUTPUT * len(ids)
    if not ids:
        print("0 cards to write")
        return
    print(f"{len(ids)} cards: about {total / 1000:.0f}k input and {out / 1000:.0f}k output tokens, "
          f"in {len(ids)} calls with no tool loop. Measured on a 33-module Java project with sonnet: about $0.004 per 1k input-plus-output.")
    print(f"estimate: ~${(total + out) * 0.0045 / 1000:.2f} on sonnet")


def cmd_write(mods, a):
    if a.since:
        ids = since_ids(a.since, mods)
        gone = sorted(set(cards()) - set(mods))
        for cid in gone:
            (CARDS / f"{cid}.md").unlink()
            print(f"{cid:40} removed: the module no longer exists")
    else:
        ids = sorted(mods) if a.all else a.ids
    unknown = [i for i in ids if i not in mods]
    if unknown:
        sys.exit(f"unknown modules: {', '.join(unknown)}")
    failed = write_cards(ids, mods, a.model) if ids else []
    cmd_index(mods, a)
    if failed:
        sys.exit(f"failed: {', '.join(failed)} - rerun `kb.py write {' '.join(failed)}`")


def cmd_touched(mods, a):
    changed = changed_modules(a.ids[0], mods)
    cs, all_skills = cards(), skills()
    covering = {}
    for mid in sorted(changed):
        # A card's skills are the ones that cover the module. Mentions are a fallback for a module with no card:
        # nearly every skill mentions the central modules, so they over-select.
        found = card_skills(cs[mid][0]) if mid in cs else skill_mentions(mods[mid], all_skills, declared_types(mods[mid]))
        for s in found:
            covering.setdefault(s, set()).add(mid)
    print("modules: " + (", ".join(sorted(changed)) or "-"))
    print("skills:")
    for s in sorted(covering):
        if s in all_skills:
            print(f"  {s} (.claude/skills/{s}/SKILL.md) - {', '.join(sorted(covering[s]))}")


IDENTIFIER = re.compile(r"^([A-Za-z_][\w$]*)(?:(?:\.|#|::)([A-Za-z_][\w$]*))?(?:\(\))?$")
FILE_NAME = re.compile(r"^\w[\w.-]*\.[A-Za-z0-9]+$")
PATH_LIKE = re.compile(r"^[\w.-]+/[\w./-]+$")


def declaration_map(mods):
    """Every name the readers declare anywhere in the project, with the files that declare it and, per file, the text
    a member is looked up in: a generic skeleton's code part, or a .java or .proto file's text."""
    declared, member_text = {}, {}
    for m in mods.values():
        for f in read_files(m):
            text = read(f)
            if f.suffix in DECLARED_EXT:
                names, member_text[f] = set(TYPE_DECL.findall(text)), text
            else:
                sk = generic_skeleton(text)
                names, in_comment, codes = skeleton_names(sk), False, []
                for line in sk.splitlines():
                    code, in_comment = code_part(line, in_comment)
                    codes.append(code)
                member_text[f] = "\n".join(codes)
            for n in names:
                declared.setdefault(n, []).append(f)
    return declared, member_text


def dead_any_code(m, mods, body, declared, member_text, all_skills):
    """The names in backticks of a card for code of any language that the code does not have."""
    own_files = {f.name for f in m.sources} | {f.name for f in wiring_files(m, mods)}
    dead = set()
    for name in re.findall(r"`([^`\n]+)`", body):
        if "/" in name:
            if PATH_LIKE.match(name) and not (ROOT / name).exists():
                dead.add(name)
        elif name in all_skills or name in mods or name in own_files:
            continue
        elif IDENTIFIER.match(name):
            first, member = IDENTIFIER.match(name).groups()
            files = declared.get(first)
            if not files or (member and not any(re.search(rf"(?<![\w$]){re.escape(member)}(?![\w$])", member_text[f])
                                                for f in files)):
                dead.add(name)
        elif FILE_NAME.match(name):
            dead.add(name)
    return dead


def dead_java(m, body, all_types, type_files):
    symbol = re.compile(r"`([A-Z]\w*)(?:[.#](\w+))?(?:\(\))?`")
    pathlike = re.compile(r"`([\w.-]+/[\w./-]+)`")
    dead = set()
    for t, member in symbol.findall(body):
        if t not in all_types:
            dead.add(t)
        elif member and not any(re.search(rf"\b{re.escape(member)}\b", read(f)) for f in type_files[t]):
            dead.add(f"{t}.{member}")
    return dead | {p for p in pathlike.findall(body) if not (ROOT / p).exists()}


def java_types(ms):
    all_types, type_files = set(), {}
    for m in ms:
        for f in m.sources:
            if f.suffix in DECLARED_EXT:
                for t in TYPE_DECL.findall(read(f)):
                    all_types.add(t)
                    type_files.setdefault(t, []).append(f)
    return all_types, type_files


def cmd_status(mods, a):
    """With ids, only those modules are reported and counted."""
    unknown = [i for i in a.ids if i not in mods]
    if unknown:
        sys.exit(f"unknown modules: {', '.join(unknown)}")
    cs, all_skills = cards(), skills()
    all_types, type_files = java_types([m for m in mods.values() if m.kind == "build"])
    declared = member_text = None
    in_work = changed_modules(a.since, mods) if a.since else set()
    problems = 0
    print(f"{'module':40} {'changed':>8}  notes")
    for mid, m in sorted(mods.items()):
        if a.ids and mid not in a.ids:
            continue
        if mid not in cs:
            print(f"{mid:40} {'':>8}  no card")
            problems += 1
            continue
        meta, body = cs[mid]
        notes, changed = [], ""
        sha = meta.get("verified-at", "")
        try:
            stat = git("diff", "--numstat", sha, "HEAD", "--", *pathspecs(m, mods))
            changed = str(sum(int(x) + int(y) for x, y, _ in (l.split("\t") for l in stat.splitlines()) if x != "-"))
        except subprocess.CalledProcessError:
            notes.append(f"unknown verified-at '{sha}'")
        if mid in in_work and changed not in ("", "0"):
            notes.append("stale: the work changed it after the card was written")
        if variant(m) == "java":
            types, files = (all_types, type_files) if m.kind == "build" else java_types(
                [o for o in mods.values() if o.kind == "build"] + [m])
            dead = dead_java(m, body, types, files)
        else:
            if declared is None:
                declared, member_text = declaration_map(mods)
            dead = dead_any_code(m, mods, body, declared, member_text, all_skills)
        if dead:
            notes.append("dead: " + ", ".join(sorted(dead)))
        lines = (CARDS / f"{mid}.md").read_text().count("\n")
        if lines > CARD_MAX_LINES + 8:
            notes.append(f"{lines} lines")
        problems += bool(notes)
        print(f"{mid:40} {changed:>8}  {'; '.join(notes)}")
    for cid in [] if a.ids else sorted(set(cs) - set(mods)):
        print(f"{cid:40} {'':>8}  card for a module that no longer exists")
        problems += 1
    print("clean" if not problems else f"{problems} modules need attention")


def cmd_index(mods, _):
    cs, all_skills = cards(), skills()
    out = [
        "# Knowledge base",
        "",
        "Generated by `kb.py index` from the cards. Do not edit: edit a card, or rerun `kb.py write`.",
        "A card says what exists and where; a skill says why and how. Neither is a source: the code is.",
        "",
    ]
    if all_skills:
        out += ["## Project skills", ""]
        out += [f"- **{n}** (`.claude/skills/{n}/SKILL.md`): {skill_description(t)}" for n, t in all_skills.items()]
        out.append("")
    groups = {}
    for m in sorted(mods.values(), key=lambda m: str(m.path)):
        groups.setdefault(m.path.parts[0] if m.path.parts else ".", []).append(m)
    for g, ms in groups.items():
        out += [f"## {g}", ""]
        for m in ms:
            meta = cs.get(m.id, ({}, ""))[0]
            if m.id in cs:
                sk = ", ".join(card_skills(meta))
                out.append(f"- **{m.id}** [card](cards/{m.id}.md): {meta.get('summary', '')}" + (f" Skills: {sk}." if sk else ""))
            else:
                out.append(f"- **{m.id}** `{m.path}`: no card yet.")
        out.append("")
    KB.mkdir(parents=True, exist_ok=True)
    (KB / "index.md").write_text("\n".join(out))
    print(f"wrote {(KB / 'index.md').relative_to(ROOT)}")


def cmd_usage(_, a):
    log = RUNS / "usage.jsonl"
    rows = [json.loads(l) for l in log.read_text().splitlines()] if log.exists() else []
    if a.since:
        since = datetime.datetime.fromisoformat(a.since.replace(" ", "T"))
        if since.tzinfo:
            since = since.astimezone().replace(tzinfo=None)
        rows = [r for r in rows if datetime.datetime.fromisoformat(r["time"]) >= since]

    def k(n):
        return f"{n / 1000:.3g}k" if n >= 1000 else str(n)

    tot = {f: sum(r[f] for r in rows) for f in ("out", "write", "read", "in")}
    cost = sum(r["cost_usd"] or 0 for r in rows)
    models = ", ".join(sorted({r["model"] for r in rows})) or "-"
    print(f"calls: {len(rows)}")
    print(f"model: {models}")
    print(f"cost: ${cost:.2f}")
    print(f"out {k(tot['out'])} · write {k(tot['write'])} · read {k(tot['read'])} · in {k(tot['in'])}")


def cmd_pack(mods, a):
    PACKS.mkdir(parents=True, exist_ok=True)
    all_skills = skills()
    for mid in a.ids:
        text = pack(mods[mid], mods, all_skills)
        (PACKS / f"{mid}.md").write_text(text)
        tokens = int(len(text) / chars_per_token(mods[mid]))
        print(f"{mid:40} ~{tokens:>6} tokens -> {(PACKS / f'{mid}.md').relative_to(ROOT)}")


COMMANDS = {"modules": cmd_modules, "estimate": cmd_estimate, "write": cmd_write, "touched": cmd_touched,
            "status": cmd_status, "index": cmd_index, "usage": cmd_usage, "pack": cmd_pack}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=COMMANDS)
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--root", default=".")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--since", help="write, estimate, status: a commit; usage: a local time, YYYY-MM-DDTHH:MM:SS")
    ap.add_argument("--model", default="sonnet")
    a = ap.parse_args()
    set_root(a.root)
    mods = modules()
    if not mods and a.cmd not in ("usage",):
        sys.exit("no source found: kb.py found no build-file module and no tracked source file; "
                 "an include line in fondue/kb/parts.txt can name one (protocol/kb.md)")
    COMMANDS[a.cmd](mods, a)


if __name__ == "__main__":
    main()
