## #1 `changed_modules` drops a change to a build-file-named file that a directory module owns, while `status` counts it

**Severity:** Blocker

`changed_modules` (kb.py:713-715) handles every path named in `BUILD_FILES` by adding the build-kind modules whose `build` is its directory, then `continue`s, so it never asks `owner()`. When no build-file module lives in that directory, the change is lost. But a group directory module owns such a file (`owns`, kb.py:309-310), and `cmd_status` counts it through `pathspecs` (`[str(m.path)]`). A `build.gradle.kts` is even one of the group's *sources* (`.kts` is on the code list). This happens wherever a Gradle or Maven build file sits in a directory with no `src/main`, e.g. a Kotlin Multiplatform module (`src/commonMain`) or an aggregator pom under a directory module. The phase file's decision 4 says "Changes count against an owner the same way: any tracked file in its scope, source or not", and its intro says `touched` and `write --since` count a directory module's changes. Here they don't, so `write --since` leaves that card as it was.

RESULT, with the fixture `{"shared/build.gradle.kts": ..., "shared/src/commonMain/kotlin/A.kt": "class A\n"}`, a card for `shared` at the first commit, then a commit that changes `shared/build.gradle.kts` (`<scratch>/cr01/a_build_file_in_group.py`):
```
modules: {'shared': ['shared/build.gradle.kts', 'shared/src/commonMain/kotlin/A.kt']}
changed_modules: set()
touched: modules: -
status: shared                                          2
```

**Proposed solution:** in `changed_modules`, fall through to the owner when no build-kind module is built by that file:
```python
        if p.name in BUILD_FILES:
            built = {m.id for m in mods.values() if m.kind == "build" and m.build == p.parent}
            if built:
                changed |= built
                continue
        m = owner(p, mods, mains)
```
For a Java build-file module nothing changes. A residual still never owns a build-file-named file directly in its directory (`owns`, kb.py:311), so it stays consistent with its `pathspecs`. Add a test in `DirectoryModules`: the fixture above, a change to `shared/build.gradle.kts` gives `changed_modules` `{"shared"}` and a non-zero `status` count for `shared`.

## #2 A `parts.txt` line whose directory holds more than one module is accepted and builds a wrong module

**Severity:** Blocker

`split_parts` (kb.py:278) takes as the parent the owner of the first owned file under the part's directory, and checks nothing else. When the directory holds files of several modules, or is wider than the directory the parent owns its files through, the part takes one module's sources but gets a scope (`pathspecs`, `owns`) that covers the whole directory. That breaks D2's "every tracked source file belongs to exactly one module, and a module's changes are its own source files'". It also loosens the Java check: `kb.py` at `1bc80fe` refused a part that was not inside a module's `src/main`. Now that part silently replaces the module, and its `main` becomes the module's directory.

RESULT (`<scratch>/cr01/b_part_spanning.py`). First, a Maven project with modules `core` and `api`, and `core-all core` in `parts.txt`. Second, with `BUDGET=1000` and `FLOOR=100`, `{"big/a.c": 10 bytes, "big/l1/x.c": 600, "big/l2/y.c": 600}`, then `big-all big` in `parts.txt` and a change to `big/l2/y.c`:
```
1bc80fe: fondue/kb/parts.txt:1: core is in no module's src/main
7c7d29f: api   api   1 files   0k | core-all   core   1 files   0k | 2 modules
before: {'big': ['big/a.c'], 'big-l1': ['big/l1/x.c'], 'big-l2': ['big/l2/y.c']}
after:  {'big-l1': ['big/l1/x.c'], 'big-l2': ['big/l2/y.c'], 'big-all': ['big/a.c']}
pathspecs big-all: ['big']
status: ... | big-all   2 | big-l1   0 | big-l2   2 | clean
```
`core` is gone and `core-all` stands in for it with `main` `core`. In the second case, `big-l2`'s change counts against `big-all` too.

**Proposed solution:** in `split_parts`, refuse a part whose directory is not inside one module:
```python
        d = Path(rel)
        owned = [(f, o) for f in files if d in f.parents for o in [owner(f, found, mains)] if o]
        parent = owned[0][1] if owned else None
        if parent is None or pid in found:
            sys.exit(f"{where}:{no}: " + (f"`{pid}` is taken" if parent else f"{rel} is in no module"))
        if any(o is not parent for _, o in owned) or not within(d, owns(parent, owned[0][0], mains)):
            sys.exit(f"{where}:{no}: {rel} is not inside one module")
```
The first condition refuses a directory that holds another module's files. The second refuses one wider than the parent's own scope: for build kind it is `1bc80fe`'s check that the directory is `main` or below it. The sample Java project's five parts lie inside one module's `src/main` and pass both. Add two tests that exit with `parts.txt:1: <dir> is not inside one module`: the Maven fixture with `core-all core`, and `DirectoryModules.big()` with `big-all big`.

## #3 A residual's `holds:` line still names a folded directory that a part took

**Severity:** Nit

`split_parts` adds the part's directory to `parent.excluded` (kb.py:286) but leaves `parent.folded` as it is. `module_header` (kb.py:524) prints every folded directory. In `test_part_inside_a_folded_child`, `big`'s pack therefore reads `holds: the files directly in big, and big/s/`, but `big/s` is `big-s`'s, and `big`'s declarations no longer list it.

**Proposed solution:** in `split_parts`, after `parent.excluded.append(d)`, add `parent.folded = [f for f in parent.folded if f != d]`. In `test_part_inside_a_folded_child`, assert that `kb.pack(mods["big"], mods, {})` contains `"holds: the files directly in big\n"`.

## #4 `protocol/kb.md` says `-` and `+` apply wherever a path sits, but neither reaches a build-file module's `src/main` or `fondue/`

**Severity:** Nit

kb.md:12-13 say "`- <pattern>`: what the pattern matches is not source" and "`+ <pattern>`: ... whatever its extension and wherever it sits". `is_source` applies the `fondue/` and `src/main` rules before either line (kb.py:161-165), and build-file modules are found without the rules (kb.py:232-239). So `- legacy-module` leaves a Maven module in place, and nothing tells the User why.

**Proposed solution:** in kb.md:15, after "whose `*` also crosses `/`.", add: "Neither line applies under `fondue/` or under a build-file module's `src/main`, which stays that module's."

## #5 A directory module's part names its own directory as its parent's

**Severity:** Nit

A dir-kind part gets `build=d` (kb.py:290). `module_header` prints `part of module {m.parent} ({m.build})` (kb.py:514), so `test_part_inside_a_group`'s part reads `part of module a (a/sub)`. For a build-kind part, the parenthesis is the parent's directory.

**Proposed solution:** for a dir-kind part, print the parent's path in that parenthesis, e.g. by keeping it as `build` (`build=parent.build`, which for a directory module is its path).

Verdict: approved-with-fixes git diff 461dd00..7c7d29f | #1, #2, #3, #4
