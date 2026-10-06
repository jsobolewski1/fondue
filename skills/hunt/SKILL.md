---
name: hunt
description: "Bug-hunting sibling of spec: two actors, a Hunter and a Reviewer, take one bug from the User's report to a verified fix - reproduce, find the root cause, fix, prove the fix. Use whenever a bug is started, continued or reviewed. Bugs live in fondue/bugs/<bug>/; fondue/specs/ holds specs. Read fondue/bugs/<bug>/current-state.txt first; fondue/bugs/archive/ is history, never current truth."
license: MIT
metadata:
  owner: "Jakub Sobolewski"
  version: 5
  status: "young - run end to end on one real bug so far; update in place as runs teach us"
---

# hunt - from symptom to verified fix

A bug goes from the User's report to a fix proven against its cause, through fixed stages.

**This skill runs on the fondue engine.** Read `protocol/engine.md` at the plugin root,
`../../protocol/engine.md` from this skill's directory, before anything below. The engine holds
state, turns, replies, rulings, review, and commits. This skill fills in the engine's hooks: stages,
roles, artifacts, transitions, the turn table, and what counts as a Blocker.

## Why a sibling of spec, not a mode
In a feature, the uncertainty is the design; in a bug, it is the diagnosis. The spec skill's plan stage,
phase files and per-phase Coders manage a design across many phases. A bug has one cause and one fix,
so they are ceremony here. What the engine gets right for bugs is kept and sharpened: the RESULT rule
(run it, never read it), a reviewer who asks what else fits the evidence, and gates that fail today.

## When to use it
Use it when **the cause is unknown and finding it takes experiments**: intermittent, distributed,
load-dependent, or where a wrong diagnosis is cheap to ship and expensive to discover. A bug with a
stack trace or a local repro whose fix follows from it needs none of this: red test, fix, green test,
one commit. Neither does a bug found while building a feature, when the project fixes those on the
feature branch in their own commit.

## Glossary
The engine's glossary holds, with these additions:
* **Spec** - here, one bug. **Kind** - `bugs`: a bug's folder is `fondue/bugs/<bug>/`.
* **Stage** - one of `report`, `hunt`, `fix`, then the engine's `done` or `abandoned`.
* **Role** - the engine's User and Arbiter, and Hunter and Reviewer.
* **Topic** - `hunt` or `fix`. The author of both is the Hunter, and the reviewer of both the Reviewer.
* **Subject** - a diagnosis file (`hunt`) or a commit range (`fix`).
* **Red commit** - the commit that adds the regression check and nothing else. The check fails there.
* **Approved artifact** - the signed `report.md`, and the diagnosis a closed hunt approved. Changing one is a User question (engine: User questions).

## Folder layout
```
fondue/bugs/
  <bug>/
    current-state.txt, roster.md, 99-user.md, stats.md     (engine)
    report.md
    hunt/
      01-diagnosis.md, 02-diagnosis.md, ...
    review/
      hunt/   00-request.md, 01-review.md, 02-answer.md, ...
      fix/    00-request.md, ...
    question.md      (engine: User questions)
    advice/          (engine: Advisors)
  archive/
    <bug>/
```

## Stages
The spec starts as the engine's Starting a spec says, with first state `report`.

### report
The User writes `report.md`, the bug's starting document, alone or with AI help. The stage ends
when the User signs it off. The Arbiter commits and sets `hunt:Draft`.

### hunt
The Hunter reads the knowledge base (engine: Knowledge base) to find its way into the code, then
reproduces the bug, localizes it, finds the root cause, writes `hunt/01-diagnosis.md` and opens
`review/hunt/`. Every accepted fix to a diagnosis goes into a new diagnosis file with the next
free number. Diagnosis files are never edited.

The Hunter may commit **diagnostic code** - counters, logs, probes - and change the environments
`report.md` allows. Each diagnostic commit is listed in the diagnosis. By the end of `fix` it is either
kept as part of the fix, with a reason, or reverted.

The Reviewer reads `report.md` and the diagnosis, and judges whether the diagnosis is sound: every
step of the causal chain stands on its RESULT, every observation in the Evidence is explained, and
the evidence rules out every other cause that would produce it. They may read code and run local
commands to test a claim. They never change an environment `report.md` gives the Hunter.
Why the review starts from the diagnosis: the Hunter has done the hunt, and a second one costs about
as much again. What guards against anchoring on the Hunter's story is the last check: a cause is
shown only when its rivals are ruled out, so a rival the Hunter never considered is a finding.

The stage closes on verdict `approved` or `closed`. If the approved diagnosis has `Outcome: exit`,
the next state is `done`, not `fix` (see Exit to a spec). A bug that will not reproduce, or is not
worth the hunt, is abandoned as the engine says.

### fix
The Hunter commits the regression check alone first: the red commit, which fails. Then they commit
the fix and open `review/fix/`, under the engine's Code turns: every turn that changes code ends with
the full build green and all tests passing. The red commit is the only commit allowed to be red, and
only at the check it adds.

The Hunter also updates any project documentation the bug proved wrong or missing, e.g. a gotcha in a
feature skill. When the project has a knowledge base, it brings that up to date too (`protocol/kb.md`).
`<sha>` is the commit the bug's code changes start from: the parent of the first diagnostic commit the
fix keeps, or of the red commit if it keeps none. The Hunter runs `kb.py write --since <sha>`, then
`kb.py status --since <sha>` until it reads `clean`, and checks against the fix the project skills
`kb.py touched <sha>` lists. The documents are committed on their own, after the fix. When
`fondue/kb/` is ignored, no card is staged and the request names the changed cards as files. There is
no handover stage.

The stage closes on verdict `approved` or `closed`, and the next state is `done`.

### Exit to a spec
When the root cause is real but its fix is a design change - a port, a contract, a module
boundary - the diagnosis says `Outcome: exit`. The hunt still closes on approval, and the bug goes to
`done`. The User may then open a spec. Its brief restates the facts it needs from the
diagnosis, because an archived bug is history, not a source.

## State
`current-state.txt` is `<stage>[:<Step>]`, e.g. `report`, `hunt:Review`, `fix:Answer`, `done`.

### Transitions
The engine's rows hold. This skill adds:

| state | reply | next state |
|---|---|---|
| `report` | User signs the report off | `hunt:Draft` |
| `hunt:Review` / `hunt:Answer` | DONE, `approved` / `closed` | `fix:Draft` |
| `hunt:Review` / `hunt:Answer` | DONE, `approved exit` / `closed exit` | `done` |
| `fix:Review` / `fix:Answer` | DONE, `approved` / `closed` | `done` |

After an exit, the Arbiter tells the User the bug left for a feature spec. It is the one closing the
User needs to hear about.

### What the Arbiter does on a transition
* **Fresh sessions.** None. Each role is spawned once, before its first turn.
* **Commit points.** When the report is signed off and when the hunt closes.
* **The writer's tokens.** `fix:Draft` and `fix:Answer` may run `kb.py write`, so their replies get the
  engine's `KB writer` row (engine: stats.md).

## Who reads and writes what
R = reads, W = writes (and reads). A role reads nothing in the spec that this table does not give it.

| artifact | Arbiter | Hunter | Reviewer |
|---|---|---|---|
| `current-state.txt`, `roster.md`, `99-user.md` | W | R | R |
| `stats.md` | W | | |
| `report.md` (User writes) | | R | R |
| `hunt/NN-diagnosis.md` | | W | R |
| `review/hunt/`, `review/fix/` | | W request, answers | W reviews |
| code | | W | R, and runs the red/green check |
| `fondue/kb/` (project, engine: Knowledge base) | | W | R |
| `question.md` | moves into a ruling | W | |
| `advice/` | W | | |

When the User asks, the Arbiter reads anything (engine: Roles every process has).

## Roles
The engine's User and Arbiter, and:
* **Hunter** - author of the diagnosis and the fix. Lives for the whole bug.
* **Reviewer** - reviews the diagnosis and the fix. Lives for the whole bug.

The Arbiter stays although there are only two actors. Why: if the Hunter sends the Reviewer its turns,
one party writes the reviewer's prompt and judges its own review. The Arbiter costs a reply line per
turn; it buys neutrality.

Both actors live across both stages. Why: a spec spawns a fresh Coder per phase by default because a
session kept across many phases re-reads its whole history. A bug has two stages and one fix. The Hunter's
context of the hunt is the asset the fix needs, and a Reviewer who approved the cause is the one to
check the fix against it.

## Artifacts

### report.md
Written and signed off by the User.
```
# <bug title>

## Symptom
<what goes wrong, observed where, how often>

## Evidence
<runs, logs, metrics, commits and build ids - everything seen, with where it lives>

## Fixed means
<the observable that proves the fix. For a rate-based symptom: the live check and its sample size
(see The fix gate)>

## Environments
<what the Hunter may change: deploy to a test cluster, run a load tool, commit diagnostic code>

## Known and open
<suspicions, ruled-out causes, and what nobody knows yet>

## Out of scope                                   (optional)
<what the Hunter must not change, even if the fix would be easier>
```

### hunt/NN-diagnosis.md
Owned by the Hunter, numbered from `01`. Every claim is under the engine's Research rule: a FACT with
its source or a RESULT with the command and its output. A cause read from the code, never run, is a
hypothesis, not a finding.
```
# Diagnosis <NN>
Outcome: fix | exit

## Reproduction
<command, environment, output. It fails today, and it shows the mechanism, not just the symptom>

## Where it dies
<the point in the path, with the RESULT that localizes it>

## Root cause
<the causal chain, step by step, from trigger to symptom>

## Evidence accounted for
<each observation in report.md's Evidence, and how the cause explains it>

## Ruled out
<each rival cause, and the RESULT that killed it>

## Diagnostic commits
<sha - what it adds - keep or revert, and why>

## Fix
<what changes and the regression check that fails today. For exit: why the fix is a design change>
```

### review/hunt/00-request.md
```
- **Subject:** hunt/01-diagnosis.md
- **Build:** <command> - green, <n> tests passed        (only if diagnostic code was committed)
```

### review/fix/00-request.md
`fix` is a code topic. Its live check is reported as `Live:`, in place of `Gates:`, because it needs its
result from before the fix too.
```
- **Subject:** git diff <from>..<to>
- **Red:** <red commit sha> - <check command> - fails: <the failure, one line>
- **Build:** <command> - green, <n> tests passed
- **Live:** <run> - before <result>, after <result>      (only when report.md's Fixed means asks for it)
- **Diagnostic commits:** <sha> kept (<why>) | <sha> reverted in <sha>
- **KB:** kb.py status --since <sha> - clean                 (only when the project has a knowledge base)
```

The hunt's closing verdict carries the outcome, e.g. `Verdict: approved hunt/02-diagnosis.md | exit`.
Its reply's verdict field reads `approved exit` (or `closed exit`).

## Turns
The engine's A turn, with this table:

| state | role | folder | the turn |
|---|---|---|---|
| `hunt:Draft` | Hunter | `hunt/` | reproduce, localize, root-cause, write `01-diagnosis.md`, open `review/hunt/` |
| `hunt:Review` | Reviewer | `review/hunt/` | review the diagnosis the newest file names for soundness |
| `hunt:Answer` | Hunter | `review/hunt/` | answer every finding; a new diagnosis file if any fix was accepted |
| `fix:Draft` | Hunter | `review/hunt/` | red commit, fix, build green, docs and knowledge base, open `review/fix/` |
| `fix:Review` | Reviewer | `review/fix/` | review the commit range the newest file names; run the red/green check only |
| `fix:Answer` | Hunter | `review/fix/` | fix what was accepted, commit, build green, answer |

## What counts as a Blocker

### Reviewing a hunt
A finding is a Blocker when:
* the reproduction shows the symptom through a mechanism other than the claimed cause. "I can make
  it fail" is not "this is why it failed"
* the causal chain has a step that is asserted, not shown
* an observation in `report.md`'s Evidence is left unexplained
* another cause would produce the same evidence and the diagnosis does not rule it out by a RESULT,
  whether the Hunter named it or not. The finding names the rival and the evidence it fits
* the fix's regression check would pass on today's code

Anything else is a Nit.

### Reviewing a fix
The Reviewer runs **exactly two commands**, and `kb.py status`, in place of the engine's one targeted command: the
regression check at the red commit, where it must fail, and at the head of the range, where it must
pass. They never rerun the build or the suite, which is trusted as reported. Why: for a feature, the
build is the author's evidence. Here the red and green of one check are the evidence of the fix
itself, and they are cheap to run. `kb.py status` spends no tokens.

A finding is a Blocker when:
* the check does not fail at the red commit, or fails for a reason other than the diagnosed cause
  (read the failure, not just the exit code)
* the fix treats the symptom, not the cause, e.g. a retry, a longer deadline or a swallowed error
  that hides the loss, unless the approved diagnosis showed a residual loss is inherent
* a diagnostic commit is neither kept with a reason nor reverted
* a card or a skill says something the fix made untrue, or `kb.py status --since <sha>` is not `clean`
* a live check that `report.md` asks for is missing, or its sample is too small (see The fix gate)
* the change is wrong, introduces a problem of its own, or breaks the project's rules

### The fix gate
A fix is proven by a check that fails on the red commit for the diagnosed reason and passes after
the fix. Prefer a deterministic test. When the bug shows only under live conditions, the live check
is the Hunter's RESULT, trusted as reported like the build. Before and after are both recorded.

For a rate-based symptom, the "after" run must be large enough that the old rate would have produced
**at least 5** failures, and it shows 0. At an expected 5, a zero is chance about 0.7% of the time
(e^-5). A run that small or smaller proves nothing.
