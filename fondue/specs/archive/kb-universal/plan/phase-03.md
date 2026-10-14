# Phase 3 - Writing and checking the cards

After Phase 2 every module has a pack. This phase gives the writer a prompt worded for any code, keeps a Java-only module's prompt byte for byte, checks the names in a card of any language against the code, and measures what a card of the new packs costs. It then writes the samples' cards, and the documents record what was measured.

plan.md decisions delivered: D8, D9, D10, and the Phase 3 section. This phase spends model calls: about 40 cards, about $3 on Sonnet.

## Essential knowledge

* **Phase 1 and 2's model** (phase-01.md, phase-02.md): `Module.kind` is `"build"` or `"dir"`; `declarations(m)` sends `.java` and `.proto` to their readers and every other source to `generic_skeleton`; a directory module's pack has `## Wiring` from its build and manifest files and `## Possible references in other modules (lines that hold a name only this module declares; not evidence of a dependency)`; its header's dependency lines are `-`.
* **The prompt today** (plan research R9): `card-writer.md` at `1bc80fe` is 41 lines, 3,164 bytes, ending in one newline; `call_writer` passes its text as `--system-prompt` (kb.py:475). Its Java-shaped lines are 1 (the input: "declarations with method bodies dropped, where other modules construct its types"), 28 (Boundaries: "what it depends on and what depends on it, from the input"), 35 (backticks: "a project type, or `Type.member`, ... (a class, interface, record, enum or proto message header)"; "name that file from \"Constructed in other modules\"") and 37 (extension mechanisms: "an interface with several implementations, a registry, a sealed hierarchy, a DI factory, a dispatch table").
* **The dead-name check today** (kb.py:596-642): backticks matching `` `([A-Z]\w*)(?:[.#](\w+))?(?:\(\))?` `` must be a type `TYPE_DECL` (kb.py:170) finds in a `.java` or `.proto` file, and a member must appear as a word in that type's files; a backtick holding a `/` must be an existing path. Since Phase 1 the types come from build-kind modules only.
* **What `kb.py usage` measures** (plan research R10): one line per call in `fondue/kb/.runs/usage.jsonl` with `in`, `write`, `read`, `out`, `cost_usd`; a call's input is `in + write + read`. `cmd_estimate` counts `len(pack) / CHARS_PER_TOKEN + WRITER_OVERHEAD` (1,800) per module and `WRITER_OUTPUT` (1,500) per card (kb.py:545-558). So characters per token for a set of modules is `sum(len(pack)) / (sum(in + write + read) - calls * 1800)`, with the packs taken by `kb.py pack` before the write.
* **The ruling of 2026-10-14** (`99-user.md`) amends plan.md's Phase 3 gate: a Boundaries entry's evidence is a build or manifest file in the pack, or a project skill; a possible-reference line is evidence for an extension point only, never for a boundary.
* **The Java pilot's cost** (`skills/kb-init/design-notes.md`): $0.07 to $0.15 a card on Sonnet; `CHARS_PER_TOKEN = 2.5` was measured on Java skeletons (kb.py:40).
* **The sample Java project's directory modules** (plan research R4, R12): `deploy` holds shell scripts and `Dockerfile.*`, `scripts` Python and shell, `specs` 3 `.java`, 7 `.proto`, 1 `.py` and 2 `.sh`. Each has a file the new reader reads, so each gets `any code`.
* **The reader's sizes on the samples' directory modules** (plan research R6): C 227,559 chars of skeleton, the shell project 12,343, fondue 6,801, the Java + Vue project's web part 87,945, hono 413,296, the sample Java project's directory modules 68,218.

## Technical decisions

### 1. One prompt file, two variants
`card-writer.md` marks a line that belongs to one variant with a prefix: `[java] ` for the Java-only variant, `[any code] ` for the other. A function `prompt(variant)` returns the file's lines with the other variant's lines dropped and its own prefix removed; unmarked lines are in both. The Java-only variant is byte-identical to `git show 1bc80fe:protocol/kb/card-writer.md`, final newline included.

The marked lines, each `[java] ` line being today's text exactly:
* line 1, `[any code] `: `You write one card of a codebase's knowledge base. The input is one module: its path, its declarations with bodies dropped, its build and manifest files, lines of other modules that hold its names (possible references, not evidence of a dependency), the project's skills, and the lines of those skills that mention the module.`
* line 28, `[any code] `: `- <what it depends on, from its build and manifest files in the input; a rule the skills state about what it must not depend on>`
* line 35, `[any code] `: `- Every name in backticks must be declared in the input's declarations (a type, function, variable, target, or the name of a file in the input), or `Name.member`; a file of another module is named by its repo path, `./<name>` for a file at the root; library names stay unquoted. When an extension point is wired in another module, name that file from "Possible references in other modules" as a repo path in backticks, and only when the line shown there does the wiring (registers, constructs or calls it). Backticks are checked mechanically against the code. Skill names in "Read next" are the only other backticks.`
* line 37, `[any code] `: `- Extension points only where the input shows the mechanism (an interface or a table of callbacks with several implementations, a registry, a router or dispatch table, a list a build file or a script runs). If you cannot see how a new one is picked up, leave it out. Omit the section if there are none.`
* after line 37, `[any code] ` only: `- "Possible references in other modules" only shows where a name appears. Never state a dependency or a boundary from it.`

**Which variant.** A module whose declarations read only `.java` and `.proto` files gets `java` (plan.md D8: "a module whose sources are only Java and `.proto`"). A module whose declarations read any file through `generic_skeleton` gets `any code`: nearly every directory module, and a build-file module that also holds Kotlin, Scala or Groovy (a mixed module). `call_writer` takes the variant and passes `prompt(variant)`.

### 2. The dead-name check for a card of any code
A card whose module gets `any code` is checked so; a card whose module gets `java` is checked exactly as today.

**The declaration map**, project-wide, as the Java check takes types from every module (plan.md D9): each declared name maps to the files that declare it. A file declares the names phase-02.md decision 4 extracts from its `generic_skeleton` output (with no length limit and no uniqueness), or, for a `.java` or `.proto` file of any module, the types `TYPE_DECL` finds in it. Function bodies and comments are never read for it: `generic_skeleton` drops bodies and the extraction reads code parts, so a name that survives only in a call or a comment declares nothing.

For an `any code` card, each backtick's whole content, by the first rule that applies:
1. it holds a `/`: the path check, as today, which reads `./<name>` as the file `<name>` at the root.
2. it is a project skill's name or a module's id: skipped.
3. it is the name of a file in the card's module's pack: one of the module's source files, or a build or manifest file the pack holds under `## Wiring` (its last path component, `install-agent.sh`, `package.json`): live. A file of another module is named by its repo path and checked by rule 1, so a bare name stays live only while the module itself has the file.
4. it matches `^([A-Za-z_][\w$]*)(?:(?:\.|#|::)([A-Za-z_][\w$]*))?(?:\(\))?$`: live when the first name is in the declaration map and, if there is a member, the member occurs as a word in **one of the files that declare the first name**: in the code part of that file's `generic_skeleton` output, or, for a `.java` or `.proto` file, in its text, as the Java check looks for a member in its type's files. Otherwise dead. So `Router.add` is dead once `Router`'s file has no `add`, whatever another file declares.
5. it looks like a file's name, `^\w[\w.-]*\.[A-Za-z0-9]+$`, and rule 3 did not take it (`install-agent.sh` after a rename): dead.
6. anything else (spaces, `*`, `@`, `$`, a leading `-`, ...): not checked, as the Java check leaves it today.

### 3. Characters per token
`CHARS_PER_TOKEN` (2.5) stays for the `java` variant. A new `CHARS_PER_TOKEN_ANY` holds the measured figure for `any code` packs, rounded to one decimal. `cmd_estimate` and `cmd_pack` use the module's variant's figure. `cmd_estimate`'s message is unchanged: its cost line is per token, whatever the variant.

The figure is measured before the gated writes, on modules no gate writes: the sample Java project's directory modules whose variant is `any code`, on its clone. On that sample all three are (`deploy`: shell scripts and Dockerfiles; `scripts`: Python and shell; `specs`: `.java` and `.proto` with Python and shell, plan research R12), and a Java-only one would be left out. `kb.py pack` exactly those, note the time, `kb.py write` exactly those, then `sum(len(pack)) / (sum(in + write + read) - n * 1800)` over exactly their rows of `kb.py usage --since <time>` (or `.runs/usage.jsonl`), `n` the number of those calls. The request names each module with its variant, and gives the figure and its inputs. Why these modules: they mix shell, Python and Java like the samples, and measuring on a gated sample would make that sample's estimate check its own calibration.

### 4. The samples' cards
On the clones of phase-01.md's Gate, at the commit under test, after the calibration:
* c, shell, fondue, hono: `kb.py estimate --root $S/<label>`, note the time, `kb.py write --all --root $S/<label>`, then `kb.py usage --since <time>`.
* java-vue: the same with its five directory modules' ids instead of `--all`.
* `kb.py status --root $S/<label>` until `clean`, fixing dead names by hand as kb-init step 5 says; for java-vue, `kb.py status <its five ids> --root $S/java-vue` (decision 5). Count the hand fixes per sample.

The cards stay in the clones. They are never committed, here or in a sample.

### 5. Status for some modules
`kb.py status` takes optional module ids, as `estimate`, `write` and `pack` do: with ids, it reports and counts only those modules, and leaves out the cards of modules that no longer exist; an unknown id exits as `write` does (`unknown modules: ...`). Without ids it is today's command. Why: a clone that gets cards for some modules only, like the Java + Vue project's five directory modules, could never read `clean` while its other modules have no card.

### 6. Tests
`protocol/kb/tests/test_cards.py`:
* `prompt("java")` equals `card-writer.md` at `1bc80fe`, read with `git show` (the test skips when the repository has no such commit, e.g. in an installed plugin);
* `prompt("any code")` holds every `[any code]` line, unprefixed, and no `[java]` line;
* variant choice: a Java-only build-file module gets `java`; the mixed fixture of phase-02.md gets `any code`; a directory module holding a shell script gets `any code`; a directory module holding only `.java` files gets `java`;
* dead names in an `any code` card: a function renamed in one module, while a second module's body still calls the old name, makes the old name dead in a card that quotes it; `Router.add` is dead when `Router`'s file has no `add` while another file declares `add`, and live while `Router`'s file has it; a quoted `install-agent.sh` is live, and dead after the file is renamed; two modules both holding a `package.json`: the subject module's card quotes a bare `package.json`, which is live, and dead once the subject module's copy is removed while the other copy remains; a quoted `./package.json` is live while a root `package.json` exists; a skill name and a module id are skipped; a Java-only card's check reports what it reports today on a Java fixture with a dead type;
* `status` with ids: a fixture with two modules, one with a card and one without, reads `clean` for the first's id and reports the second's missing card without ids;
* `cmd_estimate` uses `CHARS_PER_TOKEN_ANY` for an `any code` module and 2.5 for a `java` one.

## Tasks

### Task 1 - The prompt and its variant
Decision 1, with its tests.

### Task 2 - The dead-name check
Decision 2, with its tests.

### Task 3 - Calibration and the samples' cards
Decision 5 first, with its test; then decisions 3 and 4: `CHARS_PER_TOKEN_ANY` from the calibration write, committed; then the gated writes. Report everything the Gate asks.

### Task 4 - Documents
* `protocol/kb.md`: the `status` row takes `[<id>...]` and says names in a card of any code are checked lowercase too, file names included; "How `write` keeps the cost down" gives the measured cost of the new cards beside the Java figure; one sentence on the two prompt variants and which module gets which.
* `skills/kb-init/SKILL.md`: step 1, the module list now covers every source and costs are per card of either kind; step 5, a dead lowercase name is fixed the same way, and a quoted name that is neither declared nor a file's name is dropped from backticks.
* `skills/kb-init/design-notes.md`: a measurements section for the samples: cards, input and output tokens, cost per card (smallest, largest, mean), characters per token, the calibration; "Known limits" rewritten to describe the tool as it now is (languages, module discovery, links that are possible references only, Markdown not a source by default, Gradle dependencies still not read, and parts.txt, which the "Large modules" item still calls unbuilt).
* `README.md`: the knowledge base section's "For now it reads Java and `.proto` files in Maven and Gradle projects" (line 166) says what it reads now; the status row names the projects it ran on as the brief names them (a C project, a shell project, a Vue/JavaScript web part, a public TypeScript project, fondue), never by name.

## Gate

**G1. The prompt.** `prompt("java")` is byte-identical to `git show 1bc80fe:protocol/kb/card-writer.md` (a test, and `cmp` in the request), and the mixed fixture gets `any code`. The Java gate, as in phase-01.md's G2: `IDENTICAL`.

**G2. The writes.** The request states, before each write, `kb.py estimate`'s figure for it, and then reports per sample: cards written, `kb.py usage`'s tokens and cost, and the time.

**G3. Status.** `kb.py status` reads `clean` on each of c, shell, fondue and hono, and `kb.py status <its five directory modules' ids>` on java-vue. The request gives the number of dead names fixed by hand per sample.

**G4. The estimate.** Per sample, the input figure `kb.py estimate` printed before the write is within 20% of the sum of `in + write + read` that `kb.py usage --since` reports after it.

**G5. Cost per card.** No line of the gated writes in `.runs/usage.jsonl` has `cost_usd` above 0.20.

**G6. The cards against the code.** The request names two cards of each sample, with the clone's path. The Code Reviewer checks them, in two separate checks:
* **Extension points and "Already here"**, against that sample's code. An extension point may rest on a line under "Possible references in other modules" when that line itself does the wiring (registers, constructs or calls it).
* **Boundaries**, against the module's pack: each entry rests on a build or manifest file under `## Wiring`, or on a project skill's line in the pack. A Boundaries entry that rests on a possible-reference line, or on nothing in the pack, is a finding (plan.md's Phase 3 gate as amended by the ruling of 2026-10-14 in `99-user.md`).

A wrong or unsupported entry is a finding.

**G7. Tests.** The build is green, with every test of the three phases.

The request carries `Build:` and `Gates:` with G1-G5's results and G6's card list.
