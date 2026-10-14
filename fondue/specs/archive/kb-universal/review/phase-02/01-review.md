## #1 `generic_source` rebuilds the source rule's include, exclude and code-list tests instead of sharing them with `is_source`

**Severity:** Blocker

The phase file's decision 2 defines a build-file module's generic files as those "the source rule's steps 3, 4 and 7 make a source". `generic_source` (kb.py:661-667) writes those three steps out again: the `-` test (kb.py:664 = kb.py:177), the `+` test (kb.py:666 = kb.py:179), and the code-list and name-list test (kb.py:667 = kb.py:185). Nothing ties the copies together. A later change to what counts as code would have to be made in both places, e.g. a shebang check, which D4's "shebang-less" fixture already points at. A change made only in `is_source` would make a build-file module's `src/main` and a directory module disagree about the same kind of file. That is code that rebuilds what the code already has, which the phase file does not ask for.

**Proposed solution:** extract the two shared tests next to `is_source` and use them in both functions:
```python
def ruled(f, rules, sign):
    return any(matches(pat, f) for s, pat in rules if s == sign)


def code_file(f):
    return f.suffix.lower() in CODE_EXT or f.name in CODE_NAMES or f.name.startswith("Dockerfile.")
```
In `is_source`, kb.py:177-180 become `if ruled(f, rules, "-"): return False` and `if ruled(f, rules, "+"): return True`, and kb.py:185 becomes `return code_file(f)`. `generic_source`'s body becomes `return not ruled(f, RULES, "-") and (ruled(f, RULES, "+") or code_file(f))`. Behaviour is unchanged, so no test changes.

Verdict: approved-with-fixes git diff 9a4d789..379f0bc | #1
