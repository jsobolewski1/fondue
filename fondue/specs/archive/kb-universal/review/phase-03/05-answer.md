- #1 question:
  **Decision:** After the rewrite, some cards still have a "Boundaries" section whose only entry says the module has no dependencies, which nothing in the card's input supports. Should the prompt forbid such entries and the affected cards be written again, or should the cards stay as they are, with the weakness recorded?

  **Why it's yours:** The prompt's wording for any code is what your ruling of 2026-10-15 approved (option 1 on review/phase-03/01-review.md#2). Changing it again changes an approved artifact. Keeping the cards leaves them short of your ruling of 2026-10-14, that a "Boundaries" entry rests only on a build or manifest file or on a project skill.

  **Context:** The rewrite did what it was meant to: no card now states a dependency from imports, compile flags or the "possible references", and three of the ten checked cards leave the section out. But the writer often still writes one entry such as "No dependencies are declared for this module" or "No project dependencies were computed". For a module outside Maven and Gradle, nothing is computed and most have no manifest, so such an entry says nothing true, and a later reader may take it as "this module stands alone" when it does use other code. Of the ten checked cards, four have only such an entry. Across all 35 cards, about ten have one (I counted by searching the Boundaries sections; one of them, a web part whose `package.json` lists no dependencies, is actually supported).

  **Options:**
  1. **Forbid the entry and rewrite every card.** The prompt's last Boundaries line becomes "Omit the section if there are none: never write an entry that says the module has no dependencies, or that none were computed or declared." All 35 cards are written again (about $2.10 on Sonnet) and checked for dead names again, so the measured costs describe the prompt as it ships. The reviewer checks the same ten cards.
  2. **Forbid the entry and rewrite only the cards that have one.** The same prompt change. Only the roughly ten cards with such an entry are written again (about $0.50), from scratch. The costs already measured stay as recorded: the change touches one section, so they still describe the prompt well. The reviewer checks the same ten cards.
  3. **Keep the cards and record the weakness.** Nothing is rewritten. The design notes' Known limits say that a card of such a module may have a "Boundaries" entry that only says no dependencies were computed or declared, and that it means nothing.

  **Recommendation:** Option 2. The fix is one sentence, and an empty "no dependencies" claim is the kind of entry your earlier ruling meant to keep out. Rewriting only the affected cards costs a quarter of a full write and leaves the measured costs, which barely depend on this sentence, as they are.
- #2 accepted, fixed in 8ef9145 as proposed

**Build:** python3 -m unittest discover -s protocol/kb/tests - green, 53 tests passed

**Gates:** unchanged since 03-answer.md: 8ef9145 changes only the design notes, and no card was written.

Verdict: question 04-review.md#1
