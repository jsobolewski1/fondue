# spec — design notes

For the User choosing a roster or changing the skill. Roles do not read this file.

## Why the default roster is all Opus except the Architect

Arbiter and Coder were Sonnet until 2026-09-22. Both were changed on measured results, not preference.

- **Coder.** A Sonnet Coder's first implementation of a phase drew 12 Blockers and 10 Nits, its second answer 5 and 5; the Opus Coder that took over closed the phase on the next round.
- **Arbiter.** It looks like the safe place to save a model because it "governs whose turn it is and nothing more" — that reading is wrong. The judgment is in noticing what is *missing*: a Sonnet Arbiter ran a whole spec without ever creating `stats.md`, left `current-state.txt` naming a Review step that an approving review had already closed, and sent `Your turn.` to roles that had not yet handed back. None of those is a hard call; each needs someone who is actually reading the process rather than relaying it.

## Why two planning stages, and where the line between them runs

Pre-plan settles the approach and plan settles the technical decisions, because a frame the reviewer rejects throws away everything built on it. In the archived runs, frame-level Blockers arrived late: a required capability left out, raised in round 1 and re-asserted in round 3; a design option shown to be an estimate rather than exact, in round 4. Had the phase files already been written, each ruling would have discarded them too.

The line matters as much as the split. When pre-plan drafts answered every technical question in the brief, 60-80% of each final draft sat before its phases, as decisions like identifier lengths, metric labels and refresh threads. The pre-plan reviews mixed frame Blockers with technical ones ("the gate cannot query the histogram by its contract name"). Each technical Blocker cost a new draft file and buried the frame findings among them. Plan reviews caught the kind of Blocker plan should catch: a phase consuming a window it never creates, a contract value left for the Coder to invent. Hence the boundary test, and the rule that a technical finding at pre-plan is a Nit.

## Why a draft states invariants, and why breaking one is a Blocker at pre-plan

Five specs in a row, run in October 2026 on one fix, were each followed by independent reviews of the whole range. Every finding those reviews rated Major (their scale was Major and Minor) was in the design, and none in the code:
- a per-identity admission limit was keyed on the identity the request claims instead of the one the platform authenticates, so any caller could use up another identity's share;
- default limits refused healthy traffic on a node with one dominant identity;
- saturation tests sent their load as one identity, so the new per-identity limit refused it before it reached what the tests were meant to show;
- an outer deadline aborted only its own socket and left the inner call running, so the bound the fix claimed did not hold.

The code-level findings (path encodings, an abort race, a retry budget) were all Minor.

The first of these was in the first draft, with an argument for why it was harmless. The pre-plan reviewer saw it and could only raise it as a Nit, because it was a technical decision. The spec ran in light mode, so no plan review followed (see Why there is no light mode). Two later reviews reported it NOT FIXED. Each fix round closed one more difference between the spec's own reading of the credentials and the platform's, and one of those fixes was verified against the platform's parser instead of the provider that decides the identity, so a test pinned the wrong behaviour. The hole closed only when a full-mode spec keyed the limit on the authenticated identity and so stopped reading credentials a second time.

Four rules follow:
- **The draft states invariants, and the reviewer writes their own first.** An adversarial review needs a property to attack, and writing one's own before reading the draft keeps it from inheriting the draft's list, for the same reason as the reviewer's own approach.
- **A broken invariant is a Blocker at pre-plan, even through a technical decision.** The boundary test in "Why two planning stages" still decides what a draft carries, with invariants added to it: a decision an invariant rests on belongs in the draft. A wrong technical decision that breaks no invariant is still a Nit there. A decision that breaks a guaranteed property is a different kind of finding: it is wrong about the approach. Leaving it to plan would mean writing every phase file on a frame that cannot hold. And it is answered by a decision that keeps the invariant, never by moving the decision out of the draft, or the rule would reward leaving risky decisions out.
- **An invariant states its conditions, and a guarantee the brief did not ask for is the User's.** Almost no property holds under every load. An invariant without conditions could be broken every round, and pre-plan would never close. What the spec guarantees is also part of what it delivers, which the engine leaves to the User, so a reviewer who wants a guarantee nobody asked for raises a question, not a Blocker.
- **The RESULT an invariant rests on must exercise the part that decides.** A RESULT against a nearby parser is still a RESULT under the engine's rule, and it can still be wrong about the mechanism.

Why not open-ended review instead: in the same runs, reviews asked to find anything raised about ten new findings a round, most of them in code the round before had written, and the last round found a Major in first-round code that four earlier reviews had missed. Open-ended review samples a surface that grows with every fix, so "nothing new" never arrives and never proves anything when it does.

## Why an audit runs after the last phase, and why the auditors write the changes

In the five-spec run above, three independent reviews ran after each spec: one for tests, one for style and project rules, one for anything else. The tests review found the most that was new each round, and every one of its findings came with its proof: the throwaway mutation, the command, BUILD SUCCESS where a failure was due. The per-phase Code Reviewers had missed nearly all of them. The worst came from two defences masking each other. Two saturation tests passed only because the new per-identity limit refused their load first, so neither could fail if the defence they were written for was reverted. Both landed in one phase, and its Code Reviewer approved it: a reviewer of a change judges whether the change is right, and asking which tests can still fail is a different question. It also has a cross-phase form, a test made vacuous by a defence a later phase adds, which no review of one phase can see. So the audit asks only that question, of the whole range, once.

The style review found real breaches, but most of them were in code the previous round had written, and each cost a Coder an Answer turn to apply what the reviewer had already written out. So the auditors write their own changes and a Coder reviews them. A Coder, because checking a test change means running it, which the engine limits to one targeted command unless the process skill allows more, as this one does for the lens topics. Each auditor's write scope is narrow, test code only or behaviour-preserving changes only. That is what makes it safe for the author of a fix to also be the one who found the problem: a Tests Auditor allowed to touch production code can bend the code to fit its test. A bug in production code goes to `audit-fixes`, with a Coder and a Code Reviewer as in any phase.

The style review's commit findings, a refactoring mixed into a behaviour commit and commit subject lines over the project's length limit, were skipped in every round because the history was already pushed. The audit runs before the push, so the history could be rewritten, but the Conventions Auditor does not rewrite it: `landed.md` and every review name shas. Commit breaches are reported, not fixed, and an auditor that reports one opens a review even when it changed nothing, so that every claim the audit makes is checked by someone.

The adversarial review that found the design Majors is not an audit lens: it belongs to the Architecture Reviewer at pre-plan, against the draft's invariants (see above).

## Why there is no light mode

Until 2026-10-16 a brief could say `Mode: light`, for a spec whose design was settled and whose work was mechanical. The draft then carried the tasks, and plan split it into phase files with no research and no review. It was removed for three reasons:
- **"The design is settled" cannot be checked at the brief.** The Arbiter's check was mechanical: no open question except ones marked `(technical)`. In the five-spec run above, four specs ran light, the first among them with an admission design that turned out to have a security hole. Its open questions were the limit values and how a refusal reaches the caller. They were tagged technical, and they were the design. The one full-mode spec is the one that closed the hole.
- **It saved little.** A light plan stage took under a minute; a full one took about 20 minutes (17 to draft, 3 to review), in specs that took two to three hours each.
- **The work it was for does not need a spec.** A rename or a move small enough for the plan stage to be a large part of its cost is cheaper done directly than run through every role of a spec.

## Why a reopen starts a new attempt instead of a new draft

A failed approach can surface at plan or deep in implementation, with phases already landed. Continuing the draft sequence would skip the step that matters most at that point: the reviewer writing their own approach before reading the draft, because `02-reviewer-research.md` already exists. So a reopen moves the failed attempt aside, re-signs the brief and seats a fresh pair, who are the least anchored to the old frame.

What the new pair must not lose is why the old plan failed. So they read each earlier `plan.md`, which states the approach on a page because pre-plan drafts carry no technical detail, and each `reopen.md`, which holds the RESULT that broke it. They do not read the drafts, reviews and phase files, which argue for the failed frame. The draft must show that it does not rest on a broken assumption, and it must account for every landed commit, which makes knowing the failure something the reviewer can check.

## Why a Coder and a Code Reviewer are fresh per phase by default, and when `continue` may win

A session kept into the next phase re-reads the context it carries on every call of that phase. A fresh session instead writes its own way in: the skills, the plan, the phase file and the code it reads. Per phase, roughly:

- **Extra cost of continuing:** context carried × calls in the phase × 0.1, the cache-read price.
- **Saving:** the orientation a fresh session writes × 2, the one-hour cache-write price, plus the minutes it spends finding its way.

In the archived runs a Coder's draft turn made 70-140 calls and ended at 190-320k of context. For 017's phase 02 that came to about 1.6M input-equivalent tokens fresh against 2.7-3.0M continued, with the five-minute cache of the time. The carried context and the number of calls both grow with the size of a phase, and the saving does not, so `continue` can win only on small phases: the next phase must make fewer calls than about 20 × the orientation saved ÷ the context carried. A continued session that outgrows its context window is compacted, a lossy reset that is worse than a fresh start, so `continue` is not for big specs.

`Sessions: continue` is an experiment. Record every spec run with it below, next to a comparable one run `fresh`. `protocol/stats-total.py <stats.md>` gives the implementation stage's input-equivalent total. Compare only specs with the same roster, and pass `--write-weight 1.25` for specs run before 2026-09-30, when roles still had the five-minute cache.

| Spec | Sessions | Phases | Implementation, input-equivalent | Implementation time | Notes |
|---|---|---|---|---|---|
| 017 | fresh | 4 | 8.45M (`--write-weight 1.25`) | 104m | baseline, five-minute cache, all Opus |
