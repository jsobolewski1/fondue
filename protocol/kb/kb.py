#!/usr/bin/env python3
"""The knowledge base's tooling (protocol/kb.md). Run from the project root, or pass --root.

  kb.py modules                       list the source modules and their size
  kb.py estimate [<id>... | --since <sha>]  what writing those cards (default: all) costs, before spending it
  kb.py write <id>... | --all         write cards: pack each module, one tool-less model call each, then the index
  kb.py write --since <sha>           write the cards of modules changed since <sha>, and of modules with no card
  kb.py touched <sha>                 modules changed since <sha>, and the project skills that cover them
  kb.py status [--since <sha>]        every card against the code: changes since verified-at, dead symbols;
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
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
CARD_WRITER = HERE / "card-writer.md"

BUILD_FILES = ("pom.xml", "build.gradle", "build.gradle.kts")
DECLARED_EXT = {".java", ".proto"}
WIRING_GLOBS = ("META-INF/services/*", "application*.yml", "application*.yaml", "application*.properties")
WIRING_MAX_LINES = 60
SKILL_LINES_PER_SKILL = 15
WIRED_FROM_MAX = 40
HEADER_MAX = 220
CARD_MAX_LINES = 60
CHARS_PER_TOKEN = 2.5     # measured on Java skeletons; chars/4 undercounts code by about 1.6x
WRITER_OVERHEAD = 1800    # system prompt and harness per call, in tokens
WRITER_OUTPUT = 1500      # tokens a card takes to write
PARALLEL = 6

ROOT = KB = CARDS = PACKS = RUNS = None


def set_root(root):
    global ROOT, KB, CARDS, PACKS, RUNS
    ROOT = Path(root).resolve()
    KB = ROOT / "fondue" / "kb"
    CARDS, PACKS, RUNS = KB / "cards", KB / ".packs", KB / ".runs"


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def read(path):
    return (ROOT / path).read_text(errors="replace")


# ---------- modules ----------

class Module:
    def __init__(self, path, mid, deps, sources):
        self.path, self.id, self.deps, self.sources = path, mid, deps, sources
        self.dependents = []


def pom_info(pom):
    root = ET.parse(ROOT / pom).getroot()
    ns = root.tag[: root.tag.index("}") + 1] if root.tag.startswith("{") else ""
    aid = root.find(f"{ns}artifactId")
    deps = []
    for d in root.findall(f"{ns}dependencies/{ns}dependency"):
        a, s = d.find(f"{ns}artifactId"), d.find(f"{ns}scope")
        deps.append((a.text.strip(), s.text.strip() if s is not None else "compile"))
    return (aid.text.strip() if aid is not None else pom.parent.name), deps


def modules():
    """A module is a directory with a build file and tracked files under src/main."""
    files = [Path(p) for p in git("ls-files").splitlines()]
    found = {}
    for d in sorted({f.parent for f in files if f.name in BUILD_FILES}):
        main = d / "src" / "main"
        srcs = [f for f in files if main in f.parents]
        if not srcs:
            continue
        pom = d / "pom.xml"
        mid, deps = pom_info(pom) if pom in files else (d.name, [])
        found[mid] = Module(d, mid, deps, srcs)
    for m in found.values():
        for aid, scope in m.deps:
            if aid in found and scope != "test":
                found[aid].dependents.append(m.id)
    return found


def module_of(path, mods):
    best = None
    for m in mods.values():
        if m.path in path.parents and (best is None or len(m.path.parts) > len(best.path.parts)):
            best = m
    return best


# ---------- declarations without bodies ----------

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


def declarations(m):
    parts = []
    for f in sorted(m.sources):
        if f.suffix == ".java":
            body = java_skeleton(read(f))
        elif f.suffix == ".proto":
            body = proto_skeleton(read(f))
        else:
            continue
        if body.strip():
            parts.append(f"### {f.relative_to(m.path)}\n{body}")
    other = sorted(str(f.relative_to(m.path)) for f in m.sources if f.suffix in (".kt", ".scala", ".groovy"))
    if other:
        parts.append("### Sources this tool cannot read declarations from (names only)\n" + "\n".join(other))
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
    terms = {m.id, m.path.name} | {t for t in types if len(t) >= 6}
    pattern = re.compile(r"\b(" + "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)) + r")\b")
    hits = {}
    for name, text in all_skills.items():
        lines = [l.strip() for l in text.splitlines() if pattern.search(l)]
        if lines:
            hits[name] = lines
    return hits


def module_header(m, mods):
    internal = sorted(a for a, s in m.deps if a in mods and s != "test")
    external = sorted(a for a, s in m.deps if a not in mods and s != "test")
    return "\n".join([
        f"# Module {m.id}",
        f"path: {m.path}",
        f"depends on (project): {', '.join(internal) or '-'}",
        f"depends on (external): {', '.join(external) or '-'}",
        f"depended on by: {', '.join(sorted(m.dependents)) or '-'}",
    ])


def wiring(m):
    res = ROOT / m.path / "src" / "main" / "resources"
    parts = []
    for g in WIRING_GLOBS:
        for f in sorted(res.glob(g)):
            if f.is_file():
                lines = [l for l in f.read_text(errors="replace").splitlines() if l.strip() and not l.strip().startswith("#")]
                more = f"\n… ({len(lines) - WIRING_MAX_LINES} more lines)" if len(lines) > WIRING_MAX_LINES else ""
                parts.append(f"### {f.relative_to(ROOT / m.path)}\n" + "\n".join(lines[:WIRING_MAX_LINES]) + more)
    return "\n\n".join(parts)


def wired_from(m, mods, types):
    """Lines in other modules that construct this module's types: where it gets plugged in.
    Only files that import one of this module's packages count, so a same-named type elsewhere does not."""
    pkgs = set()
    for f in m.sources:
        if f.suffix == ".java":
            pm = re.search(r"^package\s+([\w.]+)", read(f), re.M)
            if pm:
                pkgs.add(pm.group(1))
    if not types or not pkgs:
        return ""
    constructs = re.compile(r"\bnew\s+(" + "|".join(sorted(types, key=len, reverse=True)) + r")\b")
    imports = re.compile(r"^import\s+(" + "|".join(re.escape(p) for p in pkgs) + r")\.", re.M)
    hits = []
    for other in mods.values():
        if other is m:
            continue
        for f in other.sources:
            if f.suffix != ".java":
                continue
            text = read(f)
            if not imports.search(text):
                continue
            hits += [f"- {f}:{no}: {line.strip()[:160]}" for no, line in enumerate(text.splitlines(), 1) if constructs.search(line)]
    return "\n".join(hits[:WIRED_FROM_MAX])


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
    for title, body in (("## Constructed in other modules (where it is plugged in)", wired_from(m, mods, types)),
                        ("## Wiring", wiring(m))):
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


def call_writer(mid, text, model):
    """One headless, tool-less call. No project settings: the writer needs nothing but its input."""
    proc = subprocess.run(
        ["claude", "-p", "--model", model, "--tools", "", "--system-prompt", CARD_WRITER.read_text(),
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
        lines = install_card(mid, call_writer(mid, pack(mods[mid], mods, all_skills), model))
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
    changed = set()
    for p in git("diff", "--name-only", sha, "HEAD").splitlines():
        m = module_of(Path(p), mods)
        if m and (m.path / "src" / "main" in Path(p).parents or Path(p).name in BUILD_FILES):
            changed.add(m.id)
    return changed


# ---------- commands ----------

def cmd_modules(mods, _):
    for mid, m in sorted(mods.items(), key=lambda kv: str(kv[1].path)):
        print(f"{mid:40} {str(m.path):60} {len(m.sources):>4} files")
    print(f"{len(mods)} modules")


def since_ids(sha, mods):
    """Modules the work since <sha> changed, and modules with no card."""
    return sorted(changed_modules(sha, mods) | (set(mods) - set(cards())))


def cmd_estimate(mods, a):
    ids = since_ids(a.since, mods) if a.since else (a.ids or sorted(mods))
    all_skills = skills()
    total = 0
    for mid in ids:
        tokens = int(len(pack(mods[mid], mods, all_skills)) / CHARS_PER_TOKEN) + WRITER_OVERHEAD
        total += tokens
    out = WRITER_OUTPUT * len(ids)
    if not ids:
        print("0 cards to write")
        return
    print(f"{len(ids)} cards: about {total / 1000:.0f}k input and {out / 1000:.0f}k output tokens, "
          f"in {len(ids)} calls with no tool loop. Measured on tachornis with sonnet: about $0.004 per 1k input-plus-output.")
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


def cmd_status(mods, a):
    cs = cards()
    all_types, type_files = set(), {}
    for m in mods.values():
        for f in m.sources:
            if f.suffix in DECLARED_EXT:
                for t in TYPE_DECL.findall(read(f)):
                    all_types.add(t)
                    type_files.setdefault(t, []).append(f)
    symbol = re.compile(r"`([A-Z]\w*)(?:[.#](\w+))?(?:\(\))?`")
    pathlike = re.compile(r"`([\w.-]+/[\w./-]+)`")
    in_work = changed_modules(a.since, mods) if a.since else set()
    problems = 0
    print(f"{'module':40} {'changed':>8}  notes")
    for mid, m in sorted(mods.items()):
        if mid not in cs:
            print(f"{mid:40} {'':>8}  no card")
            problems += 1
            continue
        meta, body = cs[mid]
        notes, changed = [], ""
        sha = meta.get("verified-at", "")
        try:
            stat = git("diff", "--numstat", sha, "HEAD", "--", str(m.path / "src" / "main"))
            changed = str(sum(int(x) + int(y) for x, y, _ in (l.split("\t") for l in stat.splitlines()) if x != "-"))
        except subprocess.CalledProcessError:
            notes.append(f"unknown verified-at '{sha}'")
        if mid in in_work and changed not in ("", "0"):
            notes.append("stale: the work changed it after the card was written")
        dead = set()
        for t, member in symbol.findall(body):
            if t not in all_types:
                dead.add(t)
            elif member and not any(re.search(rf"\b{re.escape(member)}\b", read(f)) for f in type_files[t]):
                dead.add(f"{t}.{member}")
        dead |= {p for p in pathlike.findall(body) if not (ROOT / p).exists()}
        if dead:
            notes.append("dead: " + ", ".join(sorted(dead)))
        lines = (CARDS / f"{mid}.md").read_text().count("\n")
        if lines > CARD_MAX_LINES + 8:
            notes.append(f"{lines} lines")
        problems += bool(notes)
        print(f"{mid:40} {changed:>8}  {'; '.join(notes)}")
    for cid in sorted(set(cs) - set(mods)):
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
        print(f"{mid:40} ~{int(len(text) / CHARS_PER_TOKEN):>6} tokens -> {(PACKS / f'{mid}.md').relative_to(ROOT)}")


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
        sys.exit("no modules found: kb.py reads Maven and Gradle projects with sources under <module>/src/main")
    COMMANDS[a.cmd](mods, a)


if __name__ == "__main__":
    main()
