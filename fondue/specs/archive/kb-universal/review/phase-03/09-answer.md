Applying the ruling of 2026-10-15 on 07-review.md#1 (option 1).

- #1 fixed in 390feee as proposed: card-writer.md:43 now reads "the module's own import and include lines count too; compile flags, environment variables and "Possible references in other modules" do not". `prompt("java")` unchanged (`cmp` against 1bc80fe: identical). fondue's `integrations.md` was moved to `$S/third-write/fondue/` and written again from scratch at 390feee: estimate 3k, 1 call, 2,598 input, 321 output, $0.014. It now has no Boundaries section. No other card was written. Design notes: 75176a7.

**Build:** python3 -m unittest discover -s protocol/kb/tests - green, 53 tests passed

**Gates:** at 390feee (75176a7 changes only the design notes), same `$S`. G1: `prompt("java")` byte-identical, the Java gate `IDENTICAL`. G3: `clean` on c, shell, fondue, hono, and on java-vue's five ids; the rewritten card needed no hand fix. G6: the same ten cards; `integrations.md` is the one that changed.

Verdict: next-round git diff 0cfada0..75176a7
