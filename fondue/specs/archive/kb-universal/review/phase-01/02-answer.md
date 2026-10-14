- #1 accepted, fixed in de5f7f9 as proposed; test `DirectoryModules.test_build_file_in_a_group_counts_against_it`
- #2 accepted, fixed in de5f7f9 as proposed; tests `DirectoryModules.test_part_over_more_than_one_module` and `test_part_wider_than_its_module`
- #3 accepted, fixed in de5f7f9 as proposed; assertion added to `test_part_inside_a_folded_child`
- #4 accepted, fixed in de5f7f9 as proposed (protocol/kb.md, the pattern paragraph)
- #5 declined (Nit)

**Build:** python3 -m unittest discover -s protocol/kb/tests - green, 28 tests passed

**Gates:** at de5f7f9, same `$S` as the request (fondue re-cloned at de5f7f9). G1: all six `kb.py modules` outputs byte-identical to those reported in the request. G2: `IDENTICAL`; `kb.py status --root $S/java` byte-identical to the request's (38 build-file lines as at 1bc80fe, plus `deploy`, `scripts`, `specs` with `no card`).

Verdict: closed git diff 461dd00..de5f7f9
