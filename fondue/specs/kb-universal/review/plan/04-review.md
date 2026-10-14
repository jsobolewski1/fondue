## #1 Bare file names are kept alive by unrelated modules

**Severity:** Blocker

The any-code prompt permits a bare file name from the module's input and requires a file wired in another module to be named by its repository path (`plan/phase-03.md:23-28`). The dead-name rule instead accepts a bare name when it is the last component of any tracked file in the project (`plan/phase-03.md:37-43`). If two modules contain `package.json`, removing it from the card's module leaves the stale `` `package.json` `` live because the unrelated copy remains. The planned test checks only the positive case (`plan/phase-03.md:61-68`).

**Proposed solution:** For a bare file name, check only filenames present in the subject module's packed inputs—its sources, wiring/build manifests, and any other file section the pack actually contains. A file from another module must use its repo-relative path as the prompt already requires; represent a root-level cross-module path as `./<name>` and make the path check normalize that form. Add a two-module test where both initially have `package.json`, remove the subject module's copy, and require its card's bare `` `package.json` `` to become dead while the other copy remains.

Verdict: approved-with-fixes fondue/specs/kb-universal/plan/phase-01.md, fondue/specs/kb-universal/plan/phase-02.md, fondue/specs/kb-universal/plan/phase-03.md, fondue/specs/kb-universal/plan/research.md | #1
