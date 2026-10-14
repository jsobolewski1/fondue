# Draft 03 - Universal knowledge base

Research: `pre-plan/01-research.md` (cited as R1-R11 and "Existing code" items 1-13). Sample projects are named as the brief names them.

## Approach

`kb.py` keeps its one pipeline: find the modules, pack each one mechanically, write each card in one tool-less call, check every card against the code. Each step of it that is Java-only today keeps its Java path byte for byte, and gains a path that knows no language, which every other file takes:

| step | Java path, unchanged | the path for everything else |
|---|---|---|
| modules | a build file with sources under `src/main` | directory modules for every code file no build-file module claims |
| declarations | `java_skeleton`, `proto_skeleton` | one reader that keeps lines by indentation and drops bodies |
| links | Maven dependencies, Java imports, `new <Type>` | names and file names of one module found in another's source |
| wiring | `META-INF/services`, Spring `application*` | the module's build and manifest files |
| the writer's prompt | `card-writer.md` as it is | the same file with its few Java-shaped lines worded for any code |
| dead-name check | capitalised type names from `.java` and `.proto` | every identifier in backticks, found as a word in the code |
| cost | 2.5 chars per token | a ratio measured on the new packs |

Nothing is installed beyond what `kb.py` needs today: Python's standard library, `git` and `claude`.

## The brief's open questions

1. **Which non-Java projects, and how good their cards must be.** The four non-Java samples at hand: the sample C project, the shell project, fondue, and the web part of the Java project with a Vue/JavaScript web part. And one TypeScript project, because the goal names TypeScript and none is at hand: hono, public, at commit `588ec13fa68ea44fed1b5e1b503341db2bf09d70` (R11). The sample Java project is the sixth sample, for the gate that nothing Java changes. A card is good enough when it passes what a Java card passes today: `kb.py status` reads `clean` after kb-init's hand-fix step, which includes the line limit, and its extension points and "Already here" entries are right when checked against the code, which kb-init asks the User to do for two or three cards. Phase 4 holds the bar; its gate is the measure.
2. **Modules for a project with no build file.** Directories (D2). The repository root splits into its first-level directories, a directory too big for one card splits into its subdirectories, and the User adjusts with `parts.txt`.
3. **Dependencies beyond the standard library, `git` and `claude`.** None (D5).
4. **What a card with no dedicated reader may cost against a Java card.** For the same amount of source, up to about twice as much input: the new reader shrinks C 4.7-5.2x, Vue and JavaScript 3.6-5.9x, TypeScript 2.2-3.2x, against `java_skeleton`'s 4.8x on Java (R3). Per card it should cost no more than the largest Java card, because a directory over the budget splits (D3). Phase 4 measures it and holds it to $0.20 a card on Sonnet, against the Java pilot's $0.07-0.15 (`skills/kb-init/design-notes.md`).
5. **Whether Java cards may change.** No. On the sample Java project, every pack and the writer's prompt stay byte-identical, which every phase's gate checks, so a Java card's input, cost and content are what they are today. Two things around Java do change, and only where they apply. A Kotlin, Scala or Groovy file in a build-file module, listed by name today (kb.py:285-287), is read by the new reader; the sample Java project has none. And code outside the build-file modules gets directory modules of its own (D2): in the sample Java project, `deploy`, `scripts` and `specs` (R5), whose missing cards `kb.py status` reports and the next `write --since` writes, unless the User excludes them.
6. **Language servers.** Not in this spec (D5). LSP has nothing to say about which directories make a module. For declarations, a server must be installed per language, and here only `clangd` is, for one of the six languages in the non-Java samples (R2); the marketplace has no plugin for shell or Vue. Without a project's build configuration, `clangd` cannot even resolve its types (brief). For links, the request is per symbol over an indexed project. The reader that needs nothing gets within 1.0-1.6x of `java_skeleton` on the same Java files (R3), so a server would buy precision at the cost of an install per language.

## Decisions

**D1. One pipeline, the Java path kept, a language-agnostic path beside each Java-only step.** The steps are reshaped where they are (Existing code 1-10): `modules()`, `declarations()`, `wiring()`, `module_header`, `wired_from`'s shape, `cmd_status`, `card-writer.md` and the cost constant each take the other path for non-Java code. Java and proto readers, Maven dependencies and the import-based links are not touched.
* Rejected: **replace `java_skeleton` with the new reader.** Java packs would grow by up to 1.6x (R3) and every Java card would change, in the User's main language.
* Rejected: **a dedicated reader per language** (C, JavaScript, Python, shell, ...). Each is a hand-written parser like `java_skeleton`'s 86 lines (kb.py:182-267), with its own tests, and the long tail still needs a reader that knows no language. That reader is close to a dedicated one on Java itself (R3), so the dedicated ones would buy little.
* Rejected: **raw source in the pack.** About 5x the input of a skeleton on C and 7x on Python (R3); the sample C project's `core` alone is 410,876 chars raw.
* Rejected: **an agent that explores the code to write the card.** Its context grows on every step; the design notes record an earlier tool spending two full sessions on a project a fifth the size of the sample Java project.

**D2. A directory module is the unit for code no build file claims.** A code file belongs to one. The repository root and every build-file module's directory split: their files group by first directory below, and the files directly in them form a module of their own. A group whose raw source exceeds the budget (D3) splits the same way one level down. Every other group is one module. A directory module never shares a directory with a build-file module, and its changes are its own files', never a nested module's. `parts.txt` gives a directory inside a directory module a card of its own, by the same code as inside a build-file module (Existing code 3), and gains a line that excludes a path. On the samples the prototype of this rule gives a list a reader of the code would draw, with exclusions only for things like old spec files and benchmarks (R5).
* Rejected: **package manifests as module boundaries.** On hono they made 16 modules of `adapters/` and `benchmarks/`, one under 1,100 chars (R5). Without them the Java + Vue project's three web parts still come out as three modules.
* Rejected: **first-level directories only, never split.** hono's `src/` would be one card for 188 files and 794,019 raw chars (R5).
* Rejected: **the root as one module while it is small.** A project crossing the budget would rename every card at once, and in a Java project unrelated leftovers (deploy scripts, tooling scripts) would share one card.
* Rejected: **a module list the User writes for every non-Java project.** It goes stale with every new directory, while a handover and a hunt run `kb.py` mechanically and need modules to follow the code. `parts.txt` stays the User's lever for the cases the rule gets wrong.

**D3. The split budget is on raw source size.** About the sample Java project's largest module (224,310 raw chars, brief), whose card `kb.py status` passes today (R7). Plan sets the figure.
* Rejected: **the budget on skeleton size.** Module boundaries, and so card names, would move with a reader setting: the C project's `examples/` is one module or five depending on whether comment lines are kept (R5).

**D4. A source is a code file; documentation and data are not.** Code is recognised by extension and by a few file names (`Makefile`, `Dockerfile`, `CMakeLists.txt`, ...); plan sets the list. Tests are out, as `src/test` is for Java, and so are vendored and generated directories, hidden directories, `fondue/` and submodules (R9). Markdown is not a source. So fondue's knowledge base covers its Python, and its skills and protocol stay documents that roles read whole.
* Rejected: **every tracked text file is a source.** The sample Java project has 501 Markdown files of old specs outside `fondue/` (R8) that would become a module, and data files would be packed as code.
* Rejected: **Markdown as a source.** "One fact, one home" (`protocol/kb.md:12`): a card says what exists and where, a skill or a document says why and how. A card about a document would repeat it.

**D5. No dependency beyond Python's standard library, `git` and `claude`.** `kb.py` runs on any machine fondue runs on, outside any Claude session. Universal-ctags and tree-sitter are not installed here (brief, R2), and a language server needs an install per language and the project's own build configuration (question 6).
* Rejected: **an optional precise reader through LSP or ctags** in this spec. It would add a second path to test per language for a gain R3 shows is small. Nothing in D1 rules it out later: it would be another dedicated reader in the same dispatch.

**D6. One reader that knows no language, for every code file with no dedicated reader, in any module.** It keeps declarations by indentation, drops bodies, keeps a signature whole across lines, and skips brackets inside strings and comments (R3, R4). Its settings, how many comment lines it keeps and how deep it goes into containers, are plan's: they trade input size (R3) against what a card can name, e.g. a Vue component's methods (R3).

**D7. Links between directory modules come from names and file names.** A module's distinctive declared names, and its file names, found as words in another module's source, give `depends on (project)`, `depended on by` and "used in other modules" lines, the counterpart of the Java pack's construction sites. `module_header` prints them as it prints Maven's. On the samples this finds the edges a reader of the code would draw, with some it would not (R6); plan sets the thresholds and the phase file lists edges that must appear and edges that must not. Build-file modules' links are computed among build-file modules only, as today (R10).
* Rejected: **no links for directory modules.** Boundaries would stay empty, and extension points would name the interface but not the file that wires a new one in: what the Java pilot saw before construction sites were added (`skills/kb-init/design-notes.md:26`).
* Rejected: **parsing each language's imports.** Per-language code again (D1).

**D8. The writer's prompt keeps one file, and a Java module's prompt stays byte-identical.** The lines that describe Java input and Java names (`card-writer.md:1`, `:35`) get a wording for any code. A module whose declarations all come from the Java and proto readers gets today's text exactly. Plan picks the mechanism.
* Rejected: **one generic wording for every module.** It changes every Java card's input, and whether their content changes could only be seen by paying to rewrite them.
* Rejected: **a second prompt file.** Two copies of 40 lines that must stay in step.

**D9. The dead-name check covers names in every language.** For a card of a module with code from the new reader, every identifier in backticks, lowercase included, must occur as a word in the project's code; paths and skill names are checked as today. A card of a Java module is checked as today, so `kb.py status` on the sample Java project reports what it reports today for its 38 modules.

**D10. Cost is measured, not assumed.** Phase 4 writes the samples' cards and takes the characters per token of the new packs from `kb.py usage`. `kb.py estimate` uses it.

**D11. A test suite on the standard library's `unittest` is the build.** The repository has no build and no tests (Existing code 12), and every Code turn needs one. Fixtures are small git repositories made in a temporary directory, so no test reads a sample. `pytest` is rejected as a dependency (D5).

**D12. Gates run on clones of the samples, never on the User's working trees.** `kb.py` writes `fondue/kb/` into the project it runs on. Each sample is cloned with `git clone --local` into a scratch directory, hono from its public repository at the commit above. The phase files name the samples as the brief does and point to `pre-plan/samples.local.md` for the paths. The **Java gate** used by every phase: on a clone of the sample Java project, `kb.py pack` for its 38 build-file modules writes packs byte-identical (`diff -r`) to those `kb.py` writes at the commit implementation starts from. R7 shows the packs are reproducible, so the check fails only on a real change.

## Phases

### Phase 1 - Modules for every project
Delivers directory modules (D2, D3, D4): the default exclusions, the `parts.txt` line that excludes a path, parts inside directory modules, and the change count for directory modules in `status`, `touched` and `write --since`. `kb.py` no longer refuses a project that has code. A directory module's pack lists its code files by name, as the pack does today for Kotlin; Phase 2 reads them. `kb.py modules` shows each module's size, for the User's check in kb-init step 1. The test suite (D11) starts here. Documents: the modules row and `parts.txt` in `protocol/kb.md`, and kb-init step 1.

Gate:
* `kb.py modules` on a clone of each sample prints the module list the phase file states, derived from the rule by hand against R5.
* The Java gate (D12).
* Tests: a change to a directory module's own file counts against it in `status` and `changed_modules`, a change in a module nested below it does not; an excluding line removes a module; a part inside a directory module takes its files.
* The build is green.

### Phase 2 - Declarations for every language
Delivers the reader of D6, for every code file with no dedicated reader, Kotlin, Scala and Groovy in build-file modules included, and a directory module's build and manifest files packed as its wiring. Documents: "What `write` reads" in `protocol/kb.md`.

Gate:
* `brackets.py`'s check (R4), run on the new reader's output: on every sample, no file's skeleton ends with a bracket open.
* On each sample's directory-module files, the reader shrinks raw source at least: the C project 4x, the web part of the Java + Vue project 3x, hono 2x, fondue 5x, the shell project 1.5x. Each floor is under the lowest of R3's settings, so it fails when the reader keeps bodies, not when plan picks a setting.
* The Java gate.
* Tests, one fixture per family: a C signature over several lines, a Python class, a Vue component written as an object, a shell function, a TypeScript interface. Each keeps its declaration and drops its body. The build is green.

### Phase 3 - Links between directory modules
Delivers D7.

Gate:
* On a clone of each sample, the packs' headers hold the edges the phase file lists as expected and none of those it lists as wrong, each checked against the sample's code when the phase file is written. R6 is the starting list, e.g. the C project's `include` used by `core` and by the examples, and the shell project's `provision` used by the root module.
* The Java gate.
* Tests on a fixture of three modules. The build is green.

### Phase 4 - Writing and checking the cards
Delivers D8, D9 and D10, the samples' cards, and the documents with what was measured: `protocol/kb.md`, kb-init (step 1, and step 5 for lowercase names), its design notes (measurements, Known limits), and the README's knowledge base section and status row.

Gate:
* A Java module's system prompt is byte-identical to `card-writer.md` at the commit implementation starts from. The Java gate.
* Cards are written on clones of the C project, the shell project, fondue and hono (`kb.py write --all`), and of the Java + Vue project's directory modules (`kb.py write <ids>`): about 37 cards, about $2-3 on Sonnet. The request states `kb.py estimate`'s figure before the write.
* On each, `kb.py status` reads `clean` after kb-init step 5's hand fixes. The request reports how many dead names were fixed by hand on each sample.
* Per sample, `kb.py estimate` before the write is within 20% of the input tokens `kb.py usage` reports after it.
* No card costs more than $0.20 (`.runs/usage.jsonl`, one line per call).
* The Code Reviewer checks two cards of each sample, their extension points and "Already here" entries, against that sample's code. A wrong entry is a finding.
* Tests: a renamed lowercase function shows as dead in a directory module's card, and a Java card's check is unchanged. The build is green.

## Left to plan

* Phase 1: the list of code extensions and names, the default exclusions, the budget's figure, module ids (the root module's among them, and how a clash with a build-file module's id resolves), the `parts.txt` syntax for exclusion, how a directory module's own files are named to `git diff`, and paths `git ls-files` quotes.
* Phase 2: the reader's settings, which build and manifest files a directory module packs, and their line limit.
* Phase 3: how names are chosen, the thresholds, and the cap on "used in other modules" lines.
* Phase 4: how a module's prompt variant is chosen, which backticks the check takes as identifiers, the characters per token, and where `kb.py estimate`'s message gets its new figures.
