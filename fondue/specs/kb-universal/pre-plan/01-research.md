# Research - kb-universal, pre-plan

The sample projects are named as the brief names them. Their paths are in `pre-plan/samples.local.md`, and a command below writes `<the sample C project>` where it ran with that path. In the Java project with a Vue/JavaScript web part, directory names carry the project's own name, written `<p>` here. The TypeScript project is public and named: no TypeScript project was at hand (brief), so one was cloned (R11).

The prototypes the RESULTs ran are in `pre-plan/results/`: `skel.py` (a reader that knows no language), `layout.py` (directory modules), `links.py` (links between them), `brackets.py` (a check on `skel.py`'s output). They are research, not a design. Each one's docstring states its rule.

Code anchors are `protocol/kb/kb.py` at `e93b5e8`, unchanged since `1bc80fe`.

## Knowledge base

RESULT: `ls fondue/kb` in this repository prints `No such file or directory`. There is no knowledge base to read, so none was.

## Existing code

Each capability the goal needs, what the code has, and whether the approach reuses it, reshapes it, or adds something new.

1. **Finding modules.** `modules()` (kb.py:88-109) takes every directory with a file in `BUILD_FILES` (kb.py:32: `pom.xml`, `build.gradle`, `build.gradle.kts`) and tracked files under `<dir>/src/main` (kb.py:94-96), reads Maven dependencies with `pom_info` (kb.py:77-85), and exits through `main()` when it finds none (kb.py:721-722). **Reshape**: build-file modules stay exactly as found today, and the code they do not claim gets directory modules in the same function.
2. **The module model.** `Module` (kb.py:65-74) already separates `path`, `main` (the directory whose changes count against the card, default `path/src/main`), `build`, `parent` and `excluded`. **Reuse**: a directory module is a `Module` whose `main` is its own directory; `excluded` already exists to keep a nested module's files out of it.
3. **Splitting a module by hand.** `split_parts` (kb.py:128-153) reads `fondue/kb/parts.txt`, lines `<card id> <directory>`, and accepts a directory that is inside any module's `main` (kb.py:142). **Reshape**: the same test makes a part of a directory module with no change, because its `main` is its directory. A line that excludes a path is new; the closest existing code is this parser, so it goes there.
4. **Which module a path belongs to, and what changed.** `module_of` (kb.py:156-161, the longest module path that contains it), `changed_modules` (kb.py:519-529, build-file changes plus paths under `main`), and `cmd_status`'s `git diff --numstat` over `main` minus `excluded` (kb.py:619). **Reshape**: a directory module counts its own files only, never a nested module's.
5. **Declarations.** `declarations()` (kb.py:274-288) dispatches by suffix: `.java` to `java_skeleton` (kb.py:182-267), `.proto` to `proto_skeleton` (kb.py:270-271); `.kt`, `.scala`, `.groovy` are listed by name (kb.py:285-287); every other file is skipped (kb.py:281-282). **Reshape**: the dispatch keeps both readers unchanged and sends every other code file to one new reader that knows no language. That reader is **new**: nothing in kb.py reads a file without knowing its language, and reshaping `java_skeleton` into it would change every Java pack (R3 shows the generic reader's output is 1.0-1.6x the Java reader's on the same Java files).
6. **Declared names, for the dead-name check.** `declared_types` (kb.py:291-296) and `cmd_status` (kb.py:599-604) collect names with `TYPE_DECL` (kb.py:170) from `.java` and `.proto` only; `cmd_status` checks backticks matching `` `([A-Z]\w*)...` `` only (kb.py:605), plus paths (kb.py:606, 631). **Reshape**: the check gains names from the generic reader, lowercase included, for cards of modules that hold such code.
7. **Links between modules.** Java only: Maven dependencies (`pom_info`), "depended on by" for split modules from Java imports (`narrow_split`, kb.py:112-125, `packages`/`importer`, kb.py:360-366), and lines in other modules that construct a module's types (`wired_from`, kb.py:369-388: `new <Type>` in files that import the module's packages). `module_header` (kb.py:324-345) prints whatever `deps` and `dependents` hold. **Reshape**: `module_header` is reused as is, filled for directory modules by a new scan; `wired_from`'s shape (a pattern, a gate on which files count, the matching lines, capped at `WIRED_FROM_MAX`) serves the directory modules' "used in other modules" lines with another pattern and gate. Choosing which names of a directory module count is **new**; the closest code is `skill_mentions` (kb.py:311-321), whose rule "names of at least 6 characters" R6 reuses.
8. **Wiring files.** `wiring()` (kb.py:348-357) packs `WIRING_GLOBS` (kb.py:34: `META-INF/services/*`, Spring `application*`) from `<module>/src/main/resources`. **Reshape**: directory modules pack their build and manifest files (e.g. `package.json`, `CMakeLists.txt`) the same way.
9. **The writer's prompt.** `call_writer` passes `card-writer.md` whole as the system prompt (kb.py:475). Its Java-shaped lines: the input description (card-writer.md:1, "declarations with method bodies dropped, where other modules construct its types") and the backtick rule (card-writer.md:35, "a class, interface, record, enum or proto message header"). **Reshape**: those lines become per reader.
10. **Cost.** `CHARS_PER_TOKEN = 2.5`, "measured on Java skeletons" (kb.py:40), used by `cmd_estimate` (kb.py:545-558) and `cmd_pack` (kb.py:703). **Reshape**: a ratio per reader.
11. **Language-free already.** Project skills (`skills()`, kb.py:301-303), a module's `README.md` (kb.py:398-400), the index (kb.py:645-673, grouped by the first path segment), cards, `usage`, `touched`. **Reuse.**
12. **Tests.** RESULT: `git ls-files | grep -i test` in this repository prints nothing. kb.py has no tests and the repository no build. **New**: there is nothing to reshape.
13. **Documents that describe the Java-only tool.** `protocol/kb.md:23` (`modules`: "a directory with a build file and sources under `src/main`"), `protocol/kb.md:34` ("What `write` reads"), `skills/kb-init/SKILL.md:18` (step 1 stops when no module is found), `skills/kb-init/design-notes.md:31-33` (Known limits), `README.md:166` ("For now it reads Java and `.proto` files"). **Reshape**: edited in place.

## FACTs carried from the brief

The brief is the User's, signed off. These are its RESULTs, restated with it as the source:
* `java_skeleton` over every `.java` source of the sample Java project: 1,692,462 raw chars to 355,724, 4.8x. Its largest module is 224,310 raw chars of Java.
* On the brief's machine, the only `ctags` is BSD ctags and `tree_sitter` is not installed.
* Claude Code's marketplace has 12 LSP plugins: clangd, csharp, gopls, jdtls, kotlin, lua, php, pyright, ruby, rust-analyzer, swift, typescript. A plugin is configuration; the server is installed separately. A stdlib script got the 10 top-level functions of one file of the sample C project from `clangd` over JSON-RPC in 1.2 s; with no `compile_commands.json`, the project's own types came back as `int *`.
* `kb.py` runs as a script outside any Claude session, and its `claude -p` calls have no tools.

## RESULTs

### R1. kb.py on the samples today
`python3 protocol/kb/kb.py modules --root <sample>`:
* the sample C project, the shell project, fondue: `no modules found: kb.py reads Maven and Gradle projects with sources under <module>/src/main`, exit 1.
* the Java project with a Vue/JavaScript web part: `24 modules`. Its web parts are `<p>-demo-server/webapp`, `<p>-demo-bsserver/webapp` and `<p>-demo-servers-shared/webapp` (98 `.vue` and `.js` files, from `git ls-files`). They sit beside `src/main`, not in it, so no module holds them (kb.py:94) and no pack sees them.
* the sample Java project: `38 modules`.

### R2. Tooling on this machine
```
$ for c in clangd jdtls sourcekit-lsp typescript-language-server pyright-langserver bash-language-server vue-language-server gopls rust-analyzer; do command -v $c || echo "$c -"; done
/usr/bin/clangd
~/.local/bin/jdtls
/usr/bin/sourcekit-lsp
typescript-language-server -
pyright-langserver -
bash-language-server -
vue-language-server -
gopls -
rust-analyzer -
$ ctags --version          -> ctags: illegal option -- -   (BSD ctags)
$ python3 -c "import tree_sitter"  -> ModuleNotFoundError: No module named 'tree_sitter'
$ python3 --version        -> Python 3.14.8
```
Of the languages in the non-Java samples (C, shell, Vue, JavaScript, Python, TypeScript), only C has a server here. The marketplace list (brief) has no plugin for shell or Vue.

### R3. A reader that knows no language: how much it keeps
`skel.py`'s rule, in short: lines are kept by indentation; a block whose header has no parenthesis, or names a container keyword (`class`, `struct`, `enum`, `interface`, `impl`, ...), is a container, any other block is a body; a line is kept when every block around it is a container, up to `--depth` levels; a kept line that leaves a bracket open keeps its continuation lines. Comments: `first` keeps the first worded line of each comment run, `none` drops them.

`python3 pre-plan/results/layout.py <sample> --measure --depth D --comments C` over the files directory modules hold (R5), and `python3 pre-plan/results/skel.py <the sample Java project> --java --depth D --comments C` over every `.java` under `src/main`, raw chars / skeleton chars:

| | raw chars | depth 3, first | depth 3, none | depth 2, first | depth 2, none |
|---|---|---|---|---|---|
| sample C project (C, CMake, one shell script) | 1,175,236 | 4.7x | 5.1x | 4.8x | 5.2x |
| shell project (shell, Make, Vagrant) | 24,005 | 2.1x | 2.5x | 2.2x | 2.7x |
| web part of the Java + Vue project (Vue, JS, shell) | 313,592 | 3.6x | 3.9x | 5.4x | 5.9x |
| fondue (Python) | 41,631 | 7.3x | 7.3x | 7.3x | 7.3x |
| hono (TypeScript) | 923,747 | 2.2x | 2.5x | 2.8x | 3.2x |
| sample Java project, this reader on its Java | 1,692,462 | 3.1x | 4.3x | 3.3x | 4.6x |
| sample Java project, `java_skeleton` (brief) | 1,692,462 | 4.8x | | | |

Per extension at depth 3 / first: `.c` 7.1x, `.h` 1.3x (headers are declarations), `.vue` 4.7x, `.js` 2.6x, `.ts` 2.2x, `.sh` 1.1-1.7x (a script is mostly top-level code). On the same Java files, this reader's output is 364,584 to 553,293 chars against `java_skeleton`'s 355,724: 1.0x to 1.6x, set by how many comment lines it keeps and how deep it goes.

Depth matters for object literals: at depth 2 a Vue component written as `export default { methods: { f() {...} } }` keeps `methods: {` but not `f()`; at depth 3 it keeps `f()` (`skel.py <the Java + Vue project> <p>-demo-server/webapp/src/components/ClientSetting.vue --depth 2` and `--depth 3`).

### R4. Signatures over several lines
The brief's prototype lost the parameters of a signature split over several lines. `skel.py` keeps a kept line's continuation lines while a bracket is open. On the largest `.c` file of the sample C project, every multi-line function signature came out whole: a `static` function whose five parameters sit on five lines kept all five lines (`skel.py <the sample C project> core/registration.c`).

`python3 pre-plan/results/brackets.py <sample>` lists every file whose skeleton ends with a bracket open, i.e. has lost the rest of a declaration: the sample C project 4 of 74 files, the web part of the Java + Vue project 2 of 100, hono 3 of 290, the shell project 1 of 6, fondue 0 of 4. In the C files the causes are brackets inside string literals (`#define JSON_HEADER "{\"e\":["`), a line cut at the 220-character limit before its closing bracket, and a bracket in a comment. A reader that skips strings and comments, and cuts a long line without losing its balance, closes these.

### R5. Directory modules
`layout.py`'s rule: a code file (by extension or name; not under `fondue/` or a hidden directory, not in a test or vendored directory, not a test file, not under a build-file module's `src/`) belongs to a directory module. The repository root and every build-file module's directory split: their files group by first directory below, and the files directly in them form a module of their own. A group over a budget of raw source chars splits the same way one level down. Every other group is one module.

`python3 pre-plan/results/layout.py <sample>` (budget 250,000 raw chars, about the sample Java project's largest module, 224,310):
* **the sample C project**, 12: `.` (2 files), `<protocol>`, `core` (25 files, 410,876 raw chars, no subdirectory to split into), `data`, `examples/bootstrap_server`, `examples/client` (14 files, its three one-file launchers included), `examples/lightclient`, `examples/server`, `examples/shared`, `include`, `tools`, `transport`. `tests/` is out as a test directory.
* **the shell project**, 2: `.` (Makefile, Vagrantfile), `provision` (4 scripts).
* **fondue**, 2: `integrations` (1 file), `protocol` (3 Python files, 38,375 chars).
* **the Java + Vue project**, 24 build-file modules unchanged, and 5: `<p>-demo-bsserver/webapp` (21 files), `<p>-demo-server/webapp` (58), `<p>-demo-servers-shared/webapp` (19), `<p>-integration-tests` (one script), `<p>-...-core/certificates` (one script).
* **the sample Java project**, 38 build-file modules unchanged, and 3: `deploy`, `scripts`, `specs` (research `.java` files of old specs, which a User would exclude).
* **hono**, 16: `.`, `adapters`, `benchmarks`, `perf-measures`, `runtime-tests`, and `src` split into `src` (9 own files), `src/adapter`, `src/client`, `src/helper`, `src/jsx`, `src/middleware`, `src/preset` (1,229 chars), `src/request` (56 chars), `src/router`, `src/utils`, `src/validator`. `.test.ts` files are out as test files.

Two variants were run and dropped:
* **Package manifests as module boundaries** (`package.json`, `Cargo.toml`, `go.mod`, ...): on hono, `adapters/` and `benchmarks/` hold one `package.json` per sub-package, and they became 16 modules, `adapters/vercel` at 1,079 raw chars among them. Without manifests the Java + Vue project's three web parts still come out as three modules, because a build-file module's directory splits.
* **A budget of 150,000**: the C project's `examples/client` split into `common` and three one-file launchers of about 1,000 chars each; the web part's `<p>-demo-server/webapp` split into 7, `router` at 2,286 chars.
* **The budget on skeleton size instead of raw size**: the C project's `examples/` (28 files, five programs) has a skeleton of 61,665 chars with comment lines kept and 56,782 without, so under a 60,000-char budget it is five modules or one depending on a reader setting. On raw size (370,424 chars) it is five whatever the reader does.

### R6. Links between directory modules by name
`links.py`'s rule: a module's names are what its skeleton declares, 6 characters or longer, declared by that module only; module A uses B when A's source holds at least 3 of B's names as words, or one of B's file names. `python3 pre-plan/results/links.py <sample>`, the edges a reader of the code would expect:
* the sample C project: `include` is used by `<protocol>`, `core`, `data`, every `examples/*` and `transport`; `transport` by every `examples/*` but `shared`; `examples/shared` by `examples/bootstrap_server`, `examples/client`, `examples/server`.
* the shell project: `provision` is used by `.` (9 names, its 4 file names: the Vagrantfile and Makefile run the scripts).
* the Java + Vue project: `<p>-demo-servers-shared/webapp` is used by both other web parts (12 and 5 names, 9 and 6 file names).
* hono: `src/utils` is used by 11 other modules, `src` by 11.

It also gives edges a reader would not draw, e.g. hono `src/jsx` "used by" `src/utils` (7 names), the C project's `examples/client` "used by" `core` (4 names). Thresholds are not tuned.

### R7. The sample Java project's packs are reproducible, on a clone
```
$ git clone --local <the sample Java project> <scratch>/java-sample && cd <scratch>/java-sample
$ python3 <fondue>/protocol/kb/kb.py pack $(python3 <fondue>/protocol/kb/kb.py modules | awk 'NF==4{print $1}')
$ ls fondue/kb/.packs | wc -l; cat fondue/kb/.packs/*.md | wc -c
      38
  845193
$ cp -r fondue/kb/.packs ../packs-run1; rm -rf fondue/kb/.packs
$ PYTHONHASHSEED=12345 python3 <fondue>/protocol/kb/kb.py pack <the same ids>; diff -r ../packs-run1 fondue/kb/.packs && echo IDENTICAL
IDENTICAL
$ git status --short          (prints nothing: .packs/ is ignored)
```
The largest pack is 67,646 chars. `kb.py status` on the sample Java project itself ends `clean`: none of its 38 cards is over the line limit or has a dead name. Packs do not depend on hash order, so a byte comparison of packs before and after a change is a check that can fail only on a real change. The clone carries the project's `fondue/kb/` (cards, `parts.txt`), so `pack` sees what it sees in the project.

### R8. Markdown in the sample Java project
`git ls-files '*.md' | grep -v '^fondue/' | wc -l` prints 522, and `git ls-files 'specs/*.md' | wc -l` prints 501: the specs of an older fondue layout. Markdown as a source would give them a module.

### R9. Submodules
`git ls-files -s | awk '$1=="160000"'` in the sample C project prints one entry, `transport/<tls>/third_party/<tls>`. `git ls-files` lists a submodule as one path, which is a directory on disk.

### R10. The current Java-only paths read code the generic modules would add
`narrow_split` reads the `.java` text of every found module (kb.py:118), and `wired_from` scans the `.java` sources of every other module (kb.py:378-382). The sample Java project's `specs/` directory holds `.java` files (R5). If a directory module holding them joined those scans, a Java pack could change; the build-file modules' links have to be computed among build-file modules only.

### R11. A TypeScript sample
```
$ git ls-remote https://github.com/sindresorhus/ky.git HEAD     (network check)
3541888878c4d303a8bc2ad61815f4e048f55a5d	HEAD
$ git clone --depth 1 https://github.com/honojs/hono.git && git -C hono log -1 --format=%H
588ec13fa68ea44fed1b5e1b503341db2bf09d70
$ git -C hono ls-files | wc -l       -> 583   (397 .ts, 32 .tsx, 27 .mts, 53 .json, 18 .md)
```
It has no build file kb.py knows, one `package.json` at the root and one in each of its sub-packages, and a single `src/` of 290 non-test code files.
