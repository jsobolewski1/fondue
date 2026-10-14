Applying the ruling of 2026-10-15 on 01-review.md#2 (option 1).

- #2 fixed in 8cc0281 as the ruling's option 1 and the proposed solution word it: the `[any code]` Boundaries line names the files that count, and a new `[any code]` line limits Boundaries to them or a skill's line and says to omit the section. `prompt("java")` is unchanged (`cmp` against 1bc80fe: identical); `Prompt.test_any_code_variant` now expects 6 `[any code]` lines. Then every gated card was written again from scratch: the first write's cards were moved to `$S/first-write/` and `$S/fondue` re-cloned at 8cc0281, so no card went into its own rewrite. Documents: 89c0edc.
- #1 and #3 as in 02-answer.md.

**Build:** python3 -m unittest discover -s protocol/kb/tests - green, 53 tests passed

**Gates:** at 8cc0281 (89c0edc changes only documents), same `$S`.
- G1: `prompt("java")` byte-identical to 1bc80fe's `card-writer.md`; the Java gate `IDENTICAL`.
- G2 / G4 / G5, the second write, `--model sonnet`, each `estimate` printed just before its write:

  | sample | estimate printed (exact) | cards | usage in+write+read | out | cost | time | estimate vs usage | largest card |
  |---|---|---|---|---|---|---|---|---|
  | c | 128k (128,451) | 12 | 144,455 | 12,163 | $0.67 | 21 s | -11.1% | $0.146 `core` |
  | shell | 13k (12,985) | 2 | 14,643 | 1,330 | $0.06 | 7 s | -11.3% | $0.033 `provision` |
  | fondue | 8k (7,917) | 2 | 8,234 | 1,150 | $0.03 | 7 s | -3.8% | $0.025 `protocol` |
  | hono | 230k (229,676) | 14 | 253,277 | 13,012 | $1.07 | 25 s | -9.3% | $0.249 `src` (accepted, ruling on question.md#1) |
  | java-vue, its 5 directory modules | 57k (57,288) | 5 | 60,473 | 3,931 | $0.26 | 13 s | -5.3% | $0.121 `<p>-demo-server-webapp` |

  G4 holds on every sample; G5 holds on every card but hono's `src`.
- G3: `kb.py status` reads `clean` on c, shell, fondue, hono, and on java-vue's five ids. Dead names fixed by hand, with the same script as before: c 56 (6 corrected, 50 backticks dropped), shell 1 (dropped), fondue 1 (the script corrected `stats.md` to the spec folder's `stats.md`, which the card does not mean; reverted by hand to plain text), hono 21 (5 corrected, 16 dropped), java-vue 9 (dropped).
- G6: the same ten cards, rewritten, in `$S/<label>/fondue/kb/cards/`: c `core.md`, `include.md`; shell `provision.md`, `root.md`; fondue `protocol.md`, `integrations.md`; hono `src-router.md`, `src-middleware.md`; java-vue `<p>-demo-servers-shared-webapp.md`, `<p>-demo-server-webapp.md`. Three of them (`include`, `provision`, `src-middleware`) now have no Boundaries section. Several that kept one hold a single "no dependencies computed / declared" entry, for the reviewer to judge against the new prompt line.

Verdict: next-round git diff 81f79c1..89c0edc
