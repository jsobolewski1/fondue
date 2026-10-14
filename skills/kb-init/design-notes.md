# kb-init - design notes

For the User changing the knowledge base or its tooling. Roles do not read this file.

## Why a map, and not a vector database
The failures it targets: an agent rebuilds something that exists under another name, and treats existing code as fixed and builds around it. A vector search over code chunks gives no sign of what it missed, which is exactly how the first failure happens. A small text index, read whole, cannot miss a module. Cards are text in git, so grep finds them, a diff reviews them, and `kb.py status` checks them against the code without spending tokens.

## Why the cost stays low
A tool that lets an agent explore the code to describe it pays for its growing context on every call. An earlier tool spent two full sessions on a project a fifth the size of the one measured below. Here a script does all the crawling (declarations without bodies, construction sites, wiring files, skill lines) and the model makes one tool-less call per card. The context never grows.

Measured on a sample Java project, 2026-10-06: 33 Maven modules, 373 main Java files, 1.6M chars. Sonnet, API-equivalent cost.

| What | Tokens | Cost |
|---|---|---|
| Card, small module (16k-char pack) | ~7k in, 1.1k out | $0.07 |
| Card, large module (52-65k-char pack) | ~25k in, 1.7-1.9k out | $0.14-0.15 |
| All cards (estimated from the packs) | ~330k in, ~50k out | ~$1.7 |
| `index.md`, read by every Architect | 4.7k | |
| One card | ~1.9k | |

- **Chars per token.** Java skeletons tokenize at about 2.5 chars per token and card prose at 2.6-2.9. The common rule of 4 undercounts code by about 1.6×. `kb.py estimate` uses 2.5.
- **Overhead.** A `claude -p` call run from a project loads that project's CLAUDE.md and the user's memory: 8.6k tokens a call on that project. `--setting-sources ""` cuts it to about 0.8k, and `kb.py` passes it.

## Measured on code of any language
Measured 2026-10-14 on clones of five projects, Sonnet, API-equivalent cost: every directory module's card (`kb.py write --all`), and on the Java project with a Vue/JavaScript web part only its five directory modules.

| Project | Cards | Input tokens | Output tokens | Cost | A card: smallest, largest, mean | Chars per token |
|---|---|---|---|---|---|---|
| C project | 12 | 143k | 12.6k | $0.64 | $0.019, $0.142, $0.054 | 2.12 |
| Shell project | 2 | 14.3k | 1.4k | $0.06 | $0.030, $0.033, $0.031 | 2.10 |
| fondue | 2 | 7.9k | 1.1k | $0.03 | $0.010, $0.025, $0.017 | 2.39 |
| Public TypeScript project | 14 | 251k | 13.7k | $1.08 | $0.010, $0.248, $0.077 | 2.17 |
| Vue/JavaScript web part and its scripts | 5 | 59.7k | 4.7k | $0.26 | $0.022, $0.123, $0.053 | 2.28 |
| All | 35 | 476k | 33.6k | $2.08 | mean $0.060 | |

- **Chars per token.** Calibrated before those writes on the sample Java project's three directory modules (shell scripts, Dockerfiles, Python, a few Java and `.proto` files): 104,557 chars of pack for 49,892 input tokens, less 1,800 a call: 2.35, so `kb.py estimate` uses 2.4 for a card of any code. The projects above came out at 2.1-2.4, so the estimate read 0-10% low on each.
- **The one card over $0.20** is a module of the TypeScript project whose files include one 90 KB file of type declarations at the top level. The reader keeps declarations, so it keeps 83 KB of it. A directory over the budget splits, but one file cannot.
- **Dead names after the first write**, fixed by hand as step 5 says: C project 89, TypeScript project 41, the web part 14, shell project and fondue none. Most are library and tool names in backticks, C build options and typedefs the reader does not see declared, and import paths written as the import does (`../../context`). A path relative to the module's own directory is accepted, because the pack names each file that way.

## What changed during the pilot, and why
- **The index-writer call was dropped.** The first design wrote the index in one call over every module's slim declarations (~96k tokens, $0.46) so it could be built before any card. Once every card is written anyway, its frontmatter summary is the index entry, and a script concatenates them for free.
- **Construction sites from other modules were added to the pack.** Without them, extension points came out right but incomplete: "add it to the composite's list", when the list lives in another module's factory. With them, cards name the file that wires a new one in. Only files that import the module's packages count, because a same-named type elsewhere (`Entry`, `Bytes`) made noise.
- **Private members stay in the pack.** Filtering to public saved little (~20k vs ~23k tokens of method signatures), and a non-public helper is exactly what should be promoted instead of rebuilt.
- **`touched` takes skills from cards, not from mentions.** Nearly every skill mentions the central modules, so a mention-based list sends the Handover Writer to check every skill.

## Known limits
- **Languages.** Java and `.proto` have readers of their own. Every other language goes through one reader that keeps declarations by indentation and drops bodies. It cannot see what indentation does not show: a C `typedef` on one line, a function-pointer type, a build option a CMake file declares. And it keeps a file that is all declarations nearly whole, so one large file of types makes an expensive card. `- <file>` in `parts.txt` leaves such a file out.
- **Module discovery.** Maven modules, and Gradle modules without their dependencies, as the build lays them out. Every other source forms directory modules: the repository root and each build-file module's directory split into their first-level directories, a directory over 250k bytes of source splits one level down, and a subdirectory under 5k there stays with its parent. A single file is never split.
- **Links.** Only build-file modules have dependency lines, from Maven. A directory module has none: its pack carries its build and manifest files, and lines of other modules that hold a name only it has, as possible references. A shared word can make such a line a coincidence, so the writer may not state a boundary from it.
- **Markdown** is not a source by default, so a project's documentation gets no card. `+ *.md` in `parts.txt` includes it.
- **Large modules.** A module of 80+ files fits in 60 lines, but its Offers section starts to read like a type list. `parts.txt` gives a directory inside a module a card of its own; a single file cannot be split.
