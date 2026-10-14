# Reviewer research - kb-universal, pre-plan

## Research

FACT: `modules()` discovers only tracked `src/main` trees beneath Maven or Gradle build files, and Maven parsing, Java import scanning, and Java construction scanning are coupled into the same discovery pipeline (`protocol/kb/kb.py:32`, `protocol/kb/kb.py:77-125`, `protocol/kb/kb.py:369-388`). Universality therefore needs a language-neutral module path alongside the existing build-module path; adding only more declaration readers would still leave non-Java repositories undiscoverable.

FACT: `Module` already separates a card's path, change root, build root, sources, parent, and excluded directories, while `module_of`, `changed_modules`, and `cmd_status` consume those fields (`protocol/kb/kb.py:65-74`, `protocol/kb/kb.py:128-161`, `protocol/kb/kb.py:519-529`, `protocol/kb/kb.py:596-642`). I would reshape this model rather than introduce a second module/card abstraction.

FACT: declaration extraction already dispatches by source suffix and leaves unsupported sources out; downstream name validation independently assumes Java/proto capitalized type declarations (`protocol/kb/kb.py:170`, `protocol/kb/kb.py:274-296`, `protocol/kb/kb.py:596-635`). A generic reader must carry both its reduced text and the names it recognizes into validation, or non-Java cards can be written but cannot be checked coherently.

FACT: the current pack format has language-neutral sections for README, project skills, cards, and module headers, but module edges and construction sites are populated by Maven and Java syntax (`protocol/kb/kb.py:324-419`). These should remain richer evidence for build-file Java modules without becoming prerequisites for a card.

FACT: the repository has no test files (`git ls-files | grep -i test` is recorded as R12 in `pre-plan/01-research.md`). This change needs a new automated regression harness rather than relying only on the sample runs.

RESULT: the Architect's directory-layout prototype produces useful modules on every sample but also produces a 56-character TypeScript module and admits false-positive cross-module edges (`pre-plan/01-research.md` R5-R6). Raw recursive splitting and symbol-overlap edges are therefore not safe as card boundaries or dependency claims without a minimum/coalescing rule and a way to omit uncertain edges.

RESULT: only one of the non-Java sample languages has an installed language server, and the marketplace has no shell or Vue server (`pre-plan/01-research.md` R2). An LSP requirement would make the stated sample set less universal, not more. LSPs may be future optional enrichers but cannot be the base mechanism of this spec.

RESULT: the generic skeleton prototype retains complete multi-line C signatures and reduces all sampled languages, while its remaining unbalanced cases have concrete lexical causes (`pre-plan/01-research.md` R3-R4). A repaired lexical reducer is viable as the universal baseline; the existing Java/proto readers should remain selected where available.

RESULT: current Java packs are reproducible byte-for-byte on a clean clone and `kb.py status` is clean (`pre-plan/01-research.md` R7). That gives the Java-compatibility gate a stronger oracle than comparing generated prose: compare packs and module identities, then run status.

## Intended approach

I would preserve the current Java/Maven/Gradle path as a compatibility-preserving specialization and add a language-neutral fallback for tracked, project-owned text source that no build module claims. The fallback would form directory modules from repository/build-root layout, recursively split only when a size budget requires it, coalesce or retain tiny leaves rather than emit meaningless cards, and let `parts.txt` express manual splits and exclusions when layout cannot convey intent.

Every module would use a reader selected per file. Java and proto keep their existing readers. Other source text goes through one dependency-free lexical reducer that preserves top-level/container declarations and balanced multi-line signatures while dropping bodies. Build and manifest files are bounded pack evidence, not mandatory module detectors. Unknown or weakly inferred relationships are omitted; a name-overlap heuristic must not be presented as a dependency edge. This makes a sparse but truthful card preferable to a confidently false boundary.

The writer contract and status check would be generalized together: the pack tells the writer which names and paths may be backticked, including lowercase names, and status validates those names against the owning module's extracted declarations. Estimates use reader-appropriate measured ratios. No LSP, ctags, tree-sitter, or non-stdlib Python dependency belongs in the baseline.

The delivery should be phased so the first phase establishes module discovery, explicit overrides, and tests; the second introduces the generic reader, writer/status contract, and cost accounting; the last integrates documentation and end-to-end gates. Done means `modules`, `pack`, `estimate`, `write`, `status`, and incremental `--since` work on fondue, the C project, the shell project, the mixed Java/Vue project, the existing Java sample, and a pinned public TypeScript fixture; existing Java module identities and packs remain byte-identical. Card-quality gates should check meaningful module boundaries, retained declarations/signatures, bounded packs, truthful validation, and clean status rather than merely successful card generation.
