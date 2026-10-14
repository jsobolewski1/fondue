- #1 accepted, fixed in 83171ca as proposed. G3 run again at 83171ca: 8 new dead names, all corrected by hand to repo paths (fondue 2: `./turn-stats.py` and `./stats-total.py` to `protocol/...`; hono 6: two in `src`, four in `src-middleware`, one of them, `./jwt/index.ts`, corrected by hand because two `jwt/index.ts` exist). Every sample reads `clean` again. New counts: c 89, shell 0, fondue 2 (2 corrected), hono 47 (23 corrected, 24 backticks dropped), java-vue 14; design notes updated in 669ab52.
- #2 question:
  **Decision:** Most cards of plain-directory code have a "Boundaries" section that the plan's rule says they may not have. Should the writer's prompt change so that it leaves the section out, and the cards be written again, or should the cards stay as they are, with the weakness recorded?

  **Why it's yours:** The prompt's wording for any code is fixed by the approved phase file (phase-03.md, decision 1). The rule the cards break is your ruling of 2026-10-14: a "Boundaries" entry may rest only on a build or manifest file, or on a project skill's line. Changing either is a change to an approved artifact.

  **Context:** A card's "Boundaries" section says what the module depends on, and later Architects trust it. A directory module (code outside any Maven or Gradle module) has no computed dependencies: its input says `-` for them, and most such modules have no build or manifest file of their own either. The reviewer checked ten cards, two per sample, and nine have at least one "Boundaries" entry that nothing allowed in its input supports. Some say "no dependencies" because the input shows `-`, which really means "not computed". Some read dependencies off import lines or compile flags. Four state a boundary from the "possible references" lines (lines in other modules that merely mention the module's names), which the prompt forbids. The cause is the prompt: its line for this section asks for dependencies "from its build and manifest files", but unlike the other optional sections it never says to leave the section out when there are none, so the writer fills it from whatever it has (review/phase-03/01-review.md#2 lists each entry).

  **Options:**
  1. **Change the prompt and write the cards again.** The prompt's "Boundaries" line for any code names the files that count (those under the input's wiring heading, or the module's own build file such as a Makefile or `CMakeLists.txt`), and one new line says the header's `-` means "not computed", that imports, compile flags, environment variables and possible references are not boundaries, and to omit the section when nothing supports it. The Java wording does not change. Then all 35 sample cards are written again (about $2.10 on Sonnet), checked for dead names again, and the same ten cards go back to the reviewer.
  2. **Keep the cards and record the weakness.** Nothing is rewritten. The design notes' Known limits say that a directory module's "Boundaries" section is not reliable, so a reader must check it against the code. Every future card of such a module will have the same problem.

  **Recommendation:** Option 1. A wrong boundary is the entry most likely to mislead a later design, which is why your earlier ruling limited what it may rest on; the fix is two prompt lines, and the rewrite costs about what the first write did.
- #3 accepted, fixed in 669ab52 as proposed

**Build:** python3 -m unittest discover -s protocol/kb/tests - green, 53 tests passed

**Gates:** at 83171ca (669ab52 changes only the design notes), same `$S`: G1 `prompt("java")` still byte-identical (`Prompt.test_java_variant_is_the_prompt_as_it_was`; card-writer.md unchanged since b7d912c); G3 `clean` on c, shell, fondue, hono, and on java-vue's five ids, with the counts above. G2, G4, G5 and the calibration as in the request: no card was written again.

Verdict: question 01-review.md#2
