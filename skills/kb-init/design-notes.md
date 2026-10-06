# kb-init - design notes

For the User changing the knowledge base or its tooling. Roles do not read this file.

## Why a map, and not a vector database
The failures it targets: an agent rebuilds something that exists under another name, and treats existing code as fixed and builds around it. A vector search over code chunks gives no sign of what it missed, which is exactly how the first failure happens. A small text index, read whole, cannot miss a module. Cards are text in git, so grep finds them, a diff reviews them, and `kb.py status` checks them against the code without spending tokens.

## Why the cost stays low
A tool that lets an agent explore the code to describe it pays for its growing context on every call. An earlier tool spent two full sessions on a project a fifth of tachornis's size. Here a script does all the crawling (declarations without bodies, construction sites, wiring files, skill lines) and the model makes one tool-less call per card. The context never grows.

Measured on tachornis, 2026-10-06: 33 Maven modules, 373 main Java files, 1.6M chars. Sonnet, API-equivalent cost.

| What | Tokens | Cost |
|---|---|---|
| Card, small module (16k-char pack) | ~7k in, 1.1k out | $0.07 |
| Card, large module (52-65k-char pack) | ~25k in, 1.7-1.9k out | $0.14-0.15 |
| All cards (estimated from the packs) | ~330k in, ~50k out | ~$1.7 |
| `index.md`, read by every Architect | 4.7k | |
| One card | ~1.9k | |

- **Chars per token.** Java skeletons tokenize at about 2.5 chars per token and card prose at 2.6-2.9. The common rule of 4 undercounts code by about 1.6×. `kb.py estimate` uses 2.5.
- **Overhead.** A `claude -p` call run from a project loads that project's CLAUDE.md and the user's memory: 8.6k tokens a call on tachornis. `--setting-sources ""` cuts it to about 0.8k, and `kb.py` passes it.

## What changed during the pilot, and why
- **The index-writer call was dropped.** The first design wrote the index in one call over every module's slim declarations (~96k tokens, $0.46) so it could be built before any card. Once every card is written anyway, its frontmatter summary is the index entry, and a script concatenates them for free.
- **Construction sites from other modules were added to the pack.** Without them, extension points came out right but incomplete: "add it to the composite's list", when the list lives in another module's factory. With them, cards name the file that wires a new one in. Only files that import the module's packages count, because a same-named type elsewhere (`Entry`, `Bytes`) made noise.
- **Private members stay in the pack.** Filtering to public saved little (~20k vs ~23k tokens of method signatures), and a non-public helper is exactly what should be promoted instead of rebuilt.
- **`touched` takes skills from cards, not from mentions.** Nearly every skill mentions the central modules, so a mention-based list sends the Handover Writer to check every skill.

## Known limits
- **Languages.** Declarations are read only from Java and `.proto` files. Kotlin needs its own extractor, because it has no semicolons to end a declaration.
- **Module discovery** covers Maven, and Gradle without its dependencies.
- **Large modules.** A module of 80+ files fits in 60 lines, but its Offers section starts to read like a type list. Splitting such a module into several cards, by package group, is not built yet.
