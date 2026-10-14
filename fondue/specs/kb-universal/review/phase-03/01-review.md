## #1 The check reads `./<path>` as relative to the module, so a card can name a root file that does not exist and still read `clean`

**Severity:** Blocker

The phase file's decision 2, rule 1, reads a backtick that holds a `/` with "the path check, as today, which reads `./<name>` as the file `<name>` at the root". The `[any code]` prompt line written in this commit (card-writer.md:38) tells the writer the same thing: "`./<name>` for a file at the root". `own_path` (kb.py:1165, called from `dead_any_code`) normalises `m.path / name`, so `./x` also counts as live when `<module>/x` exists. `test_paths_relative_to_the_module` asserts that `./app/src/views` is live for the module `web`, where no root `app/` exists. Ruling question.md#2 accepts paths like `src/main.js`, which is how the pack's headings name a module's files. No heading starts with `./`, so the ruling does not cover that form.

The gated cards do this. RESULT: none of the following files exists at the clone's root, yet `status` reads clean:
```
$ git -C $S/fondue ls-files turn-stats.py stats-total.py | wc -l
       0
fondue/fondue/kb/cards/protocol.md:`./turn-stats.py`, `./stats-total.py`
hono/fondue/kb/cards/src-middleware.md:`./jwt/index.ts`, `./request-id/index.ts`, `./timing/index.ts`, `./language/language.ts`
$ kb.py status protocol --root $S/fondue        -> clean
$ kb.py status src-middleware --root $S/hono    -> clean
```
Across the five samples' cards, 10 `./` names name no root file: fondue 2, hono 8. A reader who takes the card's own convention at its word looks for them at the repository root.

**Proposed solution:** in `own_path`, return `False` when `name` starts with `./`. In `test_paths_relative_to_the_module`, expect `dead: ../../top.sh, ../lib/x.js, ./app/src/views, app/src/gone.js`. Then run G3 again on fondue and hono, fix the new dead names by hand as before (`./turn-stats.py` becomes `protocol/turn-stats.py`), and report the new counts.

## #2 G6, Boundaries: 9 of the 10 cards have an entry that no build or manifest file and no skill line supports, and 4 state a boundary from possible references

**Severity:** Blocker

The phase file's G6 checks each Boundaries entry against the module's pack. An entry must rest on a build or manifest file or on a project skill's line, never on a possible-reference line. That is plan.md's Phase 3 gate as amended by the ruling of 2026-10-14. The `[any code]` prompt also says "Never state a dependency or a boundary from it" (card-writer.md:42). These entries, under `$S/<label>/fondue/kb/cards/` (the web part's ids written `<p>-...`), do not hold:

- c `core.md`: "No project or external dependencies are declared for this module in the manifests shown." The pack has no `## Wiring`, so this rests only on the header's `-` lines, and those mean "not computed" for a directory module (phase-02.md decision 4). `core` does use `<protocol>/` and `data/` code. "Behaviour is compiled in or out by LIB_CLIENT_MODE, ..." rests on `#ifdef` lines in its declarations.
- c `include.md`: "No project or external dependencies in the manifest." There is no manifest. "Behavior depends on compile-time macros ... cannot both be defined" rests on its declarations (`include/<lib>.h:103`, an `#error`).
- shell `provision.md`: entry 1 (no dependencies, environment variables) rests on its scripts and on no manifest. Entries 2 ("run as VM provisioners ... run on the host") and 3 ("Invoked from `./Makefile` ... and `./Vagrantfile`") rest on the possible references `Makefile:36`, `Makefile:50`, `Vagrantfile:69` and `Vagrantfile:80`.
- fondue `protocol.md`: entry 1 rests on no manifest. Entry 2 ("`integrations/agents/codex-turn-stats.py` is a separate Codex counterpart whose columns are not comparable") rests on the possible reference `integrations/agents/codex-turn-stats.py:20`.
- fondue `integrations.md`: entry 1 rests on its imports (glob, json, os, sys). Entry 2 rests on its own docstring and is not a dependency.
- hono `src-router.md`: entry 1 rests on no manifest. Entry 2 ("Imports the `Router` contract ... from `src/router.ts`") rests on its import lines.
- hono `src-middleware.md`: its one entry rests on no manifest and on its import lines.
- java-vue `<p>-demo-servers-shared-webapp.md`: entry 2 (libraries "through imports, though none of these are listed in the manifest") rests on imports. Entry 3 ("Consumed by `<p>-demo-server/webapp/src/App.vue` and `<p>-demo-bsserver/webapp/src/App.vue`") rests on possible references.

Supported: shell `root.md`, by its own `Makefile` and `Vagrantfile`; java-vue `<p>-demo-server-webapp.md`, by `package.json` under `## Wiring` and its `vite.config.js`; and the shared web part's first entry, by its `package.json`.

The cause is in the prompt. The `[any code]` Boundaries line (card-writer.md:30) asks for "what it depends on, from its build and manifest files in the input". Unlike Extension points and Already here, it never says to leave the section out. Most directory modules have no manifest, so the writer fills the section from the header's `-`, from imports, compile flags and docstrings, and four times from the possible references.

The decision is the User's. Fixing it changes the `[any code]` lines whose text phase-03.md decision 1 fixes, which is an approved artifact. Accepting the cards as they are changes G6 as the ruling of 2026-10-14 amended it.

**Proposed solution:** ask the User to amend decision 1's `[any code]` lines as follows:
- line 30 becomes `[any code] - <what it depends on, from its build and manifest files: those under "## Wiring", or its own build file among the declarations (a Makefile, CMakeLists.txt, vite.config.js); a rule the skills state about what it must not depend on>`;
- after the possible-references rule, add `[any code] - Boundaries only from those files or a skill's line. The header's "-" means no dependency was computed, not that there is none; imports, compile flags, environment variables and "Possible references in other modules" are not boundaries. Omit the section if there are none.`

Then write the gated cards again (about $2.1 on Sonnet, as G2 measured), run G3 again, and name the same ten cards for G6. The other option for the User: accept the cards, and have design-notes' Known limits say that a directory module's Boundaries are not reliable.

## #3 G6, extension points and "Already here": two entries point to the wrong place

**Severity:** Nit

- c `core.md`, "To add a payload format: declare its parse/serialize pair in `internals.h` ... behind a `LIB_SUPPORT_*` flag". A format is picked up by the content-type switches in `data/data.c` (`tlv_parse`, `json_parse`, `senml_json_parse`, `senml_cbor_parse` at `data/data.c:693-720`, and the serialize cases at `:779-830`), which the entry leaves out. Following it, a new format is never called. The pack does not show `data.c`, so the prompt's "If you cannot see how a new one is picked up, leave it out" applied. In "To add a request type", the switch is in `handle_request` (`core/packet.c:140-210`), which `lib_handle_packet` calls, not in `lib_handle_packet` itself.
- hono `src-middleware.md`, "Constant-time credential comparison ... -> `basicAuth`, `bearerAuth`". The helper is `timingSafeEqual` in `src/utils/buffer.ts`, which both import (`src/middleware/basic-auth/index.ts:10`). `COMPRESSIBLE_CONTENT_TYPE_REGEX` is declared in `src/utils/compress.ts`, not in this module.

The other eight cards' extension points and "Already here" entries match the code.

**Proposed solution:** in design-notes' "Measured on code of any language", record that of the ten cards checked against the code, one extension point was incomplete and one "Already here" entry named a caller instead of the helper, and that kb-init's check of two or three cards is what catches them.

Verdict: changes-requested
