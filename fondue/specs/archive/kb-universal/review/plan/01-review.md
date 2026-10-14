## #1 Build-root discovery drops source beside `src/main`

**Severity:** Blocker

The approved plan says a directory module owns source that a build-file module does not claim, and every source has exactly one owner (`plan/plan.md:38`). Phase 1 instead rejects every file below the build module's whole `src/` directory (`plan/phase-01.md:26-35`), although the build module claims only `src/main`. A root Maven project with `src/main/java/A.java` and `src/frontend/app.ts` therefore loses `app.ts` entirely. Simply admitting it is insufficient: the proposed group ownership and pathspec for a `src` directory would also include `src/main` (`plan/phase-01.md:64`, `plan/phase-01.md:71-75`), making the directory module count the build module's files.

**Proposed solution:** Exclude only each build module's `main` subtree from directory-source discovery, and add every contained build `main` subtree to a directory module's ownership exclusions and pathspecs. Add a root Maven fixture with `src/main/java/A.java` and `src/frontend/app.ts`; gate that the frontend gets a directory module, each change belongs only to its owner, and the Java pack stays unchanged.

## #2 Possible references omit uses from build-file modules

**Severity:** Blocker

D7 requires possible-reference lines from "other modules" while preserving build-file modules' own Java links (`plan/plan.md:58`). Phase 2 searches only other directory modules (`plan/phase-02.md:45-53`). A directory module invoked or registered from Java in a build-file module therefore loses the exact cross-module line D7 added this pack section to expose. Reading a build module to enrich a directory module's pack does not alter the build module's pack or Java link calculation.

**Proposed solution:** Search the source files of every other module when building a directory module's possible references, while still writing the section only into that directory module's pack and never inferring an edge. Add a fixture where a build-file module references a distinctive name or file owned by a directory module and require that line in the latter's pack.

## #3 The generic dead-name check does not validate names in their declaring file

**Severity:** Blocker

The any-code prompt permits a declared name, `Name.member`, or any source file's name in backticks and says they are checked mechanically (`plan/phase-03.md:18-28`). The proposed checker instead accepts `Name.member` when `Name` is declared in one file and `member` appears in any module's reader output (`plan/phase-03.md:30-37`). Thus `Router.add` stays live when `Router` lost `add` but an unrelated type still has it. It also checks a file name only inside the identifier/member regex, so a permitted name such as `install-agent.sh` falls through as unchecked because it contains `-` (`plan/phase-03.md:31-35`).

**Proposed solution:** Keep a project-wide map from each declared name to the source files whose reader output declares it, and require a member in one of those same files. Check exact source file names before applying identifier syntax, including names with hyphens. Add tests where `Router.add` is dead while an unrelated file still declares `add`, and where renaming `install-agent.sh` makes that quoted file name dead.

## #4 The any-code calibration mixes in a Java-variant call

**Severity:** Blocker

Variant selection gives a directory module containing only Java files the `java` variant (`plan/phase-03.md:28`, `plan/phase-03.md:52-58`). Calibration nevertheless combines `deploy`, `scripts`, and `specs` from the sample Java project and divides all three packs by all three calls after subtracting three overheads (`plan/phase-03.md:39-42`). Research says that sample's `specs` directory contains Java files (`plan/research.md:12`, `plan/research.md:80`), so the resulting `CHARS_PER_TOKEN_ANY` is contaminated by a call deliberately governed by the 2.5 Java ratio.

**Proposed solution:** Calibrate only modules whose selected variant is `any code`—for this sample, omit any Java-only directory module—and compute both pack characters and usage rows over exactly that set, subtracting one overhead per included call. Name each calibration module and its selected variant in the review request.

## #5 The Java/Vue status gate cannot print `clean`

**Severity:** Blocker

Phase 3 writes only the five directory-module cards in the Java/Vue clone (`plan/phase-03.md:44-50`) but G3 requires `kb.py status` to read `clean` while its 24 build-file modules have no cards and are said not to count (`plan/phase-03.md:81-84`). Current `cmd_status` counts every missing card as a problem (`protocol/kb/kb.py:596-642`), and no phase decision changes that rule or scopes the command. The gate is therefore impossible as written.

**Proposed solution:** Make `status` honor optional positional module ids, as `estimate`, `write`, and `pack` do; when ids are given, report and count only those modules. Test that an unselected missing card does not prevent scoped status from printing `clean`, document the form, and run G3 as `kb.py status <the five ids>` for Java/Vue. Keep unscoped status unchanged.

## #6 The card gate permits a Boundary that D7 forbids

**Severity:** Blocker

D7 and the any-code prompt say a possible-reference line is never evidence of a dependency or boundary (`plan/plan.md:58`, `plan/phase-03.md:22-26`). G6 nevertheless approves a Boundaries entry when its evidence is "a line that shows the call"—the possible-reference evidence intended for an extension point (`plan/phase-03.md:89`). That gate can approve exactly the false boundary the design rejected.

**Proposed solution:** For an any-code card, accept a Boundaries entry only when a packed build/manifest file or a project skill supports it. Check possible-reference call lines only as evidence for Extension points, never Boundaries. State those two checks separately in G6 and the review request.

Verdict: changes-requested
