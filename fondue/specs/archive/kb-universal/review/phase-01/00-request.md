- **Subject:** git diff 461dd00..7c7d29f
- **Build:** python3 -m unittest discover -s protocol/kb/tests - green, 25 tests passed
- **Gates:** `$S` = <scratch>/gate, clones as the phase file's Gate says (fondue cloned at 7c7d29f, hono at 588ec13f). Run from the repository root.
  - **G1** `python3 protocol/kb/kb.py modules --root $S/<label>`, every list as the phase file's table states:
    - c (12): `root` . 14k; `<protocol>` 95k; `core` 410k; `data` 196k; `examples-bootstrap_server` 54k; `examples-client` 195k; `examples-lightclient` 52k; `examples-server` 40k; `examples-shared` 27k; `include` 39k; `tools` 14k; `transport` 32k
    - shell (2): `root` . 6k; `provision` 17k
    - fondue (2): `integrations` 3k; `protocol` 47k
    - java-vue (29): the 24 build-file modules of `kb.py` at 1bc80fe, ids and paths unchanged (`diff` of id/path columns against 1bc80fe's output shows only additions), plus `<p>-demo-bsserver-webapp` 67k, `<p>-demo-server-webapp` 188k, `<p>-demo-servers-shared-webapp` 40k, `<p>-integration-tests` 9k, `<p>-core-certificates` (`<p>-core/certificates`) 7k
    - java (41): the 38 of 1bc80fe, unchanged by the same `diff`, plus `deploy` 35k, `scripts` 74k, `specs` 54k
    - hono (14): `root` . 13k; `adapters` 59k; `benchmarks` 52k; `perf-measures` 3k; `runtime-tests` 0k; `src` 154k, whose pack reads `holds: the files directly in src, and src/preset/, and src/request/`; `src-adapter` 70k; `src-client` 26k; `src-helper` 87k; `src-jsx` 165k; `src-middleware` 146k; `src-router` 35k; `src-utils` 99k; `src-validator` 8k
    - Floor: the directories split by size are c's `examples` and hono's `src`; their non-residual children are 27k-195k and 8k-165k, none under 5k.
  - **G2** the phase file's script - `IDENTICAL` (38 packs; the clone carries the sample's committed cards and `parts.txt`, so the packs include current cards and five parts). `kb.py status --root $S/java`, diffed against 1bc80fe's: the 38 build-file lines are identical; the only differences are `deploy`, `scripts` and `specs` with `no card`, and the last line, `3 modules need attention` for `clean`.

Beyond the phase file, for the reviewer:
- `module_header` takes its project artifacts from build-kind modules only. Otherwise a directory module whose id equals an external Maven artifactId would turn that dependency into a project one in a Java pack. In `DirectoryModules.test_source_beside_src_main` the pom depends on `src`, and the test fails without the restriction.
- A residual's own files leave out names in `BUILD_FILES`, as its ownership and `pathspecs` do (decision 4); only `build.gradle.kts` is on the code list, so this is the one file it affects.
- `split_parts` takes as a part's parent the owner of the first tracked file inside the part's directory that has an owner (decision 6).
- `status`'s changed column for a build-file module still counts only `src/main`, as today, so a `pom.xml` change counts in `changed_modules` but not in `status` (`test_residual_beside_a_build_module_at_the_root` pins both).
- Per decision 6 the root residual's skill-mention names are `{root}`, so a skill line with the word "root" mentions it; the empty name the old code would add is gone, which the test checks.
