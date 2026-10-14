- #1 accepted, fixed in 47fedb4 as proposed

**Build:** python3 -m unittest discover -s protocol/kb/tests - green, 41 tests passed

**Gates:** at 47fedb4, same `$S` as the request, `$S/fondue` re-cloned at 47fedb4. G1: `0 []` on c, shell, fondue, java-vue, java and hono. G2: c 5.43, java-vue 3.53, hono 2.15, fondue 7.02 (64,110 / 9,130; the clone now holds this commit's kb.py), shell 1.88. G3: the same lines as the request's on shell, c, java-vue and hono (packs rebuilt). G4: `IDENTICAL`.

Verdict: closed git diff 370d6ff..47fedb4
