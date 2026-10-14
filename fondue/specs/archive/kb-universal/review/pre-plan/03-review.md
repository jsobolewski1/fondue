## #1 Direct residual source at a build root has no possible owner

**Severity:** Blocker

D2 says every build-file module's directory splits and files directly in that directory form their own directory module, but also says a directory module never shares a directory with a build-file module (`pre-plan/04-draft.md:38`). A root Maven/Gradle project with a tracked root `Makefile` exposes the contradiction: the build module owns `./src/main`, while the residual module for `Makefile` must have path `.`, which is already the build module's directory. Dropping the residual violates D4; putting it in the build module violates the byte-identical Java contract. The existing model can carry an explicit source list, but `module_of` currently chooses ownership by the longest containing path (`pre-plan/01-research.md:18-20`), so plan cannot resolve two collocated modules without the approach choosing source ownership over path exclusivity.

**Proposed solution:** Replace the directory-sharing prohibition with a source-sharing prohibition: a residual directory module may share a path with a build-file module but owns only the direct source files that module does not claim, and every tracked source belongs to exactly one module. Leave its distinct id to plan. Add a Phase 1 fixture with a root build module, `src/main`, and a root `Makefile`; gate that both modules exist and that changes to each source set count only against its owner.

Verdict: approved-with-fixes fondue/specs/kb-universal/pre-plan/04-draft.md | #1
