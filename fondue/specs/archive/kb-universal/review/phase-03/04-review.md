## #1 G6, Boundaries after the rewrite: 4 of the 7 cards that keep the section hold only a "no dependencies" entry that nothing in the pack supports (re 01-review.md#2)

**Severity:** Blocker

The new prompt line (card-writer.md:43) says: "Boundaries only from those files or a skill's line. The header's "-" means no dependency was computed, not that there is none; ... Omit the section if there are none." The rewrite fixed what it was aimed at. None of the ten cards now states a dependency from imports, compile flags or possible references, and `include.md`, `provision.md` and `src-middleware.md` leave the section out. These cards, in `$S/<label>/fondue/kb/cards/`, still have a Boundaries section whose only entry says the module has no dependencies, and no build or manifest file and no skill line in the pack supports it:

- c `core.md`: "No project dependencies were computed for this module." This restates the header's `-` as an entry. `core` uses `<protocol>/` and `data/` code.
- fondue `protocol.md`: "No project or external dependencies computed; scripts use only the Python standard library." The header's `-`, plus imports, which the line says are not boundaries.
- fondue `integrations.md`: "No project or external dependencies are declared for this module." The pack has no `## Wiring`, so nothing in it declares anything.
- hono `src-router.md`: "No dependencies are declared for this module in its manifest." The pack has no `## Wiring` and the module has no manifest. It does import `src/router.ts` and `src/utils/url.ts`.

A later reader takes "no dependencies declared" as "this module stands alone". That is the misreading 01-review.md#2 named. The three entries that remain are supported: shell `root.md` by its `Makefile`'s `prereqs` target, and the two web parts by `package.json` and `vite.config.js`.

The decision is the User's. The wording of these `[any code]` lines is what the ruling of 2026-10-15 on 01-review.md#2 approved, so changing it again is a change to an approved artifact. Accepting the cards as they are leaves G6 short of the ruling of 2026-10-14.

**Proposed solution:** ask the User to choose:
1. In card-writer.md:43, replace "Omit the section if there are none." with "Omit the section if there are none: never write an entry that says the module has no dependencies, or that none were computed or declared." Then write the cards again, either every gated card (about $2.1, so that G2, G4 and G5 describe the prompt as it ships) or only the four above (about $0.3, with G2, G4 and G5 left as measured), and check the same ten cards.
2. Keep the cards. design-notes' Known limits says that a directory module's card may have a Boundaries entry that only says no dependencies were computed or declared, and that this means nothing.

## #2 G6, "Already here" after the rewrite: two entries point to the wrong place

**Severity:** Nit

- c `include.md`: "Session/peer comparison and removal -> `lib_session_is_equal`, `lib_session_remove`". Both are in the header's block of "Platform abstraction functions to be implemented by the user" (`include/<lib>.h:107`, declared at `:158` and `:163`). The library does not provide them. The UDP and secure transports implement them (`transport/udp/connection.c:211`, `:217`; `transport/<tls>/connection.c:566`). The same card's Extension points lists `lib_session_is_equal` as something a port must implement.
- shell `root.md`: "Private image registry at `registry.k3s-dev.local:8080` with basic auth, reachable from pods via the default service account - `registry-host`". `registry-host` (`Makefile:49-50`) only configures the host's hosts entry and Docker. The registry, its basic auth and the service-account patch come from `provision/install-docker-registry.sh` (`:280-283`), which the `Vagrantfile` provisioner runs.

The other entries of the ten rewritten cards, and every extension point among them, match the code. The first write's incomplete payload-format extension point is gone, because `core.md` now has no Extension points section.

**Proposed solution:** design-notes' "Checked against the code" bullet describes only the first write. Add the second write's result next to it: no extension point wrong, and two "Already here" entries that point to a platform hook or to the host-side target instead of the code that provides the thing.

Verdict: changes-requested
