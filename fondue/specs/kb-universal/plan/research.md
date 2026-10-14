# Research - kb-universal, plan

The mechanisms the phase files' technical decisions rest on. Sample projects are named as the brief names them, and `<p>` stands for the Java + Vue project's own name, as in `pre-plan/01-research.md` (cited "pre-plan R1-R11"). Paths are in `pre-plan/samples.local.md`; a command below writes `<the shell project>` and so on. `<hono>` is a clone of `https://github.com/honojs/hono.git` at `588ec13fa68ea44fed1b5e1b503341db2bf09d70` (pre-plan R11).

The prototypes are in `plan/results/`: `discover.py` (Phase 1's module rule), `reader.py` (Phase 2's reader, `pre-plan/results/skel.py` repaired), `refs.py` (Phase 2's possible references). Each docstring states its rule. They are research, not the implementation.

## Carried from pre-plan research

* `kb.py` is unchanged since `1bc80fe` (pre-plan research's code anchors are at `e93b5e8`). RESULT: `git diff 1bc80fe HEAD --stat -- protocol/kb/` prints nothing.
* The sample Java project's 38 packs are reproducible byte for byte on a `git clone --local` clone, across `PYTHONHASHSEED` (pre-plan R7). 38 packs, 845,193 chars.
* `git ls-files` lists a submodule as one path, mode `160000`, which is a directory on disk (pre-plan R9).
* `narrow_split` reads every found module's `.java` (kb.py:118) and `wired_from` every other module's `.java` (kb.py:378-382), and the sample Java project's `specs/` directory holds `.java` files (pre-plan R10). Java links must be computed among build-file modules only.
* The hand-written C parser of the brief lost multi-line signatures; continuation lines while a bracket is open keep them (pre-plan R4).

## R1. git pathspecs for a directory module's files
```
$ git init; mkdir -p src/main/java a/b
$ files: Makefile, src/main/java/A.java, a/f.sh, a/b/g.sh, é.sh; commit; change all five; commit
$ git diff --numstat $base HEAD -- ':(glob)*'
1	0	Makefile
1	0	"\303\251.sh"
$ git diff --numstat $base HEAD -- a ':(exclude)a/b'
1	0	a/f.sh
$ git diff --numstat $base HEAD -- ':(glob)a/*'
1	0	a/f.sh
$ git --version
git version 2.50.1 (Apple Git-155)
```
`:(glob)<dir>/*` (and `:(glob)*` at the root) takes the files directly in a directory and nothing below; `:(exclude)` takes a directory out. So the files a module owns in a directory, without those of modules below it, can be named to `git diff` as `kb.py` already names `main` minus `excluded` (kb.py:619).

## R2. Paths git quotes
In the same repository:
```
$ git ls-files
Makefile
a/b/g.sh
a/f.sh
src/main/java/A.java
"\303\251.sh"
$ git ls-files -s -z | tr '\0' '\n'
100644 814f4a4... 0	Makefile
...
100644 b69f59f... 0	é.sh
$ git diff --name-only -z $base HEAD | tr '\0' '\n'
...
é.sh
```
Without `-z`, a non-ASCII path comes back quoted and escaped, so `kb.py`'s `Path(p)` names a file that does not exist. With `-z` it comes back as it is, and `ls-files -s -z` gives the mode that marks a submodule.

## R3. `unittest` discovery with a helper module
```
$ mkdir tests; tests/test_a.py imports helper and asserts helper.X == 1; tests/helper.py: X = 1
$ python3 -m unittest discover -s <dir>/tests        (run from another directory)
Ran 1 test in 0.000s
OK
```
`discover -s <dir>` puts `<dir>` on the import path, so a test file imports a helper next to it and, through a path insert, `kb.py`. Python here is 3.14.8.

## R4. Phase 1's rule on the samples
`python3 plan/results/discover.py <sample>`: build-file modules as `kb.py` finds them, then directory modules by the rule of phase-01.md (code list, default exclusions, budget 250,000 bytes, floor 5,000 bytes, a group holding a build-file module's directory splits).
```
<the sample C project>    0 build-file modules, 12 directory modules
  residual .                          2 files    14826 bytes
  group    <protocol>                       4 files    95982
  residual core                      25 files   410890      (over the budget, no subdirectory)
  group    data                       8 files   196629
  group    examples/bootstrap_server  4 files    54979
  group    examples/client           14 files   195295
  group    examples/lightclient       5 files    52318
  group    examples/server            2 files    40106
  group    examples/shared            3 files    27729
  group    include                    1 files    39353
  group    tools                      1 files    14525
  group    transport                  5 files    32622
<the shell project>       0, 2: residual . (2 files, 7022), group provision (4 files, 17011)
fondue                    0, 2: group integrations (1 file, 3258), group protocol (3 files, 38392)
<the Java + Vue project>  24, 5: group <p>-demo-bsserver/webapp (21 files), <p>-demo-server/webapp (58),
                                 <p>-demo-servers-shared/webapp (19), <p>-integration-tests (1),
                                 <p>-...-core/certificates (1)
<the sample Java project> 38, 3: group deploy (7 files), scripts (4), specs (13)
<hono>                    0, 14: residual . (2), adapters (43), benchmarks (49), perf-measures (4),
                                 runtime-tests (4), residual src (12 files, 154143; folds src/preset, src/request),
                                 src/adapter, src/client, src/helper, src/jsx, src/middleware, src/router,
                                 src/utils, src/validator (8522 bytes)
```
The floor folds hono's `src/preset` (1,229 bytes) and `src/request` (56) and nothing else on any sample. The next smallest child of a size split is hono's `src/validator` at 8,522 bytes. No sample has a source file directly in a build-file module's directory, so none has a directory module sharing one; a fixture covers that case. `deploy` counts `Dockerfile.edge`, `Dockerfile.security`, `Dockerfile.server`, which the name rule `Dockerfile.*` takes.

## R5. What build-file modules hold under `src/main`
```
$ cd <the sample Java project>; git ls-files | grep /src/main/ | <count by extension>
[('.java', 386), ('.yml', 10), ('.proto', 8), ('.xml', 5), ('.xsd', 3)]
$ cd <the Java + Vue project>; (same)
[('.java', 702), ('.xml', 359), ('.der', 4), ('.html', 2), ('.xsd', 2), ('.properties', 1)]
```
Neither holds a file on Phase 1's code list other than `.java` and `.proto`, so sending every other code-list file of a build-file module to the new reader changes none of their packs.

## R6. Phase 2's reader on the samples
`python3 plan/results/reader.py <sample> --check`, over the files `discover.py`'s directory modules hold; "open" counts skeletons that end with a bracket open, by the reader's own string- and comment-aware count:
```
<the sample C project>    74 files, raw 1175236, skeleton 227559, 5.2x; ending with a bracket open: 0
<the shell project>        6 files, raw   24005, skeleton  12343, 1.9x; 0
fondue                     4 files, raw   41631, skeleton   6801, 6.1x; 0
<the Java + Vue project> 100 files, raw  313592, skeleton  87945, 3.6x; 0
<hono>                   290 files, raw  923747, skeleton 413296, 2.2x; 0
<the sample Java project> 24 files, raw  164240, skeleton  68218, 2.4x; 0
```
Against plan.md's Phase 2 floors (C 4x, the web part 3x, hono 2x, fondue 5x, the shell project 1.5x), the smallest margin is hono's: 2.2 against 2.

Two repairs closed the cases the pre-plan prototype left open (pre-plan R4: 4, 2, 3 and 1 files). Brackets inside string literals and comments no longer count, and a cut line is closed. A third came from hono: `tag.replace(/^W\//, '')` read `//` as a comment and left a bracket open for the rest of the file (`reader.py <hono> src/middleware/etag/index.ts` before the change). A trailing `//` or `#` comment now has to start the line or follow a space.

Depth 3 keeps a Vue component's methods: `reader.py <the Java + Vue project> <p>-demo-server/webapp/src/components/ClientSetting.vue` prints `methods: {` and `openTimeoutHelps() {` with their closing braces, and no method body.

## R7. Possible references on the samples
`python3 plan/results/refs.py <sample> [<module path>...] [--lines]`: per module, how many names only it declares, and the files its selected lines come from (40 lines at most; from one file the 3 holding the most of its names, a file-name hit counting 2 more; round-robin over the referencing modules):
* the shell project: `provision` has 52 names; its 6 lines come from the root module's `Makefile` (3) and `Vagrantfile` (3), among them the two of each that run its scripts by file name. Without the ranking, the 3 from `Vagrantfile` were its first three matches: port forwards holding a word a `provision` script also declares, and neither line that runs a script.
* the sample C project: `include` has 54 names and 40 lines from 9 modules, among them every `examples/*` module; `transport` 40 lines from 11 modules; `examples/shared` 17 lines, among them `examples/bootstrap_server`, `examples/client`, `examples/server`.
* the Java + Vue project: `<p>-demo-servers-shared/webapp` has 72 names and 40 lines from both other web parts (their `App.vue`, their components); `<p>-demo-server/webapp` 40 lines from the two others.
* hono: `src/router` has 49 names and 37 lines from 4 modules, among them `src/hono.ts:31: routers: [new RegExpRouter(), new TrieRouter()],` and `src/preset/quick.ts:21: routers: [new LinearRouter(), new TrieRouter()],` (both in the residual `src` module), the lines that wire routers in; `src/utils` 40 lines from 12 modules, among them `src/middleware/basic-auth/index.ts`.
* fondue: `protocol` 3 lines, from `integrations`.

Lines from build-file modules. With `refs.py`'s default, a build-file module's files under `src/main` are searched too, but only for the directory module's file names; `--all-names` searches them for every name, to show why not:
```
$ python3 plan/results/refs.py <the Java + Vue project> <p>-demo-servers-shared/webapp --lines --all-names | <count picked lines by owner>
  36 build      4 webapp        (40 lines from 23 modules)
$ (the same without --all-names)
  40 webapp                     (40 lines from 2 modules)
$ python3 plan/results/refs.py <the sample Java project> scripts --lines
  ... edge/edge-californium/src/main/java/.../EdgeIdentity.java:27: * ({@code scripts/build-identity.sh}, and the contract document c...
```
With every name, 36 of the 40 lines come from Java sources and resource files that hold a word the web part also declares, such as `config`, `hostname`, `endpoint` and `bootstrap` in Java imports, comments and XML, and the web parts' own references drop to 4. Across languages, a build-file module refers to a directory module by its files' names: a Java comment naming `scripts/build-identity.sh` is found by file name. The referencing modules are ordered by how many distinct names they hold, most first.

## R8. A name of length zero matches every line
```
$ python3 -c "import re; p = re.compile(r'\b(' + '|'.join(re.escape(t) for t in ['root', '']) + r')\b'); print(bool(p.search('nothing to do with it')))"
True
```
`skill_mentions` builds its pattern from `{m.id, m.path.name}` (kb.py:313-315); the root directory's `Path('.').name` is `''`, so a directory module at the root would match every line of every skill.

## R9. The writer's prompt today
```
$ git show 1bc80fe:protocol/kb/card-writer.md | wc -lc
      41    3164
$ git show 1bc80fe:protocol/kb/card-writer.md | tail -c 20 | od -c
... s   s   .  \n
```
41 lines, 3,164 bytes, ending in one newline. `call_writer` passes the file's text as `--system-prompt` (kb.py:475). The Java-shaped lines are 1 (the input), 28 (Boundaries), 35 (backticks) and 37 (extension mechanisms).

## R10. What `kb.py usage` can measure
`call_writer` appends one line per call to `fondue/kb/.runs/usage.jsonl`: `time`, `module`, `model`, `in`, `write` (cache creation), `read` (cache read), `out`, `cost_usd` (kb.py:484-492). The input a call paid for is `in + write + read`. `cmd_estimate` counts `len(pack) / CHARS_PER_TOKEN + WRITER_OVERHEAD` per module (kb.py:550). So a characters-per-token figure for any set of modules is `sum(len(pack)) / (sum(in + write + read) - calls * WRITER_OVERHEAD)`, with the packs taken by `kb.py pack` before the write, which is the input the write sends.

## R11. What build-file modules hold under `src/` besides `main`
```
$ cd <sample>; python3 <a script over kb.py's modules(): every tracked file under a build-file module's
                         src/, not under its main and not under src/test, counted and listed>
<the sample Java project>   0 []
<the Java + Vue project>    0 []
```
Neither sample has a tracked file under a build-file module's `src/` outside `main` and `src/test`, so claiming only `main` from directory-module discovery changes none of R4's lists (`discover.py`, which claims `main`, prints the same 3 and 5 directory modules).

## R12. What the sample Java project's directory modules hold
```
$ cd <the sample Java project>; git ls-files specs | sed -E 's/.*\.//' | sort | uniq -c
   1 console    6 gz    3 java    3 json  501 md    7 proto    1 py    2 sh   19 txt
```
`specs`' 13 sources (R4) are 3 `.java`, 7 `.proto`, 1 `.py` and 2 `.sh`; the `.py` and `.sh` go through the new reader, so its variant is `any code`. `deploy` holds shell scripts and three `Dockerfile.*`, `scripts` Python and shell (R4), both read by the new reader only.
