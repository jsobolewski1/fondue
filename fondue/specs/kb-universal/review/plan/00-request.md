- **Subject:** fondue/specs/kb-universal/plan/phase-01.md, fondue/specs/kb-universal/plan/phase-02.md, fondue/specs/kb-universal/plan/phase-03.md

`plan/plan.md` is `cp` of `pre-plan/05-draft.md`. The research is `plan/research.md` (R1-R10); its prototypes are in `plan/results/` (`discover.py`, `reader.py`, `refs.py`), research only, each stating its rule in its docstring. The sample paths are in `pre-plan/samples.local.md`.

Three places where a phase file fills in a gate plan.md states loosely:
* phase-02.md G1 counts brackets on code parts (strings and comments removed), where `pre-plan/results/brackets.py` counted whole lines. The reader keeps a comment's first line, and its prose can open a bracket it never closes; a declaration that lost its end shows either way.
* phase-03.md measures characters per token on the sample Java project's three directory modules before the gated writes, so that no gated sample's estimate is checked against a figure taken from its own write. That adds 3 cards to plan.md's "about 37"; the phase states about 40 cards, about $3.
* phase-03.md G3 counts `kb.py status` as clean on the Java + Vue project's clone when its five directory modules show no note: the gate writes only those, so its 24 build-file modules show `no card` there.
