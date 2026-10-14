- **Subject:** git diff 03685c8..65fdbce
- **Build:** python3 -m unittest discover -s protocol/kb/tests - green, 53 tests passed
- **Gates:** `$S` = <scratch>/gate, the clones of phase 1's Gate; `$S/fondue` cloned at f31b2c4, the commit the writes ran on. Run from the repository root. Java + Vue ids are written `<p>-...` as before.
  - **G1** `cmp` of `git show 1bc80fe:protocol/kb/card-writer.md` and `prompt("java")` at 65fdbce: identical (and `Prompt.test_java_variant_is_the_prompt_as_it_was`). The mixed fixture gets `any code` (`Variant.test_each_kind_of_module`). The Java gate: `IDENTICAL`.
  - **Calibration** (decision 3), on `$S/java` at 167cdfe: `deploy`, `scripts` and `specs`, each `any code`. `kb.py pack` gave 29,953 + 39,205 + 35,399 = 104,557 chars; `kb.py write deploy scripts specs` at 23:47:50, 3 calls, input `in + write + read` 16,528 + 15,979 + 17,385 = 49,892, $0.23. 104,557 / (49,892 - 3 × 1,800) = 2.35, so `CHARS_PER_TOKEN_ANY = 2.4` (f31b2c4).
  - **G2 / G4 / G5** the gated writes at f31b2c4, `--model sonnet`, each `estimate` printed just before its write:

    | sample | estimate printed (exact) | cards | usage in+write+read | out | cost | time | estimate vs usage | largest card |
    |---|---|---|---|---|---|---|---|---|
    | c | 128k (128,457) | 12 | 142,655 | 12,593 | $0.64 | 26 s | -10.0% | $0.142 `core` |
    | shell | 13k (12,986) | 2 | 14,343 | 1,439 | $0.06 | 7 s | -9.5% | $0.033 `provision` |
    | fondue | 8k (7,913) | 2 | 7,931 | 1,137 | $0.03 | 7 s | -0.2% | $0.025 `protocol` |
    | hono | 230k (229,684) | 14 | 251,177 | 13,727 | $1.08 | 28 s | -8.6% | **$0.248 `src`** |
    | java-vue, its 5 directory modules | 57k (57,290) | 5 | 59,723 | 4,724 | $0.26 | 15 s | -4.1% | $0.123 `<p>-demo-server-webapp` |

    G4 holds on every sample. G5 fails for hono's `src` only ($0.248); the ruling of 2026-10-15 (question.md#1, "accept") accepts it, and the design notes record it with its cause.
  - **G3** `kb.py status --root $S/<label>` at 053da1d reads `clean` on c, shell, fondue and hono, and `kb.py status <its five ids> --root $S/java-vue` reads `clean`. Dead names fixed by hand: c 89 (15 corrected to a repo path, 74 backticks dropped), shell 0, fondue 0, hono 41 (17 corrected, 24 dropped), java-vue 14 (1 corrected, 13 dropped). Before the ruling on question.md#2 there were 94 more, paths relative to the module's directory, which 053da1d accepts. The fixes followed kb-init step 5 mechanically: a dead path or file name that exactly one tracked file or directory ends with was replaced by that repo path (`./<name>` at the root); every other dead name lost its backticks. Script: <scratch>/handfix.py.
  - **G6** cards to check, in `$S/<label>/fondue/kb/cards/`: c `core.md`, `include.md`; shell `provision.md`, `root.md`; fondue `protocol.md`, `integrations.md`; hono `src-router.md`, `src-middleware.md`; java-vue `<p>-demo-servers-shared-webapp.md`, `<p>-demo-server-webapp.md`. Each module's pack: `python3 protocol/kb/kb.py pack <id> --root $S/<label>` (it now includes the card as `## Current card`). From a first look, for the reviewer to judge: `provision.md`'s third Boundaries entry ("Invoked from `./Makefile` ... and `./Vagrantfile`") and `src-router.md`'s second ("Imports the `Router` contract ... from `src/router.ts`") rest on possible references and on import lines in the declarations, not on a manifest.

Beyond the phase file, for the reviewer:
- Ruling question.md#2 (option 2): `own_path` accepts a path relative to the module's directory when it stays inside the module and exists; the `[any code]` backticks line of `card-writer.md` says a file of the module is named by its path as the input's headings give it, or by its repo path. Test `DeadNames.test_paths_relative_to_the_module`.
- A dir-kind module whose sources are only `.java` gets `java` and today's check, with its own types added to the build-kind modules' types; without them every type it declares would be dead.
- In an `any code` card, a backtick holding `/` is checked only when it has the shape of today's path check (`[\w.-]+/[\w./-]+`); other contents with a `/` are not checked, as today.
- `test_cards.py`'s Java-only check runs `kb.py` at 1bc80fe on the same fixture and compares the whole `status` output.
- The `[any code]` variant is the whole prompt for any code, five marked lines, as decision 1 lists them; `prompt()` drops each line marked for the other variant.
- `skills/kb-init/SKILL.md`'s `status:` metadata now says six projects.
