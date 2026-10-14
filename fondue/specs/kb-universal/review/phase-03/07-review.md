## #1 G6, Boundaries after the third write: the four rewritten cards now take their Boundaries from the module's own imports or docstring, which the prompt and the 2026-10-14 ruling do not accept (re 01-review.md#2)

**Severity:** Blocker

The prompt for any code now says (card-writer.md:43): Boundaries come only from the module's build and manifest files or a skill's line; "imports, compile flags, environment variables and "Possible references in other modules" are not boundaries"; and the section is left out when nothing supports it, never filled with "no dependencies". The ruling of 2026-10-14 accepts a Boundaries entry only when a build or manifest file, or a project skill, supports it.

Four of the ten checked cards were written again under that prompt. None of them has a build or manifest file in its pack (no `## Wiring` section) or a skill line. Each one still has a Boundaries section:

- C project, `core.md`: "Internal declarations are shared through `internals.h`, which includes the public `include/<lib>.h` and `<protocol>/<parser>.h`." It rests on the `#include` lines of `core/internals.h` (`:56`, `:67`).
- TypeScript project, `src-router.md`: "Router implementations import types, constants and `UnsupportedPathError` from `src/router.ts`, and `checkOptionalParameter` ... from `src/utils/url.ts`." It rests on import lines such as `src/router/reg-exp-router/router.ts:1-7`.
- fondue, `protocol.md`: "Uses only the Python standard library; `kb/kb.py` shells out to git." It rests on imports and on `def git` (`protocol/kb/kb.py:26`, `:82-83`).
- fondue, `integrations.md`: "Output columns are not comparable with turn-stats.py's ..." It rests on the script's own docstring, and it is not a dependency at all.

The first three entries are true. I checked each against the code: these modules do use those files. The fourth is a usage note. None rests on what the prompt and the ruling accept. So G6 still fails on these four cards, by the rule as written.

The writer has moved each time the prompt closed one source. In the first write it took Boundaries from possible references (lines in other modules that merely share a name). In the second write it wrote "no dependencies computed". In the third it used imports. The card template always shows a `## Boundaries` heading, and a sentence in the rules has not been enough to make the writer leave it empty. What remains now is true but not allowed. A further sentence would most likely move the writer again, not empty the section.

The decision is the User's. The evidence rule comes from the ruling of 2026-10-14, and the prompt's wording is what the rulings of 2026-10-15 approved.

**Proposed solution:** ask the User to choose:
1. **Count the module's own import and include lines as evidence.** In card-writer.md:43, replace "imports, compile flags, environment variables and "Possible references in other modules" are not boundaries" with "the module's own import and include lines count too; compile flags, environment variables and "Possible references in other modules" do not". This amends the 2026-10-14 ruling to accept a dependency the module's own code states. The `core`, `src-router` and `protocol` entries then hold as written, with no rewrite. `integrations.md` is written again (about $0.01), so its non-dependency entry goes, and the same ten cards come back for G6.
2. **Keep the rule and accept the cards as they are.** design-notes' Known limits says that a directory module's Boundaries may rest on its own imports or notes, which neither the prompt nor `kb.py status` keeps out. A reader checks them against the code. Nothing is written again.

Verdict: changes-requested
