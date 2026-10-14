## 2026-10-14 plan:Answer | settles review/plan/01-review.md#6

**Asked:** Should the card check in Phase 3 accept a "Boundaries" entry only when the module's build or manifest files, or a project skill, support it, and never because of a line that merely uses one of the module's names?

**Ruling:** Option 1

## 2026-10-15 implementation:03:Draft | settles question.md#1

**Asked:** One card on the public TypeScript sample cost $0.25 to write, over the phase's $0.20 limit per card. Do you accept it, or should something change so that it fits?

**Ruling:** accept

**Carried out as:** question.md moved into the Evidence below and deleted. Three sample-project names in it were replaced by generic labels, under the brief's rule that committed files never name a sample project.

**Evidence:**

    ## 1

    **Decision:** One card on the public TypeScript sample cost $0.25 to write, over the phase's $0.20 limit per card. Do you accept it, or should something change so that it fits?

    **Why it's yours:** The $0.20 limit is a gate in the approved plan (plan.md, Phase 3: "No card costs more than $0.20"). Passing this card anyway, or changing how such a card is built, changes an approved artifact.

    **Context:** I wrote the cards of all five samples: 35 cards for $2.08 on Sonnet. 34 of them cost $0.01-0.15. The one over the limit is hono's `src` module, at $0.248 (60,698 input tokens). That module is the handful of files directly in hono's `src/` directory. One of them, `src/types.ts`, is 90 KB of TypeScript type declarations at the top level of the file, with no function bodies. The reader that knows no language keeps declarations and drops bodies, so it keeps almost all of this file: 83 KB of the module's 111 KB of declarations. The rule that splits a large directory into smaller modules cannot help, because it splits directories, and this is one file. The Java path has no cap either: the Java + Vue sample's Java module `<the sample's core Java module>` packs to about 118k tokens, roughly $0.45 if written; its card was not part of this run.

    **Options:**
    1. **Accept it and record it.** The $0.25 card stays. The design notes record it under the measured costs, and Known limits say that a single large file of declarations makes an expensive card, and that `parts.txt` can exclude such a file (`- src/types.ts`) if the User prefers. Nothing more is built. Nothing changes on any other sample.
    2. **Exclude the file on that clone and rewrite the card.** Add `- src/types.ts` to the hono clone's `parts.txt`, as kb-init lets a User do, and rewrite `src`'s card. It would cost about $0.06 and pass the gate. The card then does not know `types.ts`'s types, and the gate's "write --all with the defaults" becomes "with one exclusion" for hono.
    3. **Cap the declarations per file.** The reader would keep at most a fixed amount of each file (say 20 KB) and mark the cut, so no single file can dominate a card. This is new design: it changes the reader of Phase 2, so the phase-2 compression figures and the hono cards would be measured and written again (about $1.10).

    **Recommendation:** Option 1. The limit was meant to keep a card's cost close to the Java pilot's, and 34 of 35 cards are well inside it. The one outlier is caused by one unusual file, and the User already has a lever for it (`parts.txt`). A cap would silently drop declarations from every large file, while Java modules have no such cap.

    ## 2

    **Decision:** Should the card check accept a path that names one of the module's own files relative to the module's directory, such as `src/main.js` in a card for the module at `<a web part of the Java + Vue sample>`?

    **Why it's yours:** The phase file fixes how the check reads a name with a `/` in it: as a path from the repository root (phase-03.md, decision 2, rule 1). Accepting other paths changes an approved artifact.

    **Context:** After the writes, `kb.py status` reports 223 dead names across the samples (the shell sample has none). The phase asks me to fix them by hand, as kb-init tells a User to, and report the count. About 94 of the 223 are not wrong: they name a real file of the module itself, written relative to the module's directory, like `src/main.js` or `fetch/bench.mts`. The writer does this because the module's input lists every file under that same relative heading (`### src/main.js`). The check looks for them from the repository root, where they do not exist. The rest of the dead names are real misses: library names that should not be in backticks (`axios`, `keytool`), C build options the C reader never sees declared (two of them, set in the CMake files), and paths from import statements (`../../src`). By sample: C 93 (7 module-relative paths), fondue 3 (3), TypeScript 92 (63), Java + Vue web parts 35 (21).

    **Options:**
    1. **Keep the check as it is, and fix every dead name by hand.** About 223 hand edits on the clones, reported per sample as the gate asks. Every future card of any code will have the same kind of dead names, and each User of kb-init will fix them by hand.
    2. **Also accept a path relative to the module's own directory, when that file exists.** A small change to the check, with a test, and one line of the prompt says so. The 94 correct paths stay as written, and about 129 dead names are fixed by hand. No card needs to be written again.
    3. **Make the writer use repository paths instead.** Change the prompt so that the writer names its module's files by their repo path. Every card of any code would have to be written again (about $2) to measure the effect.

    **Recommendation:** Option 2. The writer reads the module's files under module-relative headings, so quoting them that way is natural and correct. Accepting what is already right costs a few lines, while the other options either leave every User with dozens of false alarms or spend another full write to find out whether a prompt change works.

## 2026-10-15 implementation:03:Draft | settles question.md#2

**Asked:** Should the card check accept a path that names one of the module's own files relative to the module's directory, such as `src/main.js` in a card for the module at `<a web part of the Java + Vue sample>`?

**Ruling:** 2

## 2026-10-15 implementation:03:Answer | settles review/phase-03/01-review.md#2

**Asked:** Most cards of plain-directory code have a "Boundaries" section that the plan's rule says they may not have. Should the writer's prompt change so that it leaves the section out, and the cards be written again, or should the cards stay as they are, with the weakness recorded?

**Ruling:** Option 1

## 2026-10-15 implementation:03:Answer | settles review/phase-03/04-review.md#1

**Asked:** After the rewrite, some cards still have a "Boundaries" section whose only entry says the module has no dependencies, which nothing in the card's input supports. Should the prompt forbid such entries and the affected cards be written again, or should the cards stay as they are, with the weakness recorded?

**Ruling:** 2

## 2026-10-15 implementation:03:Answer | settles review/phase-03/07-review.md#1

**Asked:** May a card's "Boundaries" entry rest on the module's own import and include lines, or must the cards keep the stricter rule, which the writer keeps breaking?

**Ruling:** 1

