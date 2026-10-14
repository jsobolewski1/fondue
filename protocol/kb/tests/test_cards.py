"""The writer's prompt for each kind of module, the dead-name check of a card, status for some modules, the estimate."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fixture import Repo, kb, pom, run
from test_modules import JAVA
from test_reader import KOTLIN

BASE = "1bc80fe"


def at_base(path):
    """A file of this repository at the commit the spec started from, or None where that commit is not here."""
    proc = subprocess.run(["git", "show", f"{BASE}:{path}"], cwd=kb.HERE, capture_output=True, text=True)
    return proc.stdout if proc.returncode == 0 else None


class RepoTest(unittest.TestCase):
    def repo(self, files):
        r = Repo(files)
        self.addCleanup(r.cleanup)
        return r

    def card(self, r, mid, body, sha=None):
        r.write({f"fondue/kb/cards/{mid}.md": f"---\nsummary: x\nverified-at: {sha or r.head()}\n---\n{body}\n"})

    def notes(self, mid):
        """`kb.py status`'s notes for one module."""
        out, _ = run("status")
        line = next(l for l in out.splitlines() if l.split()[:1] == [mid])
        return line[50:].strip()


class Prompt(unittest.TestCase):
    def test_java_variant_is_the_prompt_as_it_was(self):
        base = at_base("protocol/kb/card-writer.md")
        if base is None:
            self.skipTest(f"no commit {BASE} here")
        self.assertEqual(kb.prompt("java"), base)

    def test_any_code_variant(self):
        text = kb.CARD_WRITER.read_text()
        mine = [l[len("[any code] "):] for l in text.splitlines() if l.startswith("[any code] ")]
        java = [l[len("[java] "):] for l in text.splitlines() if l.startswith("[java] ")]
        any_code = kb.prompt("any code").splitlines()
        self.assertEqual(len(mine), 5)
        for line in mine:
            self.assertIn(line, any_code)
        for line in java:
            self.assertNotIn(line, any_code)
        self.assertNotIn("[", "".join(l[:1] for l in any_code))


class Variant(RepoTest):
    def test_each_kind_of_module(self):
        self.repo({"java/pom.xml": pom("plain"), "java/src/main/java/app/A.java": JAVA,
                   "mixed/pom.xml": pom("mixed"), "mixed/src/main/java/app/A.java": JAVA,
                   "mixed/src/main/kotlin/B.kt": KOTLIN,
                   "ops/run.sh": "echo hi\n", "jtools/T.java": "class T {}\n"})
        mods = kb.modules()
        self.assertEqual({mid: kb.variant(m) for mid, m in mods.items()},
                         {"plain": "java", "mixed": "any code", "ops": "any code", "jtools": "java"})


class DeadNames(RepoTest):
    def test_renamed_function_still_called_elsewhere(self):
        r = self.repo({"a/lib.py": "def old_name(x):\n    return x\n",
                       "b/use.py": "def run():\n    return old_name(1)\n"})
        self.card(r, "a", "Offers `old_name`.")
        self.assertEqual(self.notes("a"), "")
        r.commit({"a/lib.py": "def new_name(x):\n    return x\n"})
        self.assertEqual(self.notes("a").split("  ")[-1], "dead: old_name")

    def test_member_must_be_in_the_declaring_file(self):
        r = self.repo({"r/router.ts": "export class Router {\n  add(path) {\n    return 1\n  }\n}\n",
                       "o/other.ts": "export function add(a) {\n  return a\n}\n"})
        self.card(r, "r", "Use `Router.add` and `Router#add()`.")
        self.assertEqual(self.notes("r"), "")
        r.commit({"r/router.ts": "export class Router {\n  remove(path) {\n    return 1\n  }\n}\n"})
        self.assertTrue(self.notes("r").endswith("dead: Router#add(), Router.add"), self.notes("r"))

    def test_file_names(self):
        r = self.repo({"s/install-agent.sh": "echo a\n", "s/run.sh": "echo b\n"})
        self.card(r, "s", "Run `install-agent.sh`.")
        self.assertEqual(self.notes("s"), "")
        (r.dir / "s/install-agent.sh").rename(r.dir / "s/setup-agent.sh")
        r.commit()
        self.assertTrue(self.notes("s").endswith("dead: install-agent.sh"), self.notes("s"))

    def test_a_manifest_must_be_the_modules_own(self):
        r = self.repo({"w1/app.ts": "export const a = 1\n", "w1/package.json": "{}\n",
                       "w2/app2.ts": "export const b = 1\n", "w2/package.json": "{}\n",
                       "index.js": "x\n", "package.json": "{}\n"})
        self.card(r, "w1", "See `package.json` and `./package.json`.")
        self.assertEqual(self.notes("w1"), "")
        (r.dir / "w1/package.json").unlink()
        r.commit()
        self.assertTrue(self.notes("w1").endswith("dead: package.json"), self.notes("w1"))
        (r.dir / "package.json").unlink()
        r.commit()
        self.assertTrue(self.notes("w1").endswith("dead: ./package.json, package.json"), self.notes("w1"))

    def test_skills_and_module_ids_are_skipped(self):
        r = self.repo({"w1/app.ts": "export const a = 1\n", "w2/app2.ts": "export const b = 1\n",
                       ".claude/skills/ops/SKILL.md": "---\ndescription: ops\n---\nx\n"})
        self.card(r, "w1", "Read `ops`; see `w2`; not `nowhere`.")
        self.assertTrue(self.notes("w1").endswith("dead: nowhere"), self.notes("w1"))

    def test_java_card_is_checked_as_before(self):
        old = at_base("protocol/kb/kb.py")
        if old is None:
            self.skipTest(f"no commit {BASE} here")
        r = self.repo({"pom.xml": pom("app"), "src/main/java/app/A.java": JAVA})
        self.card(r, "app", "`A`, `A.go`, `A.nope`, `Missing`, `src/main/java/app/A.java`, `src/gone/X.java`, `lower`.")
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "kb.py").write_text(old)
            before = subprocess.run([sys.executable, str(Path(d) / "kb.py"), "status", "--root", str(r.dir)],
                                    capture_output=True, text=True, check=True).stdout
        out, _ = run("status")
        self.assertEqual(out, before)
        self.assertIn("dead: A.nope, Missing, src/gone/X.java", out)


class StatusForSomeModules(RepoTest):
    def test_ids(self):
        r = self.repo({"a/x.py": "x = 1\n", "b/y.py": "y = 1\n"})
        self.card(r, "a", "Nothing named.")
        out, code = run("status", "a")
        self.assertEqual(out.splitlines()[-1], "clean")
        self.assertNotIn("\nb ", out)
        out, _ = run("status")
        self.assertIn("no card", next(l for l in out.splitlines() if l.startswith("b ")))
        self.assertEqual(out.splitlines()[-1], "1 modules need attention")
        _, code = run("status", "nope")
        self.assertEqual(code, "unknown modules: nope")


class Estimate(RepoTest):
    def test_chars_per_token_by_variant(self):
        self.repo({"pom.xml": pom("app"), "src/main/java/app/A.java": JAVA, "ops/run.sh": "echo hi\n"})
        with mock.patch.object(kb, "pack", lambda m, mods, skills: "x" * 100_000), \
                mock.patch.object(kb, "CHARS_PER_TOKEN_ANY", 4.0):
            java, _ = run("estimate", "app")
            any_code, _ = run("estimate", "ops")
        self.assertTrue(java.startswith("1 cards: about 42k input"), java)
        self.assertTrue(any_code.startswith("1 cards: about 27k input"), any_code)


if __name__ == "__main__":
    unittest.main()
