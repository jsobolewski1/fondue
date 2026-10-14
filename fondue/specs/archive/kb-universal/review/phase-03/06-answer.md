Applying the ruling of 2026-10-15 on 04-review.md#1 (option 2).

- #1 fixed in 71804e5: the `[any code]` Boundaries line ends "Omit the section if there are none: never write an entry that says the module has no dependencies, or that none were computed or declared.", as proposed. `prompt("java")` unchanged (`cmp` against 1bc80fe: identical). The ten cards that held such an entry were moved to `$S/second-write/<label>/` and written again from scratch at 71804e5: c `<protocol>`, `core`, `data`; fondue `integrations`, `protocol`; hono `src-client`, `src-router`, `src-validator`; java-vue `<p>-integration-tests`, `<p>-core-certificates`. The one supported entry (`<p>-demo-servers-shared-webapp`, from its `package.json`) was left. Design notes: 0cfada0.
- #2 as in 05-answer.md.

**Build:** python3 -m unittest discover -s protocol/kb/tests - green, 53 tests passed

**Gates:** at 71804e5 (0cfada0 changes only the design notes), same `$S`.
- G1: `prompt("java")` byte-identical to 1bc80fe's `card-writer.md`; the Java gate `IDENTICAL`.
- The ten rewrites, `--model sonnet`, estimate printed before each: c 54k for 3 cards, $0.27 (`<protocol>` $0.070, `data` $0.058, `core` $0.145); fondue 8k for 2, $0.03 (`integrations` $0.009, `protocol` $0.024); hono 19k for 3, $0.08 (`src-router` $0.031, `src-client` $0.037, `src-validator` $0.016); java-vue 12k for 2, $0.05 (`<p>-core-certificates` $0.021, `<p>-integration-tests` $0.032). $0.44 in all, every card under $0.20. G2, G4 and G5 for the full write stay as 03-answer.md reports them, as the ruling says.
- G3: `kb.py status` reads `clean` on c, shell, fondue, hono, and on java-vue's five ids. Dead names fixed by hand in the rewritten cards: c 5 (4 corrected, 1 dropped), fondue 0, hono 1 (corrected), java-vue 5 (1 corrected, 4 dropped). In the cards as they stand: c 58, shell 1, fondue 0, hono 19, java-vue 10.
- G6: the same ten cards. Of the 35, no Boundaries entry now says only that the module has no dependencies, apart from the supported web-part entry above (searched every card's Boundaries for "no ... dependencies / declared / computed"). `src-client` now has no Boundaries section. The rewritten cards that keep one, for the reviewer to judge: c `core.md` (headers its `internals.h` includes), hono `src-router.md` (its imports from `src/router.ts`), fondue `protocol.md` (standard library only, `kb/kb.py` runs git).

Verdict: next-round git diff 283e45d..0cfada0
