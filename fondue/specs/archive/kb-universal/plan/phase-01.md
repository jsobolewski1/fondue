# Phase 1 - Modules for every project

`kb.py` (`protocol/kb/kb.py`) finds modules only where a Maven or Gradle build file sits over `src/main`, and refuses every other project. This phase gives every tracked source file a module: build-file modules stay exactly as found today, and the source they do not claim forms **directory modules**. `fondue/kb/parts.txt` gains a line that excludes a path and a line that includes one. `status`, `touched` and `write --since` count a directory module's changes. A directory module's pack lists its source files by name; Phase 2 reads them. A stdlib `unittest` suite starts here and is the build from now on.

plan.md decisions delivered: D2, D3, D4, D11, D12 (the Java gate), and the Phase 1 section.

## Essential knowledge

Restated from the research, with what each was verified against:

* **The Java path today.** `modules()` (kb.py:88-109) takes every directory holding `pom.xml`, `build.gradle` or `build.gradle.kts` (`BUILD_FILES`, kb.py:32) with tracked files under `<dir>/src/main`, reads Maven dependencies (`pom_info`, kb.py:77-85), applies `parts.txt` (`split_parts`, kb.py:128-153), fills `dependents` from the poms, and narrows the split modules' dependents by Java imports (`narrow_split`, kb.py:112-125). `main()` exits when it finds none (kb.py:721-722). Code at `e93b5e8`, unchanged since `1bc80fe` (`git diff 1bc80fe HEAD --stat -- protocol/kb/` is empty).
* **`Module`** (kb.py:65-74) already has `path`, `main` (whose changes count against the card, default `path/src/main`), `build`, `parent` and `excluded` (directories taken out by parts).
* **Java-only code that would see new modules.** `narrow_split` reads every found module's `.java` text (kb.py:118); `wired_from` scans every other module's `.java` sources (kb.py:378-382); `cmd_status` collects declared types from every module (kb.py:599-604); the poms' dependents loop matches every module's `artifact` (kb.py:101-107). The sample Java project has `.java` files under `specs/`, outside its build-file modules, which become a directory module here. If any of these loops saw directory modules, a Java pack or Java status line could change (pre-plan research R10).
* **git pathspecs** (plan research R1, git 2.50.1): `:(glob)*` names the files directly in the root and nothing below; `:(glob)<dir>/*` the files directly in `<dir>`; `<dir> ':(exclude)<sub>'` takes a subdirectory out. `kb.py` already builds `main` + `:(exclude)` pathspecs (kb.py:619).
* **Quoted paths** (plan research R2): without `-z`, `git ls-files` and `git diff --name-only` quote and escape a non-ASCII path (`"\303\251.sh"`), which `Path()` then mis-names. With `-z` the path comes back as it is; `git ls-files -s -z` gives `<mode> <sha> <stage>\t<path>\0`, and mode `160000` marks a submodule, which is a directory on disk (pre-plan research R9).
* **The root's name is empty** (plan research R8): `Path('.').name == ''`, and `skill_mentions` (kb.py:311-321) builds a pattern from `{m.id, m.path.name}`; an empty alternative matches every line of every skill.
* **Packs are reproducible** on a `git clone --local` clone of the sample Java project, across `PYTHONHASHSEED`: 38 packs, 845,193 chars, `diff -r` identical (pre-plan research R7). This is what makes the Java gate a check that fails only on a real change.
* **What the rule gives on the samples** (plan research R4, `plan/results/discover.py`, a prototype of this phase's rule): see the Gate's table. The floor folds only hono's `src/preset` (1,229 bytes) and `src/request` (56 bytes); the next smallest child of a size split on any sample is 8,522 bytes.
* **unittest** (plan research R3): `python3 -m unittest discover -s <dir>` puts `<dir>` on the import path, so a test file imports a helper module beside it.
* **What build-file modules hold under `src/` besides `main`** (plan research R11): in the two Java samples, only `src/test`. So taking only `main` out of directory-module discovery, rather than all of `src/`, adds no module on either, and the Gate's lists hold.

## Technical decisions

### 1. Listing tracked files
One helper lists the tracked files once per run with `git ls-files -s -z`, skips mode `160000` entries, and returns `Path`s. `modules()` finds build files from it instead of `git("ls-files").splitlines()` (kb.py:90). `changed_modules` reads `git diff --name-only -z`. For the ASCII paths of the sample Java project the lists are the same, which the Java gate checks.

### 2. What is a source outside the build-file modules
A tracked file is a directory-module source by the first rule that applies, in this order:
1. under `fondue/`: no.
2. under the `main` directory of a build-file module (its `src/main`, for a module `modules()` finds, not a part): no. That module owns it, as today. The rest of its `src/` goes through the rules below like any other path: `src/test` is out as a test directory (rule 5), and a `src/frontend/app.ts` beside `src/main` is a source.
3. matched by an exclude line of `parts.txt`: no.
4. matched by an include line: yes, whatever its extension and wherever it sits.
5. a directory on its path starts with `.` (hidden), or is named `test`, `tests`, `__tests__`, `testing`, `e2e` or `spec` (tests), or `vendor`, `third_party`, `third-party`, `node_modules`, `dist`, `build`, `target`, `out` or `generated` (vendored or generated): no.
6. its name matches `test_*.py`, `*_test.<ext>`, `*.test.<ext>`, `*.spec.<ext>`, `*_spec.rb`, `*Test.java` or `*Tests.java`: no.
7. its extension, compared lower-case, is on the code list, or its name is on the name list, or starts with `Dockerfile.`: yes.
8. otherwise: no.

The code list: `.c .h .cc .cpp .cxx .hh .hpp .hxx .m .mm .cs .go .rs .swift .kt .kts .scala .groovy .java .proto .js .mjs .cjs .jsx .ts .mts .cts .tsx .vue .svelte .py .rb .php .pl .pm .lua .sh .bash .zsh .ksh .ps1 .dart .ex .exs .erl .hs .clj .cmake .tf .zig .nim .jl .r`. The name list: `Makefile makefile GNUmakefile Dockerfile Containerfile Vagrantfile Rakefile Justfile justfile CMakeLists.txt Jenkinsfile`. Markdown and data formats are not on them (plan.md D4); a file with no extension is a source only by name or by an include line.

Both lists and both directory sets are module-level constants next to `BUILD_FILES`.

### 3. `parts.txt` line kinds
`#` starts a comment, blank lines are skipped, as today. A line is one of:
* `- <pattern>`: exclude.
* `+ <pattern>`: include.
* `<card id> <directory>`: a part, as today.

A symbol, not a word, marks the two new kinds because a card id can be any word: the sample C project has a directory module called `include`. Any other line with other than two tokens stays the error it is today (`<file>:<line>: expected ...`, now naming all three forms).

A pattern matches a path when it equals the path, names a directory the path is under, or matches the whole path as an `fnmatch.fnmatchcase` glob, where `*` also crosses `/` (so `*.zig` matches every `.zig` file). Patterns are relative to the project root.

The file is read once per run, before directory modules are formed; parts are applied after, as today.

### 4. Directory modules
**Roots** are the repository root and the directory of every build-file module that is not a part. The source files of D2 group top-down, from the root:
* In a directory being split, the files directly in it form its **residual** module, and the rest group by their first directory below it. Each such child group is:
  - **split** the same way, when its directory is a root or holds one below it (a structural split), or when its sources exceed the **budget** (a size split);
  - otherwise, after a size split only, **folded** into the residual when its sources are under the **floor**;
  - otherwise one **group** module.
* Folding happens only in a size split. The first-level directories of the root, of a build-file module's directory, and of any directory split to reach one, are never folded.
* A residual exists when the split directory holds files directly or folded children. When a directory over the budget has no subdirectory (the C project's `core`), its residual holds all of it.

**Budget** 250,000 bytes; **floor** 5,000 bytes. A group's size is the sum of its source files' sizes on disk (`stat().st_size`), so no file is read to find modules. The budget is about the sample Java project's largest module (224,310 chars), whose card `kb.py status` passes. The floor folds the two stray leaves on the samples and nothing else (plan research R4).

**Ownership.** Every tracked source belongs to exactly one module. A **group** at `d` owns every tracked file under `d`, minus `excluded`, and minus the `main` of every build-file module under `d` (a group `src` in a build-file module's directory holds its `src/frontend`, never its `src/main`). A **residual** at `d` owns the files directly in `d`, except those named in `BUILD_FILES` (a build-file module's), plus every file under its folded directories, minus `excluded` and minus any build-file module's `main` under them. A residual may sit in a build-file module's directory, owning only the files directly there that the module does not claim (plan.md D2). Changes count against an owner the same way: any tracked file in its scope, source or not, as a build-file module counts all of `src/main`.

**Ids.** A directory module's id is its path with `/` replaced by `-`; the residual at the root is `root`. Build-file modules take their ids first, as today; directory modules then take theirs in path order. An id already taken gets `-dir`, then `-dir2`, `-dir3`, ... A part's id that clashes stays the error it is today.

### 5. The module model
`Module` gains `kind` (`"build"` for a build-file module and its parts, `"dir"` for a directory module and its parts) and `folded` (a residual's folded directories; empty otherwise), and a residual is marked (e.g. `residual = True`). A directory module has `main = path`, `build = path`, `artifact = id`, `deps = []`.

Two functions replace the path-prefix ownership that `module_of` (kb.py:156-161) and `cmd_status` (kb.py:619) each spell out:
* `owns(m, p)`: build kind, `m.main` is a parent of `p` and no `excluded` directory is `p` or a parent of it; group, the same with `m.path`, and no build-file module's `main` is a parent of `p`; residual, as in decision 4.
* `pathspecs(m)`: build kind, exactly today's `[str(m.main), *(":(exclude)<d>" for d in m.excluded)]`; group, `[str(m.path)]`, then `:(exclude)<main>` for each build-file module's `main` under it, then the excludes; residual, `:(glob)*` at the root or `:(glob)<d>/*` elsewhere, then each folded directory, then `:(exclude)<d>/<b>` for each `b` in `BUILD_FILES`, then `:(exclude)<main>` for each build-file module's `main` under a folded directory, then the excludes.

**The owner of a path** is the module that owns it, and when more than one does (a part inside its parent's scope), the one whose root (`main` for build kind, `path` for dir kind, the folded directory for a path a residual owns through it) has the most parts. `module_of` is removed.

### 6. Where each command uses them
* `changed_modules(sha, mods)`: from `git diff --name-only -z <sha> HEAD`. A path named in `BUILD_FILES` adds the build-kind modules whose `build` is its directory, as today; any other path adds its owner, if it has one. For the Java path this is today's result: a part's root is longer than its parent's.
* `cmd_status`: the changed count is `git diff --numstat <sha> HEAD -- <pathspecs(m)>`. The declared types for the dead-name check come from build-kind modules only, so a Java card's line is what it is today.
* `split_parts`: a part's parent is the owner of a file inside the part's directory, instead of the first module whose `main` contains it (kb.py:142). The error for a directory no module owns reads `<file>:<line>: <dir> is in no module`. A part of a dir-kind module is a dir-kind group at its directory; its parent loses its files and gets the directory in `excluded`, as a build-kind parent does today.
* Java links among build-kind modules only: the poms' dependents loop (kb.py:101-107) matches build-kind targets; `narrow_split` takes its split modules and its texts from build-kind modules; `wired_from` scans build-kind modules. `pack` calls `wired_from` and `wiring` for build-kind modules only.
* `skill_mentions`: a dir-kind module's names are its id and, unless it is at the root, its path as a string (`src/utils`), never `Path('.').name`. Build kind unchanged.
* `cmd_index` groups by first path segment, as today; the root's modules group under `.`.

### 7. A directory module's pack
* The header is `module_header`'s, unchanged: its dependency lines read `-`. A residual gets one more line after `path:`, `holds: the files directly in <d>` and `, and <folded>/` for each folded directory.
* README: `<path>/README.md`, as today.
* Declarations: `.java` and `.proto` sources through their readers, as today; every other source listed under the heading the pack already uses for Kotlin, `### Sources this tool cannot read declarations from (names only)`. A build-kind module's declarations are not touched in this phase.
* No wiring and no construction sites yet (Phase 2).

### 8. Commands' output
* `kb.py modules` adds each module's size, in thousands of bytes of its sources: `f"{mid:40} {str(m.path):60} {len(m.sources):>4} files {size // 1000:>6}k"`. A script that takes ids takes the lines whose fourth field is `files`.
* `main()`, when no module is found, exits with `no source found: kb.py found no build-file module and no tracked source file; an include line in fondue/kb/parts.txt can name one (protocol/kb.md)`.

### 9. Tests (the build)
* `protocol/kb/tests/fixture.py`: builds a small git repository in a temporary directory from a `{path: text}` map, commits with a fixed author, and can commit a change; points `kb.set_root` at it.
* `protocol/kb/tests/test_modules.py`: this phase's tests.
* Tests import `kb` by putting `protocol/kb` on `sys.path`.
* **Build:** `python3 -m unittest discover -s protocol/kb/tests`, from the repository root. Green means every test passes.

## Tasks

### Task 1 - Sources and `parts.txt`
The tracked-file helper (decision 1), the source rule (decision 2), and the `parts.txt` parser with its three line kinds (decision 3).

Tests:
* each rule of decision 2 on a fixture: `fondue/`, a build-file module's `src/test`, a hidden directory, each test directory name, a vendored directory, each test-file pattern, an extension in upper case, `Dockerfile.edge`, a file with no extension that is not on the name list;
* a submodule entry is skipped (a fixture with `git submodule add` of a second fixture repository, or an index entry added with `git update-index --add --cacheinfo 160000,<sha>,<path>`);
* `- <dir>` removes a module; `- <glob>` removes matching files; `+ <glob>` makes a file with an extension on no list, and with no shebang, a source in a fixture that has no other source, and `kb.py` then finds a module where it refused before; `-` wins over `+` on the same path;
* a malformed line exits with its line number.

### Task 2 - Directory modules, ownership, ids
Decisions 4 and 5, wired into `modules()` after the build-file modules and before `split_parts`.

Tests:
* the root and a first-level directory: a file at the root and one in `a/` give modules `root` and `a`;
* a size split: a directory over the budget with children above and under the floor gives a group per large child and a residual holding the small ones; a first-level directory under the floor is still a module of its own;
* a structural split: a group that holds a build-file module's directory below it splits down to it;
* a residual in a build-file module's directory: a Maven fixture at the root with `src/main/java/A.java` and a root `Makefile` has both modules, with distinct ids, and a change to each one's source counts only against its owner, in `status` and in `changed_modules` (the plan.md Phase 1 gate's fixture);
* source beside `src/main`: a Maven fixture at the root with `src/main/java/A.java` and `src/frontend/app.ts` has a directory module holding `app.ts` (the group `src`), whose `pathspecs` exclude `src/main`; a change to each file counts only against its owner; and the build-file module's pack is byte-identical to its pack in the same fixture without `src/frontend`;
* a change to a directory module's own file, and to a file under one of its folded children, counts against it; a change in a separate module below it does not;
* an id clash: a directory module whose id a build-file module already has gets `-dir`;
* a part inside a directory module takes its files, and its parent's changes no longer count them; a part the User names inside a folded child gets its own card;
* a non-ASCII file name is a source and its change is counted;
* the root's skill mentions do not match an unrelated skill line.

Use small budget and floor values in tests by patching the module constants.

### Task 3 - Commands and packs
Decisions 6, 7 and 8: `changed_modules`, `cmd_status`, `split_parts`, the Java-only loops, `skill_mentions`, `pack` for a directory module, `cmd_modules`, `main()`.

Tests:
* `pack` of a directory module: header lines read `-`, a residual's `holds:` line, the names-only list;
* `kb.py modules` prints the size column;
* a fixture with no source exits with the new message;
* `estimate`, `write --since` (with the writer call stubbed) and `touched` take directory modules.

### Task 4 - Documents
* `protocol/kb.md`: the `modules` row (line 23) says what a module is now, build-file modules and directory modules, in a sentence each; the `parts.txt` paragraph (line 10) gains the exclude and include lines and their patterns.
* `skills/kb-init/SKILL.md` step 1 (line 18): it stops only when `kb.py` finds no source, and then tells the User that an include line can name one; the module list shows sizes; a directory module that looks wrong is fixed with `parts.txt` (split, exclude, include).

## Gate

Run on clones, never on the samples themselves (plan.md D12). In a scratch directory `$S` outside this repository, one clone per sample, named by label; the paths are in `fondue/specs/kb-universal/pre-plan/samples.local.md`:
```
git clone --local <the sample C project> $S/c
git clone --local <the shell project> $S/shell
git clone --local <this repository> $S/fondue                 # at the commit under test
git clone --local <the Java project with a Vue/JavaScript web part> $S/java-vue
git clone --local <the sample Java project> $S/java
git clone https://github.com/honojs/hono.git $S/hono && git -C $S/hono checkout 588ec13fa68ea44fed1b5e1b503341db2bf09d70
```

**G1. Module lists.** `python3 protocol/kb/kb.py modules --root $S/<label>` prints exactly these modules, by id and path, in any order. `<p>` is the Java + Vue project's own name, which its directories carry.

| sample | build-file modules | directory modules (id, path) |
|---|---|---|
| c | none | `root` `.`; `<protocol>`; `core`; `data`; `examples-bootstrap_server` `examples/bootstrap_server`; `examples-client` `examples/client`; `examples-lightclient` `examples/lightclient`; `examples-server` `examples/server`; `examples-shared` `examples/shared`; `include`; `tools`; `transport` |
| shell | none | `root` `.`; `provision` |
| fondue | none | `integrations`; `protocol` |
| java-vue | the 24 that `kb.py` at `1bc80fe` prints, unchanged | `<p>-demo-bsserver-webapp` `<p>-demo-bsserver/webapp`; `<p>-demo-server-webapp` `<p>-demo-server/webapp`; `<p>-demo-servers-shared-webapp` `<p>-demo-servers-shared/webapp`; `<p>-integration-tests`; and the `certificates` directory of the build-file module whose name ends in `-core`, id its path with `-` |
| java | the 38 that `kb.py` at `1bc80fe` prints, unchanged | `deploy`; `scripts`; `specs` |
| hono | none | `root` `.`; `adapters`; `benchmarks`; `perf-measures`; `runtime-tests`; `src` (a residual whose `holds:` line names `src/preset/` and `src/request/`); `src-adapter`; `src-client`; `src-helper`; `src-jsx`; `src-middleware`; `src-router`; `src-utils`; `src-validator` |

No module a size split made is under the floor: on every sample, every directory module that is not a residual and sits below a directory over the budget has at least 5,000 bytes (`modules`' size column, and the request shows the sizes).

**G2. The Java gate** (plan.md D12):
```
git -C <this repository> show 1bc80fe:protocol/kb/kb.py > $S/kb-base.py
ids=$(python3 $S/kb-base.py modules --root $S/java | awk '$4=="files"{print $1}')    # 38 ids
python3 $S/kb-base.py pack $ids --root $S/java > /dev/null && mv $S/java/fondue/kb/.packs $S/packs-base
python3 protocol/kb/kb.py pack $ids --root $S/java > /dev/null && mv $S/java/fondue/kb/.packs $S/packs-new
diff -r $S/packs-base $S/packs-new && echo IDENTICAL
```
It prints `IDENTICAL`. Also `python3 protocol/kb/kb.py status --root $S/java` prints, for the 38 build-file modules, the same lines as `python3 $S/kb-base.py status --root $S/java`; the three directory modules add `no card` lines.

**G3. Tests.** The build is green, with every test of Tasks 1-3.

The request carries `Build:` and `Gates:` with G1's six outputs, G2's `IDENTICAL` and its `status` comparison, and `$S`.
