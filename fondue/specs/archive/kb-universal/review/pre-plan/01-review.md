## #1 Recursive size splitting creates meaningless modules

**Severity:** Blocker

D2 says every over-budget group splits by its child directories and says the resulting sample lists are ones a code reader would draw (`pre-plan/03-draft.md:38`). The recorded result contradicts that claim: hono gets `src/request` at 56 raw characters and `src/preset` at 1,229, while the lower-budget variant creates several roughly 1,000-character launcher modules (`pre-plan/01-research.md:92-103`). Those are accidental directory leaves, not capabilities worth separate cards. This is wrong about the module-boundary approach, and Phase 1's exact-list gate would freeze the accident into the design (`pre-plan/03-draft.md:74-80`).

**Proposed solution:** Add a lower meaningful-size rule to D2: after a size-driven split, fold small child groups into the base directory's residual module while substantial children remain separate; an explicitly named `parts.txt` part is exempt. Leave the numeric lower bound to plan. Add to Phase 1's gate that no automatically created child is below it, and update the sample module lists accordingly.

## #2 Name overlap cannot be asserted as a dependency edge

**Severity:** Blocker

D7 turns occurrences of declared names or file names into `depends on (project)`, `depended on by`, and wiring evidence (`pre-plan/03-draft.md:54-58`). Its only RESULT already produces edges a reader would reject, including hono `src/jsx` used by `src/utils` and the C client used by `core` (`pre-plan/01-research.md:105-112`). A hand-picked allow/deny list for the samples in Phase 3 (`pre-plan/03-draft.md:92-98`) can tune those repositories but cannot make lexical coincidence mean dependency in an arbitrary language. Cards are the map later roles trust; a sparse boundary is safer than a false one.

**Proposed solution:** Do not populate dependency fields from name-frequency inference. Keep exact Java/Maven edges and exact relationships exposed by packed build or manifest files. If lexical cross-module hits are still useful, label them as possible references in the pack only and prohibit the writer from presenting them as boundaries or wiring without exact evidence. Remove Phase 3 as a standalone delivery phase, or redefine it around exact evidence with a gate that checks the evidence rather than tuned symbol thresholds.

## #3 A finite extension list still refuses unknown-language projects

**Severity:** Blocker

The goal says a knowledge base for "any project" should be possible (`pre-plan/00-brief.md:4-6`), but D4 makes membership depend on a finite list of extensions and filenames chosen in plan (`pre-plan/03-draft.md:47-49`, `pre-plan/03-draft.md:114`). The generic reader does not make discovery universal if an unlisted language never reaches it: such a repository still has no module and `kb.py` still refuses to build. Neither directory parts nor exclusions can currently include a source that discovery never recognized.

**Proposed solution:** Keep known extensions for automatic classification, but add a language-neutral escape hatch that can include tracked text files or directories as source (alongside exclusion). Make Phase 1 gate a repository containing an otherwise unknown, shebangless text-source extension through that override. Then the default can remain conservative about Markdown and data while the mechanism is genuinely not language-bounded.

## #4 The stated Java compatibility promise excludes an admitted class of Java cards

**Severity:** Blocker

Question 5 answers that Java card cost and content may not change, then immediately permits Kotlin, Scala, or Groovy files inside an existing build-file module to enter the pack through the new reader (`pre-plan/03-draft.md:27`). Phase 2 requires exactly that (`pre-plan/03-draft.md:83-90`), and D8 preserves the old prompt only when all declarations are Java/proto (`pre-plan/03-draft.md:60-62`). Such mixed JVM modules already have cards under the Java/build-module path, so their input, prompt, cost, and potentially content change. The pure-Java sample gate cannot detect this boundary.

**Proposed solution:** State the compatibility contract precisely: modules containing only Java/proto keep byte-identical packs and prompts; existing mixed-language build modules may improve and change. Add a mixed Java/Kotlin fixture that gates the intended new behavior. If the intended promise really covers every existing build-file card, keep unsupported JVM files name-only in this spec instead.

## #5 Whole-project word occurrence is too weak for generic dead-name validation

**Severity:** Nit

D9 accepts every quoted identifier when it occurs anywhere in the project's code (`pre-plan/03-draft.md:64`). Lowercase function and variable names are commonly duplicated across modules, so the Phase 4 rename test can pass while a card still names a symbol its own module no longer declares (`pre-plan/03-draft.md:100-110`). The exact matcher is a technical decision for plan rather than pre-plan.

**Proposed solution:** Reduce D9 to the approach-level requirement that generic quoted code names are validated against reader-produced names owned by the card's module while Java behavior remains unchanged. Leave syntax and matching to plan, and gate a rename where another module still contains the same lowercase word.

Verdict: changes-requested
