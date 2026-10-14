# Phase 2 - Packs for every language

After Phase 1 a directory module's pack lists its source files by name. This phase reads them: one reader that knows no language turns every source file with no dedicated reader into its declarations, in directory modules and in build-file modules alike. A directory module also packs its build and manifest files, and the lines of other directory modules that hold its names, labelled as possible references. No dependency edge is inferred for a directory module.

plan.md decisions delivered: D1 (the reader, wiring and construction-site rows of its table), D6, D7, and the Phase 2 section.

## Essential knowledge

* **Phase 1's model** (phase-01.md): `Module.kind` is `"build"` or `"dir"`; a directory module is a group or a residual; `owns(m, p)` and `pathspecs(m)` give its files; the source rule (phase-01.md decision 2) decides what a source is, with the code list, the name list and `parts.txt` include lines. Java links, `wired_from` and `wiring` run for build-kind modules only.
* **Today's dispatch** (kb.py:274-288): `.java` to `java_skeleton` (kb.py:182-267), `.proto` to `proto_skeleton` (kb.py:270-271), `.kt`, `.scala`, `.groovy` listed by name, everything else skipped. Each read file goes into the pack as `### <path relative to the module>` and its text.
* **`wired_from`** (kb.py:369-388): for each other module, each `.java` source whose text imports one of this module's packages, every line matching `new <Type>`, as `- <path>:<line no>: <line, stripped, 160 chars>`, at most `WIRED_FROM_MAX` (40) lines; `pack` prints them under `## Constructed in other modules (where it is plugged in)`.
* **`wiring`** (kb.py:348-357): files matching `WIRING_GLOBS` under `src/main/resources`, each as `### <path relative to the module>` and its lines that are neither blank nor `#` comments, at most `WIRING_MAX_LINES` (60), then `… (<n> more lines)`; `pack` prints them under `## Wiring`.
* **What the build-file modules of the two Java samples hold under `src/main`** (plan research R5): only `.java` and `.proto` among the code list's extensions, so sending every other code-list file of a build-file module to the new reader changes none of their packs.
* **The reader, prototyped** (`plan/results/reader.py`, plan research R6): on every sample's directory-module files, no skeleton ends with a bracket open, and raw source shrinks C 5.2x, the shell project 1.9x, fondue 6.1x, the Java + Vue project's web part 3.6x, hono 2.2x. Three repairs got it there from the pre-plan prototype: brackets in strings and comments do not count; a cut line is closed; a trailing `//` or `#` comment must start the line or follow a space, because `tag.replace(/^W\//, '')` in hono otherwise opened a bracket for the rest of its file. At depth 3 a Vue component written as an object keeps `methods: {` and each method's header, and no body.
* **Possible references, prototyped** (`plan/results/refs.py`, plan research R7, with the rule of decision 4): `provision` in the shell project gets lines from the root module's `Makefile` and `Vagrantfile`, which run its scripts by file name; the C project's `include` gets lines from every `examples/*` module; the Java + Vue project's shared web part gets lines from both other web parts; hono's `src/router` gets lines from `src/hono.ts` and from `src/preset/quick.ts` and `src/preset/tiny.ts`, which construct routers.
* **Java packs are reproducible** on a clone, across hash seeds (pre-plan research R7).

## Technical decisions

### 1. The reader
A function `generic_skeleton(src)` next to `java_skeleton`, with these rules, which are `plan/results/reader.py`'s:
* **Leading licence.** After any blank lines and a `#!` line, a leading `/* ... */` or `<!-- ... -->` block, or a leading run of lines starting with `#` (not a preprocessor directive), `//` or `--`, is dropped when it holds `copyright`, `license` or `licence` (any case).
* **Code part of a line**, used for every bracket count and every block header: the line without string literals and comments. A string literal runs from `"`, `'` or `` ` `` to the same quote, with backslash escapes; a quote with no closing quote on the line is a plain character. A comment is a `/* ... */` span, which may run across lines, or the rest of the line from a `//` or `#` that starts the line or follows a space or tab.
* **Balance**: the number of `(` and `[` in the code part, less `)` and `]`. Braces are not counted: blocks come from indentation.
* **Comment lines**: a line inside a `/* */` block, or whose first non-blank characters are `#` (not `#!`, not a preprocessor directive), `//`, `--`, `*` or `<!--`. They never open or close a block. Of a run of them, ended by a blank or a code line, the first that holds a word character is kept, when its position is shown, cut at 160 characters.
* **Preprocessor lines**: `#` then optional spaces then `if`, `ifdef`, `ifndef`, `else`, `elif`, `endif`, `define`, `undef`, `include`, `pragma` or `error`. They never open or close a block; when shown, each is kept cut at 220 and closed (see Cut), and its continuation lines are not kept.
* **Indentation**: leading spaces count 1, a tab 4.
* **Blocks**: when a code line is indented more than the code line before it, a block opens, whose header is that earlier line with its continuation lines; it closes at the first code line indented no more than its header. A block is a **container** when its header's code part has no `(`, or names one of `class struct enum interface union trait impl object namespace module record protocol extension` before its first `(`; otherwise it is a **body**. A code line that is only brackets and punctuation (`{`, `}`, `);`) does not become the header.
* **Shown**: every open block is a container, and at most 2 blocks are open (depth 3).
* **Kept**: a shown code line, cut (see Cut). While its balance, counted on the whole line, stays above zero, the lines after it are its continuation: kept whatever their indentation, never opening a block.
* **Cut**: a kept line over 220 characters is cut to 220, followed by `…` and the closing brackets that its kept part leaves open, innermost first. A cut line's continuation lines are still kept.

The constants are named next to the others: depth, 220, 160, the container keywords.

### 2. Which files a module's declarations read
`declarations(m)` sends, in path order:
* `.java` to `java_skeleton` and `.proto` to `proto_skeleton`, as today;
* every other **source** file to `generic_skeleton`. For a directory module that is every file it holds. For a build-file module it is every file under `src/main` that the source rule's steps 3, 4 and 7 make a source: on the code list or the name list, or matched by an include line, and not matched by an exclude line.

Each read file goes in as today, `### <path relative to the module>` and its skeleton, when the skeleton is not blank. The names-only list goes: no source is left unread. A build-file module holding only `.java` and `.proto` among its sources reads exactly what it reads today, so its pack does not change.

### 3. A directory module's wiring
`wiring(m)` for a directory module packs the files it owns (phase-01.md decision 5) whose name is one of `package.json deno.json jsr.json tsconfig.json Cargo.toml go.mod pyproject.toml setup.cfg requirements.txt Pipfile composer.json Gemfile pubspec.yaml`, in path order, at most 8, each formatted exactly as `wiring` formats a file today. They go under `## Wiring`, as today. Build-file modules: unchanged. A source file is never also a wiring file: `CMakeLists.txt` and `Makefile` are sources, read by the reader.

### 4. Possible references
For a directory module `m`:
* **Its names**: the names its files' `generic_skeleton` output declares (below), and its files' names, with and without extension (`install.sh`, `install`); each at least 6 characters long, and only those no other directory module also has.
* **Names a skeleton declares**, line by line on the code part: the word after `struct enum union typedef class interface type def func fn function const let var trait impl module object record protocol extension namespace alias macro` (a `*` between is allowed); the name after `#define`; the first word followed by `(`; a word at the start of the line, after an optional `export`, followed by `:` (not `::`) or `=` (not `==`); and `name` in a line `} name;`. Not these words: `if for while switch return catch sizeof elif else until case when export default import from public private protected static extern inline`.
* **Lines**: every line of another module's source that holds one of its names as a whole word (not preceded or followed by a word character or `$`). Another module is any module but `m`: another directory module's files, and a build-file module's files under its `src/main`; from a build-file module only `m`'s file names count, never its other names (plan research R7: with every name, 36 of the 40 lines picked for the Java + Vue project's shared web part came from Java and resource files holding words like `config` or `endpoint`, and the web parts' own references fell to 4; across languages a module is referred to by its files' names). From one file, the 3 lines that hold the most distinct names are taken, a line holding one of its file names counting 2 more, ties to the earlier line, and kept in line order. The referencing modules are ordered by how many distinct names their lines hold, most first, ties in path order; the lines are then taken round-robin over them, one from each in turn, up to 40 (`WIRED_FROM_MAX`). Each as `- <path>:<line no>: <line, stripped, 160 chars>`. Why the ranking: in the shell project, the first three lines of `Vagrantfile` that hold a `provision` name are port forwards holding a common word, and the two that run its scripts by file name come later (plan research R7).
* **Heading**: `## Possible references in other modules (lines that hold a name only this module declares; not evidence of a dependency)`, after the declarations, where `pack` puts construction sites today; left out when there are none.
* **Header**: a directory module's `depends on (project)` and `depended on by` stay `-`. Nothing above feeds them.

`wired_from`'s loop is reshaped so both callers share it: a helper takes a module's other modules' files, a test on a file's text and a line pattern, and returns the matching lines per module, in order. `wired_from` calls it with today's arguments (build-kind modules, `.java` sources, the import test, the `new <Type>` pattern) and flattens the result to its first 40, so its output is today's. The possible references call it with every other module's sources, no file test and the names pattern (the file-names pattern for a build-file module), and select as above.

### 5. Tests
`protocol/kb/tests/test_reader.py`, one fixture per family, each keeping the declaration and dropping the body:
* C: a `static` function whose parameters span three lines, with a body; a `typedef struct { ... } name;`; a `#define` with parentheses; a licence block on top; a string holding `"{\"e\":["`.
* Python: a class with two methods and a module-level function; their bodies, and a docstring inside one, are dropped.
* Vue: a single-file component whose `<script>` is `export default { data() {...}, methods: { f() {...} } }`; `methods:` and `f()` are kept, their bodies are not.
* Shell: a function `name() { ... }` with a body, and top-level commands.
* TypeScript: an `interface` with members; a `function` whose signature spans lines and has a body; a line with a regex literal holding `//`.
* A line over 220 characters with an open bracket is cut and closed.
* A mixed build-file module: a Maven fixture with `src/main/java/A.java` and `src/main/kotlin/B.kt`; its pack holds `A.java`'s declarations exactly as `java_skeleton` gives them and `B.kt`'s from `generic_skeleton`, and no names-only list.

`protocol/kb/tests/test_packs.py`:
* wiring: a directory module with a `package.json` packs it under `## Wiring`; a build-file module's wiring is today's;
* possible references: three directory modules where `b` calls a function `a` declares and `c` names one of `a`'s files; `a`'s pack holds both lines under the heading; a name both `a` and `c` declare is not used; a file in `b` with more than 3 matching lines gives 3, and when its first matches hold one name each and a later line names a file of `a`, that later line is among them; a build-file module whose Java source names one of `a`'s files gives that line, and a line of it holding only a function name `a` declares gives none; the header's dependency lines read `-`; the build-file module's pack is byte-identical with and without `a`.

## Tasks

### Task 1 - The reader
Decision 1, with its tests.

### Task 2 - The dispatch, wiring and possible references
Decisions 2, 3 and 4, with their tests and the mixed-module test. Reshape `wired_from` as decision 4 says.

### Task 3 - Documents
`protocol/kb.md`, "What `write` reads" (line 34): Java and `.proto` through their readers; every other source through a reader that keeps declarations by indentation, in any language; for a directory module, its build and manifest files and the possible references, which are not dependencies. The "How `write` keeps the cost down" paragraph names the possible references beside the construction sites.

## Gate

On the clones of phase-01.md's Gate, rebuilt at the commit under test (`$S/fondue` re-cloned; the others unchanged).

**G1. No skeleton ends with a bracket open.** For every sample, every file a directory module holds is read with `generic_skeleton`, and the output's balance, counted line by line on code parts and never below zero, ends at zero:
```
python3 - $S/<label> <<'EOF'
import sys; sys.path.insert(0, "protocol/kb"); import kb
kb.set_root(sys.argv[1]); mods = kb.modules(); bad = []
for m in mods.values():
    if m.kind != "dir": continue
    for f in m.sources:
        if f.suffix in (".java", ".proto"): continue
        bal, block = 0, False
        for line in kb.generic_skeleton(kb.read(f)).splitlines():
            code, block = kb.code_part(line, block)
            bal = max(0, bal + kb.balance(code))
        if bal: bad.append(str(f))
print(len(bad), bad)
EOF
```
It prints `0 []` for each of c, shell, fondue, java-vue, java and hono (the names `code_part` and `balance` are the reader's helpers; the snippet follows whatever the implementation calls them). The count runs on code parts, as `pre-plan/results/brackets.py` (pre-plan research R4) ran on whole lines, because the reader keeps a comment's first line, whose prose may open a bracket it never closes ("(e.g. in case of"); a declaration that lost its end shows either way.

**G2. Compression.** Over the same files, the sum of raw lengths divided by the sum of skeleton lengths is at least: c 4, java-vue 3, hono 2, fondue 5, shell 1.5. The request reports each figure. The prototype's are 5.2, 3.6, 2.2, 6.1 and 1.9; hono's margin is the smallest, so a change that grows the output by more than a tenth shows there first.

**G3. Possible references and headers.** `python3 protocol/kb/kb.py pack <ids> --root $S/<label>`, then in `fondue/kb/.packs/`:
* no directory module's header has anything but `-` after `depends on (project):` or `depended on by:`;
* shell: `provision`'s possible references hold a line of `Makefile` and a line of `Vagrantfile` that each name one of its scripts;
* c: `include`'s hold a line from a file of each of `examples/bootstrap_server`, `examples/client`, `examples/lightclient`, `examples/server` and `examples/shared`;
* java-vue: the shared web part's hold lines from files of both other web parts;
* hono: `src-router`'s hold a line of `src/hono.ts` and a line of `src/preset/quick.ts` or `src/preset/tiny.ts`.

**G4. The Java gate**, as in phase-01.md's G2: `IDENTICAL`.

**G5. Tests.** The build is green, with every test of this phase and of Phase 1.

The request carries `Build:` and `Gates:` with G1's six outputs, G2's figures, G3's checks, and G4's `IDENTICAL`.
