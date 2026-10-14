# Universal knowledge base
Mode: full

## Goal
The knowledge base refuses to build for non-Java projects. Most of what I do is Java-based, but fondue is meant to be universal: building a knowledge base for a TypeScript project, a shell project, any project, should be possible.

## Context
Facts about the code as it is at `fd012e7`. Paths are in this repository.

**Where `kb.py` is Java-specific** (`protocol/kb/kb.py`):
* **Module discovery.** `modules()` treats a directory as a module only if it has a build file (`BUILD_FILES` = `pom.xml`, `build.gradle`, `build.gradle.kts`) and tracked files under `src/main`. RESULT, run in this repository: `python3 protocol/kb/kb.py modules` prints `No modules found: kb.py reads Maven and Gradle projects with sources under <module>/src/main` and exits 1. Step 1 of `skills/kb-init/SKILL.md` then stops the run.
* **Dependencies.** Read from `pom.xml` only (`pom_info`). Gradle modules are found, but without their dependencies.
* **Declarations.** `declarations()` reads `.java` (`java_skeleton`, a hand-written parser that drops method bodies and keeps a Javadoc's first sentence) and `.proto`. `.kt`, `.scala` and `.groovy` files are listed by name only. Any other file is left out of the pack without a word.
* **Links between modules.** "Depended on by" for a split module (`narrow_split`) and "constructed in other modules" (`wired_from`) use Java `package`/`import` lines and `new <Type>`.
* **Dead-name check.** `kb.py status` collects declared names with `TYPE_DECL` (`class|interface|enum|record|message|service`) from `.java` and `.proto` files only. It checks only backtick names that start with a capital letter, so a lowercase name (a function, a shell command) is never checked.
* **Wiring files.** `WIRING_GLOBS` covers `META-INF/services/*` and Spring's `application*.yml|yaml|properties`, under `src/main/resources`.
* **The card writer's prompt** (`protocol/kb/card-writer.md`) says a backtick name must be "a class, interface, record, enum or proto message header".
* **Cost model.** `CHARS_PER_TOKEN = 2.5` was measured on Java skeletons.
* `skills/kb-init/design-notes.md` (Known limits) already names languages and module discovery as limits.

**What the Java skeleton saves.** RESULT, measured on a sample Java project (Maven, 38 modules), summing over every `.java` source of every module: raw source 1,692,462 chars; `java_skeleton` output 355,724 chars, 4.8× smaller. A 40-line prototype that knows no language (it keeps lines up to one indent level inside a class/struct/enum-like container and replaces deeper lines with `…`) gave 461,791 chars, 3.7× smaller. It was a feasibility check, not a design. Its known gap: a signature split over several lines lost its parameters (seen on a sample C project). The sample Java project's largest module is 224,310 chars of raw Java.

**What the tooling depends on.** `kb.py` imports only the Python standard library, and runs `git` and `claude`. On the machine this was checked on, the only `ctags` installed is BSD ctags, not universal-ctags, and the Python module `tree_sitter` is not installed.

**Language servers.** Claude Code's official plugin marketplace has 12 LSP plugins: clangd, csharp, gopls, jdtls, kotlin, lua, php, pyright, ruby, rust-analyzer, swift, typescript. A plugin is configuration only: its `lspServers` entry in the marketplace's `marketplace.json` names the server command and the file extensions it serves, and the server itself is installed separately (e.g. `npm install -g typescript-language-server typescript`, from the typescript-lsp README). On the machine this was checked on, `jdtls-lsp` is installed and enabled, and `clangd`, `jdtls` and `sourcekit-lsp` are on the `PATH`. RESULT: a 40-line script using only the Python standard library spoke JSON-RPC over stdio to `clangd`, sent `initialize`, `didOpen` and `textDocument/documentSymbol` for one file of the sample C project, and got its 10 top-level functions with their signatures in 1.2 s. With no `compile_commands.json`, clangd could not resolve the project's own types and printed them as `int *`. `kb.py` runs as a script, outside any Claude session, and its card-writer calls (`claude -p`) have no tools.

**Sample projects at hand to try it on**, by tracked file extension:
* fondue itself: markdown and Python, no build file.
* a C project: C and headers, CMake.
* a shell project: shell scripts.
* a Java project with a Vue/JavaScript web part.
* the sample Java project (Maven) the current tool was measured on.
No TypeScript project is at hand.

Their local paths are in `pre-plan/samples.local.md`, which is never committed. Every committed file (research, drafts, phase files, reviews, code, docs) names a sample project only as this list does, never by its name or path.

## Open questions
* Which non-Java projects does the spec have to work on to count as done, and how good must their cards be?
* How a project with no build file that names its modules (fondue itself, a folder of shell scripts) gets its modules.
* Whether the tooling may depend on anything beyond the Python standard library, `git` and `claude`.
* What a card for a language with no dedicated reader may cost, compared with a Java card.
* Whether Java cards (cost, content) may change at all.
* If there are LSP plugins available, perhaps they should be used to detect modules, read declarations, or find links between modules?
