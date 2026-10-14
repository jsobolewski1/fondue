# Draft 05 - Universal knowledge base

Research: `pre-plan/01-research.md` (cited as R1-R11 and "Existing code" items 1-13). Sample projects are named as the brief names them.

## Approach

`kb.py` keeps its one pipeline: find the modules, pack each one mechanically, write each card in one tool-less call, check every card against the code. Each step of it that is Java-only today keeps its Java path byte for byte, and gains a path that knows no language, which every other file takes:

| step | Java path, unchanged | the path for everything else |
|---|---|---|
| modules | a build file with sources under `src/main` | directory modules for every source file no build-file module claims |
| declarations | `java_skeleton`, `proto_skeleton` | one reader that keeps lines by indentation and drops bodies |
| links | Maven dependencies, Java imports, `new <Type>` | no inferred edge; lines in other modules that hold the module's own names, labelled as possible references |
| wiring | `META-INF/services`, Spring `application*` | the module's build and manifest files |
| the writer's prompt | `card-writer.md` as it is | the same file with its few Java-shaped lines worded for any code |
| dead-name check | capitalised type names from `.java` and `.proto` | every identifier in backticks, found among the names the readers declare |
| cost | 2.5 chars per token | a ratio measured on the new packs |

Nothing is installed beyond what `kb.py` needs today: Python's standard library, `git` and `claude`.

## The brief's open questions

1. **Which non-Java projects, and how good their cards must be.** The four non-Java samples at hand: the sample C project, the shell project, fondue, and the web part of the Java project with a Vue/JavaScript web part. And one TypeScript project, because the goal names TypeScript and none is at hand: hono, public, at commit `588ec13fa68ea44fed1b5e1b503341db2bf09d70` (R11). The sample Java project is the sixth sample, for the gate that nothing Java changes. A card is good enough when it passes what a Java card passes today: `kb.py status` reads `clean` after kb-init's hand-fix step, which includes the line limit, and its extension points and "Already here" entries are right when checked against the code, which kb-init asks the User to do for two or three cards. Phase 3 holds the bar; its gate is the measure.
2. **Modules for a project with no build file.** Directories (D2). The repository root splits into its first-level directories, a directory too big for one card splits into its subdirectories, a subdirectory too small for a card of its own stays with its parent, and the User adjusts with `parts.txt`: split, exclude, or include what the default does not see as code (D4).
3. **Dependencies beyond the standard library, `git` and `claude`.** None (D5).
4. **What a card with no dedicated reader may cost against a Java card.** For the same amount of source, up to about twice as much input: the new reader shrinks C 4.7-5.2x, Vue and JavaScript 3.6-5.9x, TypeScript 2.2-3.2x, against `java_skeleton`'s 4.8x on Java (R3). Per card it should cost no more than the largest Java card, because a directory over the budget splits (D3). Phase 3 measures it and holds it to $0.20 a card on Sonnet, against the Java pilot's $0.07-0.15 (`skills/kb-init/design-notes.md`).
5. **Whether Java cards may change.** Not for a module whose sources are only Java and `.proto`: its pack and the writer's prompt stay byte-identical, so its card's input, cost and content are what they are today. On the sample Java project every module is such a module, and every phase's gate checks its 38 packs byte for byte. A build-file module that also holds Kotlin, Scala or Groovy files, listed by name today (kb.py:285-287), does change: the new reader reads those files, its pack grows by their declarations, and its call gets the prompt for any code (D8). That is the change Known limits asks for (`skills/kb-init/design-notes.md:31`); a mixed fixture gates it (Phase 2, Phase 3). Separately, code outside the build-file modules gets directory modules of its own (D2): in the sample Java project, `deploy`, `scripts` and `specs` (R5), whose missing cards `kb.py status` reports and the next `write --since` writes, unless the User excludes them.
6. **Language servers.** Not in this spec (D5). LSP has nothing to say about which directories make a module. For declarations, a server must be installed per language, and here only `clangd` is, for one of the six languages in the non-Java samples (R2); the marketplace has no plugin for shell or Vue. Without a project's build configuration, `clangd` cannot even resolve its types (brief). For links, the request is per symbol over an indexed project. The reader that needs nothing gets within 1.0-1.6x of `java_skeleton` on the same Java files (R3), so a server would buy precision at the cost of an install per language.

## Decisions

**D1. One pipeline, the Java path kept, a language-agnostic path beside each Java-only step.** The steps are reshaped where they are (Existing code 1-10): `modules()`, `declarations()`, `wiring()`, `wired_from`'s shape, `cmd_status`, `card-writer.md` and the cost constant each take the other path for non-Java code. Java and proto readers, Maven dependencies and the import-based links are not touched.
* Rejected: **replace `java_skeleton` with the new reader.** Java packs would grow by up to 1.6x (R3) and every Java card would change, in the User's main language.
* Rejected: **a dedicated reader per language** (C, JavaScript, Python, shell, ...). Each is a hand-written parser like `java_skeleton`'s 86 lines (kb.py:182-267), with its own tests, and the long tail still needs a reader that knows no language. That reader is close to a dedicated one on Java itself (R3), so the dedicated ones would buy little.
* Rejected: **raw source in the pack.** About 5x the input of a skeleton on C and 7x on Python (R3); the sample C project's `core` alone is 410,876 chars raw.
* Rejected: **an agent that explores the code to write the card.** Its context grows on every step; the design notes record an earlier tool spending two full sessions on a project a fifth the size of the sample Java project.

**D2. A directory module is the unit for source no build file claims.** A source file (D4) belongs to one. The repository root and every build-file module's directory split: their files group by first directory below, and the files directly in them form a module of their own. A group whose raw source exceeds the budget (D3) splits the same way one level down; after such a split, a child group under a floor of raw source folds back into its parent's own module, so a size split never makes a card of a stray small directory (R5: hono's `src/request` at 56 chars, `src/preset` at 1,229). The floor applies to what a size split makes, not to the first-level directories of the root or of a build-file module, and not to a part the User names. Every other group is one module. A directory module may share a directory with a build-file module, but then owns only the source files that module does not claim: every tracked source file belongs to exactly one module, and a module's changes are its own source files' and its folded children's, never another module's. Plan gives such a module its distinct id. `parts.txt` gives a directory inside a directory module a card of its own, by the same code as inside a build-file module (Existing code 3), and gains two lines: one that excludes a path, one that includes a path as source (D4). On the samples the prototype of this rule, without the floor, gives a list a reader of the code would draw apart from the two small `src/` leaves the floor folds, with exclusions only for things like old spec files and benchmarks (R5).
* Rejected: **package manifests as module boundaries.** On hono they made 16 modules of `adapters/` and `benchmarks/`, one under 1,100 chars (R5). Without them the Java + Vue project's three web parts still come out as three modules.
* Rejected: **first-level directories only, never split.** hono's `src/` would be one card for 188 files and 794,019 raw chars (R5).
* Rejected: **split with no floor.** Every small leaf of an oversized directory becomes a card: two in hono's `src/` (R5), and more as a budget drops (at 150,000 chars, three launchers of about 1,000 chars in the C project).
* Rejected: **the root as one module while it is small.** A project crossing the budget would rename every card at once, and in a Java project unrelated leftovers (deploy scripts, tooling scripts) would share one card.
* Rejected: **a module list the User writes for every non-Java project.** It goes stale with every new directory, while a handover and a hunt run `kb.py` mechanically and need modules to follow the code. `parts.txt` stays the User's lever for the cases the rule gets wrong.

**D3. The split budget is on raw source size.** About the sample Java project's largest module (224,310 raw chars, brief), whose card `kb.py status` passes today (R7). Plan sets the figure.
* Rejected: **the budget on skeleton size.** Module boundaries, and so card names, would move with a reader setting: the C project's `examples/` is one module or five depending on whether comment lines are kept (R5).

**D4. By default a source is a code file; documentation and data are not; the User can include anything else.** Code is recognised by extension and by a few file names (`Makefile`, `Dockerfile`, `CMakeLists.txt`, ...); plan sets the list. Tests are out, as `src/test` is for Java, and so are vendored and generated directories, hidden directories, `fondue/` and submodules (R9). Markdown is not a source by default. So fondue's knowledge base covers its Python, and its skills and protocol stay documents that roles read whole. A list cannot know every language, so a `parts.txt` line includes a tracked path (a directory or a file pattern) as source, whatever its extension. Its text then goes through the reader of D6, which needs no language. A project in a language the list lacks gets modules from that one line, and `kb.py` refuses only a project with no source at all after its overrides.
* Rejected: **every tracked text file is a source.** The sample Java project has 501 Markdown files of old specs outside `fondue/` (R8) that would become a module, and data files would be packed as code.
* Rejected: **Markdown as a source by default.** "One fact, one home" (`protocol/kb.md:12`): a card says what exists and where, a skill or a document says why and how. A card about a document would repeat it. A User who wants it anyway includes it.
* Rejected: **the extension list alone.** A project in a language not on it would still be refused, and nothing the User writes could change that.

**D5. No dependency beyond Python's standard library, `git` and `claude`.** `kb.py` runs on any machine fondue runs on, outside any Claude session. Universal-ctags and tree-sitter are not installed here (brief, R2), and a language server needs an install per language and the project's own build configuration (question 6).
* Rejected: **an optional precise reader through LSP or ctags** in this spec. It would add a second path to test per language for a gain R3 shows is small. Nothing in D1 rules it out later: it would be another dedicated reader in the same dispatch.

**D6. One reader that knows no language, for every source file with no dedicated reader, in any module.** It keeps declarations by indentation, drops bodies, keeps a signature whole across lines, and skips brackets inside strings and comments (R3, R4). Its settings, how many comment lines it keeps and how deep it goes into containers, are plan's: they trade input size (R3) against what a card can name, e.g. a Vue component's methods (R3).

**D7. No dependency edge is inferred for a directory module; the lines that use its names are packed as possible references.** A directory module's header names no project dependency and no dependent: no exact evidence for one exists without parsing each language, and a name shared by two modules is not a dependency (R6 shows edges a reader would reject). What a directory module depends on, the writer reads from its build and manifest files, packed as its wiring (D1). The pack does carry, under a heading that says they are possible references, the lines of other modules that hold a name only this module's reader output declares, capped like `wired_from`'s construction sites and built by the same reshaped function. The writer's prompt for any code (D8) lets it name a file as where something plugs in only when such a line itself shows it (a call that registers or constructs), and never lets it state a boundary from them. Build-file modules' links are computed among build-file modules only, as today (R10).
* Rejected: **dependency edges from shared names.** A false boundary misleads every later Architect who trusts the card; a sparse one only sends them to the code.
* Rejected: **no cross-module lines at all.** Extension points would name the interface but not the file that wires a new one in: what the Java pilot saw before construction sites were added (`skills/kb-init/design-notes.md:26`).
* Rejected: **parsing each language's imports** for exact edges. Per-language code again (D1).

**D8. The writer's prompt keeps one file, and a Java-only module's prompt stays byte-identical.** The lines that describe Java input and Java names (`card-writer.md:1`, `:35`) get a wording for any code. A module whose sources are only Java and `.proto` gets today's text exactly; any other module, a mixed build-file module included, gets the wording for any code. Plan picks the mechanism.
* Rejected: **one generic wording for every module.** It changes every Java card's input, and whether their content changes could only be seen by paying to rewrite them.
* Rejected: **a second prompt file.** Two copies of 40 lines that must stay in step.

**D9. The dead-name check covers names in every language.** For a card of a module with code from the new reader, every identifier in backticks, lowercase included, must be a name the readers declare somewhere in the project, as the Java check takes declared types from every module (kb.py:599-604): the readers' output, never function bodies, so a name that survives only in a call or a comment is dead. Paths and skill names are checked as today. A card of a Java-only module is checked as today, so `kb.py status` on the sample Java project reports what it reports today for its 38 modules.

**D10. Cost is measured, not assumed.** Phase 3 writes the samples' cards and takes the characters per token of the new packs from `kb.py usage`. `kb.py estimate` uses it.

**D11. A test suite on the standard library's `unittest` is the build.** The repository has no build and no tests (Existing code 12), and every Code turn needs one. Fixtures are small git repositories made in a temporary directory, so no test reads a sample. `pytest` is rejected as a dependency (D5).

**D12. Gates run on clones of the samples, never on the User's working trees.** `kb.py` writes `fondue/kb/` into the project it runs on. Each sample is cloned with `git clone --local` into a scratch directory, hono from its public repository at the commit above. The phase files name the samples as the brief does and point to `pre-plan/samples.local.md` for the paths. The **Java gate** used by every phase: on a clone of the sample Java project, `kb.py pack` for its 38 build-file modules writes packs byte-identical (`diff -r`) to those `kb.py` writes at the commit implementation starts from. R7 shows the packs are reproducible, so the check fails only on a real change.

## Phases

### Phase 1 - Modules for every project
Delivers directory modules (D2, D3, D4): the default exclusions, the floor on what a size split makes, the `parts.txt` lines that exclude and include a path, parts inside directory modules, and the change count for directory modules in `status`, `touched` and `write --since`. `kb.py` refuses only a project with no source at all. A directory module's pack lists its source files by name, as the pack does today for Kotlin; Phase 2 reads them. `kb.py modules` shows each module's size, for the User's check in kb-init step 1. The test suite (D11) starts here. Documents: the modules row and `parts.txt` in `protocol/kb.md`, and kb-init step 1.

Gate:
* `kb.py modules` on a clone of each sample prints the module list the phase file states, derived from the rule by hand against R5. No module a size split made is under the floor.
* The Java gate (D12).
* Tests: a change to a directory module's own file, or to a child folded into it, counts against it in `status` and `changed_modules`, and a change in a separate module below it does not; a fixture with a build-file module at the root, its `src/main`, and a root `Makefile` has both modules, and a change to each one's sources counts only against its owner; an excluding line removes a module; a part inside a directory module takes its files; a small child of an oversized directory folds into its parent's module, and a part the User names there does not; a fixture repository whose only source is in a shebang-less extension on no list has no module, and gets one from an including line.
* The build is green.

### Phase 2 - Packs for every language
Delivers the reader of D6, for every source file with no dedicated reader, Kotlin, Scala and Groovy in build-file modules included; a directory module's build and manifest files packed as its wiring; and the possible references of D7. Documents: "What `write` reads" in `protocol/kb.md`.

Gate:
* `brackets.py`'s check (R4), run on the new reader's output: on every sample, no file's skeleton ends with a bracket open.
* On each sample's directory-module files, the reader shrinks raw source at least: the C project 4x, the web part of the Java + Vue project 3x, hono 2x, fondue 5x, the shell project 1.5x. Each floor is under the lowest of R3's settings, so it fails when the reader keeps bodies, not when plan picks a setting.
* On a clone of each sample, no directory module's header names a project dependency or dependent. The possible references hold the lines the phase file lists, each checked against the sample's code when the phase file is written, e.g. the shell project's lines that run the `provision` scripts, in `provision`'s pack.
* The Java gate.
* Tests, one fixture per family: a C signature over several lines, a Python class, a Vue component written as an object, a shell function, a TypeScript interface. Each keeps its declaration and drops its body. A build-file module holding Java and Kotlin packs its Java declarations exactly as `java_skeleton` gives them and its Kotlin ones from the new reader. The build is green.

### Phase 3 - Writing and checking the cards
Delivers D8, D9 and D10, the samples' cards, and the documents with what was measured: `protocol/kb.md`, kb-init (step 1, and step 5 for lowercase names), its design notes (measurements, Known limits), and the README's knowledge base section and status row.

Gate:
* A Java-only module's system prompt is byte-identical to `card-writer.md` at the commit implementation starts from, and the mixed fixture of Phase 2 gets the wording for any code. The Java gate.
* Cards are written on clones of the C project, the shell project, fondue and hono (`kb.py write --all`), and of the Java + Vue project's directory modules (`kb.py write <ids>`): about 37 cards, about $2-3 on Sonnet. The request states `kb.py estimate`'s figure before the write.
* On each, `kb.py status` reads `clean` after kb-init step 5's hand fixes. The request reports how many dead names were fixed by hand on each sample.
* Per sample, `kb.py estimate` before the write is within 20% of the input tokens `kb.py usage` reports after it.
* No card costs more than $0.20 (`.runs/usage.jsonl`, one line per call).
* The Code Reviewer checks two cards of each sample against that sample's code: their extension points and "Already here" entries, and that each Boundaries entry has evidence in the pack (a build or manifest file, or a line that shows the call). A wrong or unsupported entry is a finding.
* Tests: a function renamed in one module while another module's body still calls the old name shows as dead in a directory module's card, and a Java-only card's check is unchanged. The build is green.

## Left to plan

* Phase 1: the list of code extensions and names, the default exclusions, the budget's and the floor's figures, module ids (the root module's among them, a directory module's that shares a build-file module's directory, and how a clash with a build-file module's id resolves), the `parts.txt` syntax for exclusion and inclusion, how a directory module's own files are named to `git diff`, and paths `git ls-files` quotes.
* Phase 2: the reader's settings, which build and manifest files a directory module packs and their line limit, how a module's own names are chosen for the possible references, and their cap and heading.
* Phase 3: how a module's prompt variant is chosen and the wording for any code, which backticks the check takes as identifiers, the characters per token, and where `kb.py estimate`'s message gets its new figures.
