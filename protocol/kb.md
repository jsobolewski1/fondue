# kb - the project's knowledge base

The knowledge base maps what a codebase already has, so that a role about to design or build finds it before building it again. It lives in the project at `fondue/kb/`, outside any spec, and outlives every spec. The `kb-init` skill creates it. A spec's handover and a hunt's fix keep it current.

Read this file when you write or update the knowledge base. A role that only reads it needs the engine's Knowledge base section, not this file.

## What it holds, and what it does not
* **index.md** - one entry per module: a summary of what it offers, with other names for the same capability, and the skills that cover it. Above them, every project skill with its description. A script generates it from the cards, so it is never edited by hand. It stays small enough to read whole, about 5k tokens for 30-40 modules. Why read it whole: you cannot search for something you do not know exists.
* **cards/<module>.md** - one per module, at most 60 lines: purpose, what it offers, its extension points with the file that wires a new one in, what not to rebuild, its boundaries, and the skills to read next. `card-writer.md` next to this file is the card's shape and rules. It has two variants, marked line by line: a module whose declarations come only from Java and `.proto` gets the Java wording, any other module the wording for any code.
* **parts.txt** - optional, written by the User, one line each:
  - `<card id> <directory>`: a module too broad for one card gets a card per directory inside it, e.g. a package directory. Each part is a module to every command; the module's own card keeps what is left, and disappears when nothing is. A build file depends on the whole module, so a part's users are the modules that import its packages, and the parts of one module use each other the same way. Why not split the module instead: how the code is built is the project's decision, not the knowledge base's.
  - `- <pattern>`: what the pattern matches is not source, e.g. `- benchmarks` or `- *.min.js`. A directory left with no source has no module.
  - `+ <pattern>`: what the pattern matches is source, whatever its extension and wherever it sits, e.g. `+ *.zig` for a language `kb.py` does not list. `-` wins over `+`.

  A pattern is a path relative to the project root, a directory and everything under it, or a glob over the whole path whose `*` also crosses `/`. Neither line applies under `fondue/` or under a build-file module's `src/main`, which stays that module's. `#` starts a comment.

The split with project skills is **one fact, one home.** A card says what exists and where. A skill says why and how. A card that starts explaining has content that belongs in a skill.

A card is never an inventory: signatures, file lists and call sites are what grep and the code give on demand. That keeps it small, and it keeps it from going stale on every change.

**A card is where to look, never a source.** A research FACT cites the code, not a card. Each card records `verified-at: <commit>`, and `kb.py status` shows what changed under it since.

## Tools
`kb/kb.py` next to this file, run from the project root with `python3`. Every command but `write` is mechanical and spends no tokens.

| command | what it does |
|---|---|
| `modules` | lists the modules, each with its file count and its size in thousands of bytes. A **build-file module** is a directory with a Maven or Gradle build file and sources under `src/main`. A **directory module** holds the source no build file claims: the repository root and each build-file module's directory split into their first-level directories, one module each, with the files directly in them as a module of their own; a directory over 250k bytes of source splits the same way one level down, and there a subdirectory under 5k stays with its parent. Source is a code file by extension or name, outside test, vendored, generated and hidden directories and `fondue/`. Then the parts `parts.txt` names |
| `estimate [<id>... \| --since <sha>]` | the tokens and cost of writing those cards (default: all), before spending them |
| `write <id>... \| --all` | writes cards, then the index |
| `write --since <sha>` | writes the cards of modules changed since `<sha>` and of modules with no card, removes the cards of modules that are gone, then the index |
| `touched <sha>` | the modules changed since `<sha>`, and the project skills that cover them |
| `status [<id>...] [--since <sha>]` | every card against the code, or only the cards of the modules named: lines changed since `verified-at`, names in backticks the code no longer has, missing cards, cards over the limit. In a card of a module read as Java, a name is a capitalised type; in a card of any other code, every name in backticks is checked, lowercase too: a function, variable or type the readers declare somewhere in the project, a file of the module by its name, or a path from the repository root or from the module's directory. With `--since`, a card for a module the work changed that is older than the change is a problem too. It ends `clean` or with a count. Drift outside the work is a number in the `changed` column, not a problem |
| `index` | regenerates `index.md` |
| `usage [--since <time>]` | the calls `write` made since a local time as `date +%Y-%m-%dT%H:%M:%S` prints it: their count, model and cost, and as its last line their tokens in `stats.md` form |

**How `write` keeps the cost down.** A script packs each module's input: its declarations with method bodies dropped, the lines in other modules that construct its types (for a directory module, the lines that hold a name only it has, as possible references), its wiring files, and the skill lines that mention it. One `claude -p` call per card then writes it, with no tools and no project settings. That makes one call per card, with no agent loop whose context grows on every step. A card that exists goes into the call too, so the writer changes only what the code changed. Measured on a 33-module Java project: ~$1.7 for all cards on Sonnet, $0.07-0.15 per card. Measured on 35 directory modules of C, shell, Python, Vue/JavaScript and TypeScript code: $2.09 on Sonnet, $0.01-0.15 a card but one, $0.25 for a module that holds a 90 KB file of type declarations. `write` takes `--model` (default `sonnet`), and needs the `claude` CLI on the `PATH`, whichever agent runs the role.

What `write` reads: Java and `.proto` declarations through their own readers, and every other source, in any language, through a reader that keeps declarations by indentation and drops bodies. Maven dependencies, and Gradle modules without their dependencies. A directory module has no dependency lines: the pack carries its build and manifest files (`package.json`, `Cargo.toml`, `pyproject.toml`, ...) as its wiring, and the lines of other modules that hold a name only it declares or one of its file names, labelled as possible references. They are where it may be used, not evidence of a dependency.

## Keeping it current
* **A spec** updates it at handover, before anything else (spec: handover). **A hunt** updates it in its fix (hunt: fix).
* **Whoever updates it**, with `<sha>` the commit the work started from, i.e. the parent of its first commit:
  - runs `kb.py write --since <sha>`;
  - runs `kb.py status --since <sha>` until it is `clean`, editing a card by hand where a name is dead;
  - reads `kb.py touched <sha>` for the project skills to check.
  - When `kb.py touched` lists no skill and `write` wrote no card, there is nothing to update.
* **Every card is regenerated from the code,** so a hand edit to a card survives only as long as the writer keeps it. A fact worth keeping by hand belongs in a skill.
* **A project skill** describes the code as it is now. A section the work made wrong is rewritten in place, with no history and no changelog.
* **Changes outside fondue** show in `kb.py status`. Run `kb.py write --since <sha>` for them whenever you choose.

## Commits
`fondue/kb/` is project documentation, not a spec. It is committed with the documents that update it, never with a spec folder. `.packs/` and `.runs/` are scratch, and `write` creates the `.gitignore` that keeps them out. A project that ignores `fondue/kb/` (`git check-ignore -q fondue/kb` succeeds) keeps its knowledge base local: nobody stages it, and a review of an update names the changed cards as files next to the commit range of the skills.
