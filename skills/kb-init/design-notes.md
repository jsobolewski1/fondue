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
Measured 2026-10-15 on clones of five projects, Sonnet, API-equivalent cost: every directory module's card (`kb.py write --all`), and on the Java project with a Vue/JavaScript web part only its five directory modules.

| Project | Cards | Input tokens | Output tokens | Cost | A card: smallest, largest, mean | Chars per token |
|---|---|---|---|---|---|---|
| C project | 12 | 144k | 12.2k | $0.67 | $0.018, $0.146, $0.056 | 2.09 |
| Shell project | 2 | 14.6k | 1.3k | $0.06 | $0.029, $0.033, $0.031 | 2.04 |
| fondue | 2 | 8.2k | 1.2k | $0.03 | $0.009, $0.025, $0.017 | 2.24 |
| Public TypeScript project | 14 | 253k | 13.0k | $1.07 | $0.009, $0.249, $0.077 | 2.15 |
| Vue/JavaScript web part and its scripts | 5 | 60.5k | 3.9k | $0.26 | $0.021, $0.121, $0.051 | 2.25 |
| All | 35 | 481k | 31.6k | $2.09 | mean $0.060 | |

- **Chars per token.** Calibrated before those writes on the sample Java project's three directory modules (shell scripts, Dockerfiles, Python, a few Java and `.proto` files): 104,557 chars of pack for 49,892 input tokens, less 1,800 a call: 2.35, so `kb.py estimate` uses 2.4 for a card of any code. The projects above came out at 2.0-2.3, so the estimate read 4-11% low on each.
- **The one card over $0.20** is a module of the TypeScript project whose files include one 90 KB file of type declarations at the top level. The reader keeps declarations, so it keeps 83 KB of it. A directory over the budget splits, but one file cannot.
- **Dead names**, fixed by hand as step 5 says, in the cards as they stand: C project 58, TypeScript project 19, the web part 10, shell project 1, fondue none. Most are library and tool names in backticks, C build options and typedefs the reader does not see declared, and import paths written as the import does (`../../context`). A path relative to the module's own directory is accepted, because the pack names each file that way.
- **Boundaries.** The first write's prompt for any code asked for dependencies "from its build and manifest files" but never said to leave the section out. Most directory modules have neither, so the writer took Boundaries from imports, compile flags, environment variables and the possible references, in nine of ten cards checked. The prompt now names the files that count, says the header's `-` means "not computed", and leaves the section out when nothing supports it. The table is the second write, with that prompt. It still let the writer fill an empty section with "no dependencies were computed" or "none declared", which says nothing true of a module whose dependencies nobody computes; the prompt now forbids such an entry, and the ten cards that had one were written again with it ($0.44, not in the table). Written again, four of them took Boundaries from the module's own import and include lines, which are exact evidence of what it uses, so the prompt now counts them; one that held a usage note instead was written once more.
- **Checked against the code.** Of ten cards of the first write, two from each project, whose extension points and "Already here" entries a reviewer checked against the code, one extension point was incomplete (it named where a new payload format is declared, not the switch that picks it up, which the pack did not show) and one "Already here" entry named the callers of a helper instead of the helper. Of the same ten cards of the second write, no extension point was wrong, and two "Already here" entries pointed to the wrong place: to a platform hook the user must implement, as if the library provided it, and to the host-side build target instead of the script that provides the thing. Step 6's check of two or three cards is what catches them.

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
