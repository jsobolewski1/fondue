# engine - the machinery every fondue process runs on

A **process skill** takes one unit of work through fixed stages, with AI sessions in roles that review each other's work. `spec` (a feature) and `hunt` (a bug) are process skills. This file is what they share: state, turns, replies, rulings, review, and commits. A process skill defines only what differs, the hooks listed at the end, and says so in its own words.

Every role and the Arbiter read this file together with their process skill. Where the two conflict, the process skill wins, and it says so in place.

Why a shared engine: when one skill borrowed the other's machinery by reference, every change to the first silently changed the second, and the list of what "does not apply" went stale.

## Glossary
Every term below is used in this meaning only. A process skill adds its own terms.

* **Spec** - one unit of work, whatever the process: a feature, a bug. Its folder is `fondue/<kind>/<spec>/` at the project root, where the process skill names `<kind>`, e.g. `specs` or `bugs`.
* **Stage** - a named part of the process. The process skill lists its stages. `done` and `abandoned` end every process.
* **Step** - whose turn it is inside a reviewed stage: `Draft` (the author produces the work), `Review` (the reviewer writes findings), `Answer` (the author answers them).
* **Role** - User (human), Arbiter, and the roles the process skill defines.
* **Author** - the role whose work is under review. **Reviewer** - the role that reviews it. The process skill names both for each topic.
* **Turn** - one piece of work by one role, started by `Your turn.` and ended by a reply.
* **Topic** - one thing under review, and its folder `review/<topic>/`.
* **Round** - one review and the answer to it.
* **Subject** - the exact thing a round reviews: a file, a list of files, or a commit range.
* **Finding** - one numbered problem in a review, cited as `<file>#<id>`, e.g. `01-review.md#3`.
* **Thread** - a finding and every later re-assertion of it, named by the `<file>#<id>` that first raised it.
* **Verdict** - the fixed last line of every review and answer. It decides the next state.
* **Ruling** - a User decision recorded in `99-user.md`. Binding on every role. A role never argues against it; new evidence that bears on it is a User question.
* **Question** - a decision that belongs to the User, not a role: what the spec delivers, anything a ruling settled, or a change to an approved artifact. An author, or a role in a turn with no verdict, raises it with a QUESTION reply, and a reviewer raises it in a finding (see User questions). A ruling settles it.
* **Starting document** - what the User writes and signs off for the process to start from, e.g. a brief or a bug report. The process skill names it.
* **Advisor** - a read-only session the Arbiter spawns when the User asks, to give the User a second opinion (see Advisors). It is not a role: it takes no turn and writes nothing in the spec.
* **FACT** - a claim with its source stated. **RESULT** - a claim with the command that was run and its output.
* **Knowledge base** - the project's map of what its code already has, in `fondue/kb/` (see Knowledge base). **Card** - its page for one module.

## The spec folder
```
fondue/<kind>/
  <spec>/
    current-state.txt
    roster.md
    99-user.md
    stats.md
    review/
      <topic>/   00-request.md, 01-review.md, 02-answer.md, ...
    question.md                                 (only while a question outside any finding is pending)
    advice/      01-<agent>-<model>-<effort>.md, ...   (only once an advisor was asked)
    ...          what the process skill adds
  archive/
    <spec>/
```
`fondue/<kind>/archive/` is history, never current truth.

## Starting a spec
The User opens a session and loads a process skill. That session is the Arbiter. It walks the User through the start, and asks only what the User has not already said: in the opening message, or in an earlier answer that settles a later question too, e.g. "opus at high for every role". It asks **one question at a time**, with the default as the first option. It uses the AskUserQuestion tool when the session has one; when the choices outnumber what the tool takes, it lists them in text and takes a free answer. An option is a whole answer, e.g. a complete roster row, so most questions take one pick. Why one at a time: a block of questions gets skimmed, and the roster is where a careless answer costs the most, on every turn of the spec.

**The most recent spec** of this kind is the one with the highest number when the folders are numbered, `archive/` included. Otherwise it is the one whose `roster.md` git last committed. A project with no spec of this kind has none, and every default that would come from it falls away.

In this order, it:
1. **Continue or start.** When the User neither names a spec nor asks for a new one, and specs of this kind are in progress (any `fondue/<kind>/*/` outside `archive/`), it lists them with the state each is in, and asks whether to continue one or start a new one. With none in progress it starts a new one without asking. To continue a spec, it skips the steps below, except as this list says:
   - **step 2** runs for every adapter the roster names.
   - **The Arbiter row** gets this session's model, and the effort the User gives when asked.
   - **Handles.** Every `agent <id>` Handle cell goes to `-`, because a Claude role died with the session that spawned it, and each such role is spawned anew before its next turn. An adapter's session outlives the Arbiter, so its handle stays.
   - **Anything pending is settled first.** Before sending any turn, it reads the last `stats.md` row and checks for `question.md` and `reopen.md`. A CONFLICT, QUESTION or BLOCKED with no ruling after it in `99-user.md` goes to the User, as On every reply says.
   - **A turn that was in flight** on an adapter may have finished. Its Reply location is read, and a reply found there is handled under On every reply.
   - **A spec still in its first state** gets step 9, unless its starting document is already signed off.
2. **Agents.** It reads `integrations/agents/contract.md` at the plugin root. If the User's agents were never set up, it runs the first-run setup that file describes.
3. **Name.** It asks for the spec's title, and proposes the folder name. When any spec folder of this kind begins with a number, `archive/` included, the name is `<NNN>-<slug>`, one above the highest; otherwise it is `<slug>`. The slug is a few lowercase words of the title joined by `-`. The User may change it. A name taken by any spec of this kind, archived ones included, is refused, because `done` moves the folder into `archive/`.
4. **The process skill's questions before the roster**, if it has any.
5. **The roster, role by role**: the Arbiter first, then the roles in the order the process skill lists them. Each role gets one question, for its agent, model and effort. The options are, in order:
   - the process skill's default for the role;
   - the role's row in the most recent spec, if it differs;
   - a row on each agent registered in `~/.config/fondue/integrations/agents/`.

   When the process skill has no default, the first option is the Arbiter's own model at `high`. When there is only one option, "Other" is the second. For the Arbiter's own row, the model is the session's own, and only the effort is asked: a session cannot see its own effort. A role on an adapter then gets the questions its adapter asks at roster time (Agent settings).
6. **Skills.** It lists the project's skills, `.claude/skills/*/SKILL.md`, and the User's, `~/.claude/skills/*/SKILL.md`, each with its description. It asks which ones every role loads, then whether any role loads more. The most recent spec's Skills section is the default. The path of every chosen skill is recorded next to its name (Starting a role).
7. **The process skill's questions after the roster**, if it has any.
8. **Confirm.** It shows the folder name, the answers to the process skill's questions, and `roster.md` as it will be written. A change goes back to that one question. On the User's yes, it:
   - creates the spec folder with the process skill's layout;
   - writes `roster.md`;
   - writes the starting document's template, filled with the title and the answers it takes. That keeps them on disk, however the document is drafted;
   - writes the process skill's first state into `current-state.txt`.

   `99-user.md` and `stats.md` are appended to, and are created on their first entry, `stats.md` with its table header.
9. **The starting document.** It asks how the User wants to draft it. Whichever way is chosen, the document is the User's: they edit it, and only they sign it off.
   - **Myself.** It waits for the sign-off.
   - **Interview me.** It asks for the template's sections one at a time. It writes the User's answers in their words, then shows the whole document for edits.
   - **From a source.** The User points to notes, an issue, a document or this conversation. It drafts from that source and the answers already given, nothing else.
   - **With research.** It reads the code, the knowledge base and the sources the User names. It writes only FACTs about what exists, with their anchors, under the template's context or evidence. This is its research for the User (Roles every process has): what it finds reaches the roles only through the document the User signs.

   In every way, the Arbiter's own words are limited to restating the source and recording what exists. The goal, the scope, any decision, any permission and anything marked for the process skill's checks are the User's words. It proposes no approach. What the source leaves open goes under the template's open section, unmarked, and the User adds any mark a process skill defines. Why: a starting document the Arbiter shaped would steer every role while carrying the User's signature. And the sign-off checks a process skill runs on it would test the Arbiter's own judgement.

The User starts only the Arbiter. The Arbiter spawns every other role.

## State

### current-state.txt
Owned by the Arbiter. One line:
```
<stage>[:<qualifier>][:<Step>]
```
The process skill says which stages carry a qualifier (e.g. a phase number) and which carry a Step. The Arbiter rewrites the line after every reply, **before** sending the next `Your turn.`. That is what makes a two-word message enough.

### Transitions
The Arbiter picks the next state from the reply line alone and never opens the artifact. These rows hold in every process. The process skill adds its own, above all the row that says where a topic goes when it closes.

| state | reply | next state |
|---|---|---|
| `<x>:Draft` | DONE, `request opened` | `<x>:Review` |
| `<x>:Review` | DONE, `changes-requested` or `approved-with-fixes` | `<x>:Answer` |
| `<x>:Answer` | DONE, `next-round` | `<x>:Review` |
| `<x>:Review` / `<x>:Answer` | DONE, `approved` / `closed` | as the process skill says for that topic |
| any | User rules to abandon the spec | `abandoned` (see Closing a spec) |
| any | CONFLICT, QUESTION or BLOCKED | unchanged (see On every reply) |

`<x>` is the state without its Step, e.g. `plan` or `implementation:03`.

## Artifacts every spec has

### roster.md
The process skill, then the agent, model and effort of each role, the handle of each spawned role, and the skills of each role.
```
# Roster

**Skill:** fondue:spec

| Role | Agent | Model | Effort | Handle |
|---|---|---|---|---|
| Arbiter | claude | opus | high | - |
| Architect | claude | fable | high | agent a3c99aa3cf5f0bd4a |
| Architecture Reviewer | codex | gpt-5.6-sol | xhigh | session 01a0bf4c-f5ae-7851-81d7-13355d6fae9a |
| Coder | claude | opus | high | - |

## Skills

- **all:** <skill>, <skill>
- **Coder, Code Reviewer:** <skill>

## Agent settings

- **Architecture Reviewer:** <what its adapter asks to be decided up front, e.g. Codex's sandbox and network>
```
Agent is `claude` or the name of an adapter in `~/.config/fondue/integrations/agents/`. For a Claude role the model is the spawn call's name: `sonnet`, `opus`, `haiku` or `fable`. Effort is one of `low`, `medium`, `high`, `xhigh`, `max`. The **Skill:** line tells a new Arbiter session, or a role, which process the spec runs. Agent settings is there only when a role's adapter asks for decisions at roster time.

The Arbiter writes the handle into the role's Handle cell when it spawns the role, `agent <id>` for Claude and `session <handle>` for an adapter, and replaces it when it spawns a new session for the role. Until then the cell is `-`. The handle is how it sends the role later turns and finds its figures for `stats.md`.

### 99-user.md
Every ruling, at any stage, in the User's own words. Appended and never rewritten. It sits at the spec root so that every role can read it.
```
## <YYYY-MM-DD> <state>[ | settles <file>#<id>]

**Asked:** <the question put to the User>

**Ruling:** <the User's words>

**Carried out as:** <what the Arbiter did beyond recording it, e.g. a file moved or a line changed>   (optional)

**Evidence:** <a role's file that the ruling retires, moved here verbatim>                         (optional)
```
Only **Ruling:** must be the User's own words. The Arbiter writes the two optional lines, and they say only what was done or what was retired, never why the User ruled.

### stats.md
Owned by the Arbiter, one table row per finished turn, per advisor's answer, per research session it spawns for the User, and per piece of work it does after the last review (e.g. a handover it writes). No other role reads it.
```
| Date | Role | Model | State | Result | Counts | Tokens | Time |
|---|---|---|---|---|---|---|---|
| 2026-09-30 | Code Reviewer | fable/high | implementation:01:Review | approved | 0 Blocker, 0 Nit | out 6.33k · write 103k · read 630k · in 228 | 2m |
| 2026-09-30 | Coder | opus/high | implementation:01:Draft | BLOCKED: host firewall rule for port 8068 missing | - | out 16.6k · write 120k · read 5.43M · in 98 | 11m |
| 2026-09-26 | Architecture Reviewer | codex gpt-5.6-sol/xhigh | pre-plan:Review | approved-with-fixes | 2 Blocker, 1 Nit | in 3.14M (2.97M cached) · out 22.7k | 8m |
```
State, Result and Counts come from the reply line. Result is the verdict for DONE, and otherwise `CONFLICT: <file>#<id>`, `QUESTION: <refs>` or `BLOCKED: <the reply's sentence>`. An advisor gets a row too, with the Role `Advisor`, the State it was asked in and the Result `advice`. So does a research session the Arbiter spawns for the User, with the Role `Researcher` and the Result `research`. Both take Counts `-`, and Tokens and Time as a role on that agent does. The written paths stay out: they are on disk and in git. A `|` inside a cell is written `\|`.

For a Claude role, the last two cells are the output of `turn-stats.py` next to this file, run from the project directory with the role's agent id (`--all` prints every turn). The transcript it reads is at `~/.claude/projects/<project>/<arbiter-session-id>/subagents/agent-<agent-id>.jsonl`, where `<project>` is the working directory with `/` replaced by `-`, e.g. `/home/x/project` -> `-home-x-project`. Run it after the task-notification that the agent finished, not on its reply: the reply lands before the transcript's last usage lines, and figures taken then are short.

For a role on another agent, they are the output of its adapter's Stats, or `- | -` if the adapter has none. It is not comparable with a Claude row.

`kb.py write` (Knowledge base) makes model calls that no role's transcript holds. After every reply to a turn the process skill says may run it, the Arbiter runs `kb.py usage --since <the time it sent that turn>` and adds one more row: the Role `KB writer`, as Model the `model:` it prints, the same State, the Result `cards written`, Counts `-`, as Tokens its last line, and Time `-`. It adds no row when it prints `calls: 0`.

Never take token numbers from the role itself: a session cannot count its own tokens.

## Research
Every research entry, in whatever file the process skill names, is either a FACT with its source stated, or a RESULT with the command run and its output. Never a guess.

A claim about **a mechanism the spec does not control** must be a RESULT, e.g. how a build plugin matches a version pattern, or what a test runner does when a filter matches nothing. Documentation and a plausible reading of the source are not sources: run it and record the output. The rule covers the mechanisms a decision rests on, not every detail of the code, which the author of the code will find. Why: a gate built on a misunderstood mechanism is a check that cannot fail, and everything built on it is unverified.

Once a FACT is recorded, no other role researches the same question again. A RESULT may be re-run if it is non-deterministic or expected to have changed.

## Knowledge base
A project may have a knowledge base at `fondue/kb/`, made by the `kb-init` skill: `index.md`, one entry per module and every project skill, and `cards/<module>.md`, what a module offers, where a new thing plugs in, and what not to rebuild. The process skill says which role reads it, and when. A role that reads it:
* **reads `index.md` whole**, then the cards it needs: the modules its work touches, and every module whose entry matches a capability its work needs. Why whole: you cannot search for something you do not know exists.
* **treats a card as where to look, never as a source.** A FACT cites the code a card pointed to, never the card. A card that the code contradicts is out of date, not evidence.
* **skips all of this when `fondue/kb/index.md` does not exist.** Nothing in a process depends on the knowledge base being there.

Who writes it, and how, is in `protocol/kb.md` next to this file. A role that only reads it does not read that file. Its tool, `kb.py`, is `python3 <plugin root>/protocol/kb/kb.py`, run from the project root; from this file it is `kb/kb.py`. `kb.py status` spends no tokens.

## Code turns
A role that writes code commits it during its turns and never stages `fondue/`, except `fondue/kb/` (Knowledge base). It runs the full build with tests at the end of **every** turn that changed code, Draft and Answer alike. A turn is not DONE until the build is green with all tests passing. An answer that only challenges or declines changes no code and reports the last green build.

That run is the only build of the topic: the request and every answer report it, and it is trusted as reported. A gate that the build does not run, such as a live check, is run on the same turns and reported the same way.

The reviewer of code never reruns the build or the test suite. They may run one targeted command as the anchor of a finding, e.g. a mutation that shows a test cannot fail. That is evidence for a finding, not a re-check of the build. The process skill may allow a different set of commands.

## Review

### review/<topic>/
One folder per topic. Every round of that topic lands there. The files share **one** number sequence in the order they were written: `00-request.md`, `01-review.md`, `02-answer.md`, `03-review.md`, ... A number is never reused. The newest file is what the next turn answers.

### review/<topic>/00-request.md
Written by the author to open the first round. Later rounds have no request: the answer that asks for another round names the new subject.
```
- **Subject:** <file> | <file>, <file> | git diff <from>..<to>
- **Build:** <command> - green, <n> tests passed        (code topics)
- **Gates:** <command> - <result>                       (code topics, each gate the build does not run)
- <the process skill's own fields>

<what changed and anything the reviewer must know that no artifact says>
```

### review/<topic>/NN-review.md
Findings and the verdict. Nothing else: no list of what was checked and found fine, no summary. Those are not findings, and every later reader pays for them.
```
## #1 <one-sentence title>

**Severity:** Blocker | Nit

<description, with its anchor>

**Proposed solution:** <what to change>

## #2 <one-sentence title> (re 01-review.md#3)

...

Verdict: changes-requested
```
A finding that re-asserts one from an earlier review of the topic carries `(re <file>#<id>)`, naming the review that first raised it. That origin is the finding's **thread** (see Escalation). A finding without it is new.

The verdict line is one of:
* `Verdict: approved <subject>` - no Blockers. Nits are not applied and no answer follows. A reviewer who wants a Nit applied lists it under `approved-with-fixes`.
* `Verdict: approved-with-fixes <subject> | #2, #4` - see Approval with fixes.
* `Verdict: changes-requested` - at least one Blocker the reviewer cannot approve unseen, or a finding that holds a User question (User questions), whatever its severity.

A process skill may add an outcome to a closing verdict, e.g. `Verdict: approved <subject> | exit`.

### review/<topic>/NN-answer.md
The author answers every finding by its id, one line each where possible. Prose only for a challenge, or for a fix that departs from the proposal, and only as much as the reviewer needs to judge it.
```
- #1 accepted, fixed in <file or commit>
- #2 accepted, fixed differently in <file or commit>: <why>
- #3 challenged: <position, with its anchor>
- #4 declined (Nit)
- #5 deadlocked: <position, with its anchor>
- #6 question: <the decision the User must take, with its anchor>

**Build:** <command> - green, <n> tests passed        (code topics)

**Gates:** <command> - <result>                       (code topics, each gate the build does not run)

Verdict: next-round <subject>
```
The verdict line is one of:
* `Verdict: next-round <subject>` - the reviewer has something new to judge. The subject is the new file, the files touched, or the commit range carrying the fixes, i.e. `git diff <from>..<to>`. Why: without it the reviewer re-reviews work already approved.
* `Verdict: closed <subject>` - only after `approved-with-fixes` when every listed fix was applied as proposed. The subject is the final file, the files, or the topic's full commit range.
* `Verdict: deadlocked <thread>[ | question <refs>]` - see Escalation. The questions are listed when the same answer also asks the User (User questions).
* `Verdict: question <refs>` - see User questions.

### Findings
Every finding has an id (its number in the file), a title, a severity, a description and a proposed solution.
* **Blocker** - must be fixed or challenged. **Nit** - may be fixed or declined, and never blocks approval. What counts as a Blocker for each topic is the process skill's to say. Anything else is a Nit.
* **The description must carry an anchor**: `file:line` for a claim about code, the command and its output for a claim about behaviour, or the line of the spec it contradicts for a claim that something is wrong or missing. A finding with no anchor costs the author a round to prove or disprove, so it is not a finding.
* **A finding that says a third-party mechanism does not exist must show it failing**, with the command and its output. An empty search (an API listing, a grep, a `javap`) shows only that it was not where you looked. Absence of a config key is not absence of a capability: a sentinel value, another entry point or a newer version all look the same to an empty search. Why: the author usually accepts such a finding and designs the capability out. This is the reviewer's half of the RESULT rule, and it binds hardest on a reviewer who cannot see the research.

### Approval with fixes
When every Blocker has a concrete, local proposed solution and none changes the design, the reviewer approves with fixes, listing the finding ids the approval depends on. The author applies each listed fix exactly as proposed and answers `closed`. No further round follows: re-reviewing a fix applied verbatim only confirms what both sides already agreed.

The approval is void as soon as the author challenges a listed finding, fixes it differently, or asks the User about it. The answer is then `next-round`. When the author asks, it is `question`, and the answer after the ruling is `next-round`. A reviewer who cannot state a fix precisely enough to approve it unseen answers `changes-requested`.

### Escalation
A deadlock is a disagreement about **whether the work is right**, and only one sequence makes it: the author challenged a finding, the reviewer re-asserted it with `(re <origin>)`, and the author still disagrees. The author then writes their position once more as `#<id> deadlocked: ...`, answers every other finding, ends with `Verdict: deadlocked <origin>` and replies CONFLICT. Neither side writes on that finding again.

A finding the author accepted is not on that path. If the reviewer re-asserts it, the author fixes it again or challenges it, and a challenge starts the sequence. A disagreement about **what the spec should deliver** is never a deadlock: it is a User question, asked the first time it appears. Why: a scope question argued as a deadlock reaches the User rounds late, after both sides have spent those rounds on a decision neither of them can take.

The Arbiter sends the User exactly this, and the User reads the files:
```
CONFLICT on <thread> in review/<topic>/: positions in <files from the reply>. Your ruling?
```
The Arbiter neither summarises, quotes nor rules. After the ruling, the author gets the next turn in the same Answer state and writes a new answer applying the ruling, with a normal verdict.

A **new** finding on new evidence is never a deadlock, however late it arrives.

### User questions
Some decisions are the User's whatever the evidence says: **what the spec delivers** (its goal, its scope, what counts as done), anything a ruling already settled, and **a change to an approved artifact** (the process skill names which artifacts carry an approval). A role that meets one neither decides it nor argues it across rounds. The question is asked the first time it appears, and it is always on disk:
* **an author** who meets one in a finding, whether they would fix, challenge or decline it, answers every other finding, writes `#<id> question: <the decision, with its anchor>`, ends with `Verdict: question <refs>` and replies QUESTION. A decision an author meets outside any finding goes into `question.md`, as in a Draft turn.
* **a reviewer** never replies QUESTION. They write the finding as usual, say in it that the decision is the User's, and end with `changes-requested` whatever its severity, so that an answer follows. The author then asks. Why: a review that stopped on a question would leave the author's next turn with no review to answer.
* **a role in a turn with no verdict** (a Draft) writes nothing that the decision shapes. It writes the decision and its anchor into `question.md` at the spec root and replies QUESTION.

A role that writes code ends a QUESTION turn at its last green commit. An answer may hold several questions; the verdict, the reply and the Arbiter's message list them all.

**An agreed change is a question too.** When the author and the reviewer agree that an approved artifact must change, the author asks the User to approve it as an amendment, unless the process skill routes that change elsewhere (spec: an approach that cannot work reopens). The approved file is not edited, unless the process skill says otherwise for it: the ruling amends it, and every role reads the amendment in `99-user.md`. Why: an approved file carries its approval, so editing it would make it say something nobody approved. And redoing the work for a change both sides agree on throws away everything the change does not touch.

The Arbiter sends the User exactly this, and the User reads the files:
```
QUESTION in <state>: <refs from the reply>. Evidence in <paths from the reply>. Your ruling?
```
The Arbiter neither summarises nor rules. It records one ruling per question with `settles <file>#<id>`, or moves the text of `question.md` into the **Evidence:** of the first of its rulings and deletes the file. Once every question has a ruling, the same role gets the next turn in the same state. An author writes a new answer that applies the rulings, as after a CONFLICT, with a normal verdict. A Draft turn resumes its work.

When one answer holds both a deadlock and a question, the author replies CONFLICT and appends `| question <refs>` to the line. The Arbiter puts both to the User.

### Advisors
At a CONFLICT, at a QUESTION, or at any other time, the User may ask the Arbiter for advisors: second opinions from sessions outside the spec, on an agent, model and effort the User names. An advisor:
* **is spawned like a role** (Starting a role): on Claude with `fondue:role-<effort>`, and on another agent through its adapter's Start, read-only. It gets no Handle cell and is never sent `Your turn.`; the Arbiter keeps its handle in its own context, for a follow-up.
* **is read-only.** It writes nothing in the repository, changes no code and commits nothing. Its final message is its whole output.
* **gets one fixed prompt, the same for every advisor on that question.** The prompt says that the session is an advisor and not a role: it loads no fondue skill, it is read-only, and its final message is its whole output. Then it names:
  - the thread, the question (`<file>#<id>` or `question.md`), or the User's own question;
  - the files to read: the starting document, `99-user.md`, the research, and every file on the thread or in the reply's evidence, with the subjects they cite;
  - the process skill's rules for what counts as a Blocker.

  It asks four things: which position is right and why, with anchors; whether it is a Blocker; the resolution the advisor would propose if neither side is right; and what both sides missed. The prompt never says which way the User leans. Why: an advisor that knows the User's lean tends to confirm it.

The Arbiter saves each advisor's final message verbatim to `advice/NN-<agent>-<model>-<effort>.md`, e.g. `advice/02-claude-opus-xhigh.md`, numbered across the spec. It relays the advice to the User and adds the advisor's row to `stats.md`. At the User's request, the Arbiter sends an advisor a follow-up, read-only like its start: another advisor's file by its path, and a request to respond. Its answer is saved the same way. Roles never read `advice/`: what the User takes from it reaches them through the ruling.

## Roles every process has
* **User** - owns the spec. Writes what the process starts from, picks the roster, rules on escalations, questions and blockers.
* **Arbiter** - runs the process: spawns roles, sends turns, keeps `current-state.txt`, `stats.md` and `99-user.md`, commits the spec, and goes to the User for a CONFLICT, a QUESTION, a BLOCKED or a User decision. On its own account it never reads, analyses or judges what a role produced: the reply line is all it needs. It never rules on the merits, and it never builds or tests. A finished turn is not news to the User, because the artifacts already say what happened. The User may hold this role, but an AI is preferred. One session for the whole spec.

  **When the User asks, the Arbiter researches for the User.** It reads the artifacts, the code and the sources, runs read-only commands, may spawn read-only research sessions, and answers the User directly. What it finds reaches the roles only through the User: in a ruling, or in a starting document the User amends. It never writes into a role's artifact or message. Why: the User's questions steer the spec and deserve real research, while the roles still see nothing but what the User put on the record, so the Arbiter stays neutral towards them.

  A process skill may give the Arbiter work after the last review has closed, e.g. writing the handover. Then no review is left for its neutrality to protect.

## Communication
Sessions share nothing but the artifacts on disk. A message says **whose turn it is** and nothing more.

**Never put spec content in a message**: no summaries, findings, file contents or restated decisions. A role that needs to tell another role something writes it in its artifact. Why: content in a message duplicates an artifact, is paid for on every hop, and lets a role act on something never written down. An advisor's prompt (Advisors) is the one exception: it names a question and the files to read, and restates nothing from them.

A role exchanges messages with the Arbiter only, never with another role, and never spawns a subagent of its own. A command it is not permitted to run is a BLOCKED, not something to route around.

### Starting a role
The Arbiter spawns each role right before its first turn, and again whenever the process skill calls for a fresh session.

**On Claude**, it uses the Agent tool with `run_in_background: true`, `subagent_type: fondue:role-<effort>` and `model: <model>`, both from the role's `roster.md` row. It records the agent id in `roster.md` and sends every later turn to that id with SendMessage (load it with ToolSearch if it is deferred). The Agent tool always creates a new session, so it is never used to send a turn. The role starts with an empty context. It dies with the Arbiter session. Re-spawning it is cheap, because everything it knew is on disk and `current-state.txt` tells it where the spec is.

The spawn call has no effort parameter: effort comes only from the agent definition. So the five agent types `fondue:role-{low,medium,high,xhigh,max}` must exist before the Arbiter session starts, because agent types load at session start. The fondue plugin ships them, for every process skill. Each definition sets only `effort` and a one-hour prompt cache (`experimental.cacheTtl: 1h`), and the model passed on the spawn call overrides the definition's. Why the hour: a subagent's cache otherwise lives five minutes, and a role waits longer than that for every review, so each of its turns began by re-writing its whole context to the cache. Claude Code ignores the hour while a subscription draws on usage credits. If a type is missing, the Arbiter stops and tells the User. It never spawns at a different effort.

The spawn prompt is the role's first turn:
```
Load the fondue:<process skill> skill. Your role is <role>. Spec: <path to spec folder>. Your turn.
```
The role loads the process skill, this file, and the skills `roster.md` gives it, then takes the turn like any other.

**On another agent**, the role is started and sent its turns through its adapter's Start and Turn, as `integrations/agents/contract.md` says. Its prompt names each skill by path, `Read <skill dir>/SKILL.md and follow it as the <name> skill.`, because no other agent can load a Claude Code plugin's skills. The Arbiter knows the directory of each fondue skill, since they sit together under the plugin's `skills/`. It records the path of each project or User skill when it fixes the roster (Starting a spec, step 6), and asks the User only for a skill outside those folders.

### A turn
```
Your turn.
```
That is the whole message, and it always starts a new turn, however the harness words it (e.g. "sent a message while you were working"). The state has changed since the role's last reply, so it never repeats that reply. The role:
1. reads `current-state.txt`
2. finds its work for that state in the process skill's turn table
3. lists the folder the table names. The newest file - the highest number, not the latest modified - is what the turn answers.
4. reads `99-user.md` if it exists
5. does the work, writes the artifact, replies

### Reply
One line. When a turn has more than one kind to report, it sends the higher one: **CONFLICT outranks QUESTION outranks BLOCKED outranks DONE**.
```
DONE <state> | wrote <paths> | <verdict> | <counts>
CONFLICT <state> | wrote <paths> | thread <file>#<id> deadlocked | positions in <every review and answer file on the thread>[ | question <refs>]
QUESTION <state> | wrote <paths> | question <refs> | evidence in <paths>
BLOCKED <state> | <what is missing or failing, one sentence>
```
* `<paths>` are relative to the repository root, e.g. `fondue/specs/json-top/review/phase-01/00-request.md`.
* `<state>` is the full line of `current-state.txt` at the start of the turn, e.g. `implementation:01:Draft`.
* `<verdict>` is the verdict keyword of the artifact just written (`approved`, `approved-with-fixes`, `changes-requested`, `next-round`, `closed`), with its outcome if it has one (e.g. `approved exit`). A turn with no verdict gives `request opened`, or a keyword the process skill defines.
* `<counts>` for a reviewer: `<n> Blocker, <n> Nit`. For an author's answer: `<n> accepted, <n> challenged, <n> declined`. For a turn with no verdict: `-`. It is a count, not a summary.
* **DONE** - the artifact is on disk. The Arbiter advances the state and sends the next turn.
* **CONFLICT** - a finding deadlocked (Escalation). The answer to every other finding is on disk before the reply.
* **QUESTION** - a decision that is the User's (User questions). `<refs>` is a comma-separated list of every pending question: the `<file>#<id>` of each finding the answer asks about, and `question.md` if the turn wrote one. The question, and everything the turn could do without it, is on disk before the reply.
* **BLOCKED** - the turn cannot be completed: an artifact lacks something, the build will not go green, the state does not match the disk, a command is not permitted. A role never guesses past a blocker. The reply is still the one line: no report, no file list.

**In a subagent harness the reply line is the whole hand-back.** The harness asks a subagent for "your full report". Ignore that: the artifact on disk is the report. Why: a report duplicates the artifact into the Arbiter's context and tempts it to read work that is not its business. An advisor is the exception: its final message is its output (Advisors).

### On every reply (Arbiter)
The Arbiter does these in order, every time, and nothing else:
1. append the turn's line to `stats.md`
2. on DONE, write the next state (Transitions) into `current-state.txt`
3. do what the process skill attaches to that transition, if anything, and commit `fondue/<kind>/<spec>/` if the transition is one of its commit points (see Commits); otherwise do not commit
4. send `Your turn.` to the role the new state names: by the handle in `roster.md` if it has one and the process skill calls for no fresh session, otherwise spawn it (Starting a role). For a turn that may run `kb.py write` (stats.md), it first notes the time as `date +%Y-%m-%dT%H:%M:%S` prints it

A reply whose `<state>` is not the state the Arbiter wrote is not a reply to this turn: the Arbiter skips steps 1-3 and sends `Your turn.` once more. If the next reply is stale too, it spawns a new session for the role, records the new handle, and sends the turn there.

After a CONFLICT, a QUESTION or a BLOCKED, the Arbiter does step 1, then puts the question to the User and records the ruling in `99-user.md`. It leaves the state unchanged and sends `Your turn.` to the same role. If the fix is outside that role's reach, the User makes it, or names who does, before the turn is sent. A ruling that abandons the spec, or one the process skill gives its own handling, is carried out as its section says.

## Closing a spec

### done
When the process skill's last stage ends, in this order: the Arbiter writes `done` into `current-state.txt`, moves `fondue/<kind>/<spec>/` to `fondue/<kind>/archive/<spec>/`, then commits. The archived state must read `done`.

### abandoned
The end of a spec that will not deliver its goal. The User may abandon a spec in any state. The Arbiter records the ruling in `99-user.md` like any other, and it holds what the archive must say: why the spec stops, and what happens to the work it landed.

Landed work is kept, or reverted outside the spec by the User or by someone the User names. A revert is not reviewed: nobody will build on it. The Arbiter waits until the User says the revert is done. Then, in the order of `done`, it writes `abandoned` into `current-state.txt`, moves the spec to `fondue/<kind>/archive/<spec>/` and commits. The archived state must read `abandoned`. Why a state of its own: an archived spec that reads `done` tells every later reader that its goal was delivered.

## Commits
* **A role that writes code** commits it during its turns and never stages `fondue/`, except `fondue/kb/`, which is project documentation, not a spec.
* **Arbiter** commits `fondue/<kind>/<spec>/` at the commit points the process skill names, and once more at `done` or `abandoned`, after the move to the archive. Work the process skill gives it after the last review, e.g. a handover document, it commits on its own, never with a spec folder.

A project may keep its specs out of git. If `git check-ignore -q fondue/<kind>/<spec>/` succeeds, the Arbiter makes none of the spec commits. The check is on the spec folder, because a project may ignore one kind, e.g. `fondue/bugs/`, and still commit the rest of `fondue/`. Code commits are unchanged either way. No part of the process may depend on a spec commit.

## Hooks: what a process skill defines
* its **kind**: the folder under `fondue/` its specs live in, and its **starting document** with its template
* its **start questions**, asked before and after the roster (Starting a spec), and its **default roster**, if it has one
* its **stages**, in order: the first state written at start, which stages carry a qualifier and a Step, and the stage whose end leads to `done`
* its **roles**: what each does, how long each session lives, when a role gets a fresh session, and who reads and writes each of its artifacts
* its **folder layout** beyond the spec folder above, and its artifacts
* its **transitions** beyond the engine's, including where each topic goes when it closes
* its **turn table**: for each state, the role, the folder it lists and the work
* its **topics**: for each one the author, the reviewer, the subject, the request fields beyond `Subject`, `Build` and `Gates`, and **what counts as a Blocker**
* any **reply keywords** for turns with no verdict, and any **outcome** on a closing verdict
* what the Arbiter **does on a transition** besides writing the state, and its **commit points**
* any **ruling with its own handling**, beyond abandoning the spec
* which of its artifacts **carry an approval**, so that changing one is a User question
* any **work the Arbiter does after the last review** has closed
