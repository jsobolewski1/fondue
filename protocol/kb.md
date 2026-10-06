# kb - the project's knowledge base

The knowledge base maps what a codebase already has, so that a role about to design or build finds it before building it again. It lives in the project at `fondue/kb/`, outside any spec, and outlives every spec. The `kb-init` skill creates it. A spec's handover and a hunt's fix keep it current.

Read this file when you write or update the knowledge base. A role that only reads it needs the engine's Knowledge base section, not this file.

## What it holds, and what it does not
* **index.md** - one entry per module: a summary of what it offers, with other names for the same capability, and the skills that cover it. Above them, every project skill with its description. A script generates it from the cards, so it is never edited by hand. It stays small enough to read whole, about 5k tokens for 30-40 modules. Why read it whole: you cannot search for something you do not know exists.
* **cards/<module>.md** - one per module, at most 60 lines: purpose, what it offers, its extension points with the file that wires a new one in, what not to rebuild, its boundaries, and the skills to read next. `card-writer.md` next to this file is the card's shape and rules.
* **parts.txt** - optional, written by the User: a module too broad for one card gets a card per package directory, one `<card id> <directory>` per line. Each part is a module to every command; the module's own card keeps what is left, and disappears when nothing is. A build file depends on the whole module, so a part's users are the modules that import its packages, and the parts of one module use each other the same way. Why not split the module instead: how the code is built is the project's decision, not the knowledge base's.

The split with project skills is **one fact, one home.** A card says what exists and where. A skill says why and how. A card that starts explaining has content that belongs in a skill.

A card is never an inventory: signatures, file lists and call sites are what grep and the code give on demand. That keeps it small, and it keeps it from going stale on every change.

**A card is where to look, never a source.** A research FACT cites the code, not a card. Each card records `verified-at: <commit>`, and `kb.py status` shows what changed under it since.

## Tools
`kb/kb.py` next to this file, run from the project root with `python3`. Every command but `write` is mechanical and spends no tokens.

| command | what it does |
|---|---|
| `modules` | lists the modules: a directory with a build file and sources under `src/main`, and the parts `parts.txt` names |
| `estimate [<id>... \| --since <sha>]` | the tokens and cost of writing those cards (default: all), before spending them |
| `write <id>... \| --all` | writes cards, then the index |
| `write --since <sha>` | writes the cards of modules changed since `<sha>` and of modules with no card, removes the cards of modules that are gone, then the index |
| `touched <sha>` | the modules changed since `<sha>`, and the project skills that cover them |
| `status [--since <sha>]` | every card against the code: lines changed since `verified-at`, names in backticks the code no longer has, missing cards, cards over the limit. With `--since`, a card for a module the work changed that is older than the change is a problem too. It ends `clean` or with a count. Drift outside the work is a number in the `changed` column, not a problem |
| `index` | regenerates `index.md` |
| `usage [--since <time>]` | the calls `write` made since a local time as `date +%Y-%m-%dT%H:%M:%S` prints it: their count, model and cost, and as its last line their tokens in `stats.md` form |

**How `write` keeps the cost down.** A script packs each module's input: its declarations with method bodies dropped, the lines in other modules that construct its types, its wiring files, and the skill lines that mention it. One `claude -p` call per card then writes it, with no tools and no project settings. That makes one call per card, with no agent loop whose context grows on every step. A card that exists goes into the call too, so the writer changes only what the code changed. Measured on a 33-module Java project: ~$1.7 for all cards on Sonnet, $0.07-0.15 per card. `write` takes `--model` (default `sonnet`), and needs the `claude` CLI on the `PATH`, whichever agent runs the role.

What `write` reads: Java and `.proto` declarations, Maven dependencies, and Gradle modules without their dependencies. A source it cannot read is listed by name in the input. Kotlin and other languages are not read yet.

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
